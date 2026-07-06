"""Tests for watchlist snapshot history and success reporting."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.intraday_watchlist import IntradayWatchlistPick
from analyzer.watchlist_eod import score_session_plan
from analyzer.watchlist_history import (
    MIN_RETENTION_DAYS,
    build_recent_suggested_picks,
    build_watchlist_success_report,
    fetch_snapshots_for_date,
    save_watchlist_snapshot,
    score_daily_watchlist,
    session_target_date,
)


def _fake_pick(symbol: str, rank: int = 1) -> IntradayWatchlistPick:
    from analyzer.intraday_watchlist import PivotLevels, ProChecklist

    checklist = ProChecklist(
        volume_ok=True,
        atr_ok=True,
        rsi_macd_ok=True,
        levels_ok=True,
        news_ok=True,
        passed=5,
        notes=[],
    )
    return IntradayWatchlistPick(
        rank=rank,
        nse_symbol=symbol,
        name=symbol,
        sector="IT",
        price=1000.0,
        atr_pct=2.0,
        volume_ratio=1.5,
        rsi=55.0,
        macd_bullish=True,
        entry=1010.0,
        stop_loss=995.0,
        target=1040.0,
        prep_score=80.0,
        market_bias="BULLISH",
        checklist=checklist,
        pivot=PivotLevels(pivot=1000, r1=1010, r2=1020, s1=990, s2=980),
        support=990.0,
        resistance=1020.0,
        sector_tailwind=True,
        breakout_note="test",
        news_note="",
        can_enter=True,
        plan_summary="Long above entry",
    )


class TestWatchlistHistory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "journal.db"
        self.jp = patch("analyzer.suggestion_journal.journal_db_path", return_value=self.db)
        self.je = patch("analyzer.watchlist_eod.journal_db_path", return_value=self.db)
        self.jh = patch("analyzer.watchlist_history.journal_db_path", return_value=self.db)
        self.jp.start()
        self.je.start()
        self.jh.start()

    def tearDown(self):
        self.jh.stop()
        self.je.stop()
        self.jp.stop()
        self.tmp.cleanup()

    def test_save_snapshot_and_fetch(self):
        picks = [_fake_pick("RELIANCE"), _fake_pick("TCS", 2)]
        n = save_watchlist_snapshot(picks, market_bias="BULLISH", prep_date="2026-07-01")
        self.assertEqual(n, 2)
        trade_date = session_target_date()
        snaps = fetch_snapshots_for_date(trade_date)
        self.assertEqual(len(snaps), 2)
        self.assertEqual(snaps[0].symbol, "RELIANCE")

    def test_score_daily_watchlist(self):
        picks = [_fake_pick("RELIANCE")]
        save_watchlist_snapshot(picks, prep_date="2026-07-01")
        trade_date = session_target_date()

        with patch("analyzer.watchlist_history.can_score_trade_date", return_value=True):
            with patch("analyzer.watchlist_history._session_ohlc", return_value=(1045.0, 996.0, 1030.0)):
                scored = score_daily_watchlist(trade_date=trade_date)
        self.assertEqual(len(scored), 1)
        self.assertEqual(scored[0].outcome, "target_hit")

        with patch("analyzer.watchlist_history.can_score_trade_date", return_value=True):
            with patch("analyzer.watchlist_history._session_ohlc", return_value=(1045.0, 996.0, 1030.0)):
                again = score_daily_watchlist(trade_date=trade_date)
        self.assertEqual(len(again), 0)

    def test_success_report_win_rate(self):
        from analyzer.watchlist_history import init_watchlist_history

        init_watchlist_history()
        trade_date = "2026-07-01"
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                """
                INSERT INTO watchlist_outcomes (
                    id, trade_date, symbol, entry, stop_loss, target,
                    session_high, session_low, session_close, outcome, note, scored_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wo_2026-07-01_A", trade_date, "A", 100, 95, 110,
                    112, 99, 108, "target_hit", "ok", "now",
                ),
            )
            conn.execute(
                """
                INSERT INTO watchlist_outcomes (
                    id, trade_date, symbol, entry, stop_loss, target,
                    session_high, session_low, session_close, outcome, note, scored_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wo_2026-07-01_B", trade_date, "B", 100, 95, 110,
                    102, 94, 96, "stop_hit", "ok", "now",
                ),
            )

        report = build_watchlist_success_report(days=MIN_RETENTION_DAYS)
        self.assertEqual(report.target_hits, 1)
        self.assertEqual(report.stop_hits, 1)
        self.assertAlmostEqual(report.win_rate_pct, 50.0)

    def test_build_recent_suggested_picks(self):
        picks = [_fake_pick("RELIANCE"), _fake_pick("TCS", 2)]
        save_watchlist_snapshot(picks, prep_date="2026-07-01")
        trade_date = session_target_date()

        with patch("analyzer.watchlist_history.can_score_trade_date", return_value=True):
            with patch("analyzer.watchlist_history._session_ohlc", return_value=(1045.0, 996.0, 1030.0)):
                score_daily_watchlist(trade_date=trade_date)

        rows = build_recent_suggested_picks(MIN_RETENTION_DAYS)
        self.assertGreaterEqual(len(rows), 2)
        symbols = {r.symbol for _, r in rows}
        self.assertIn("RELIANCE", symbols)
        self.assertIn("TCS", symbols)
        reliance = next(r for _, r in rows if r.symbol == "RELIANCE")
        self.assertEqual(reliance.outcome, "target_hit")
        self.assertTrue(reliance.scored)


class TestScoreSessionPlan(unittest.TestCase):
    def test_mixed_conservative(self):
        outcome, _ = score_session_plan(
            entry=100, stop_loss=95, target=110,
            session_high=115, session_low=94, session_close=105,
        )
        self.assertEqual(outcome, "mixed")


if __name__ == "__main__":
    unittest.main()
