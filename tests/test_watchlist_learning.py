"""Tests for watchlist strategy learning from outcomes."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.watchlist_learning import (
    DEFAULT_STRATEGY,
    PickFeatureRow,
    apply_watchlist_strategy_tuning,
    build_watchlist_learning_report,
    get_watchlist_strategy,
    reset_watchlist_strategy,
)


class TestWatchlistLearning(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "journal.db"
        self.strat = Path(self.tmp.name) / "strategy.json"
        self.jp = patch("analyzer.suggestion_journal.journal_db_path", return_value=self.db)
        self.je = patch("analyzer.watchlist_eod.journal_db_path", return_value=self.db)
        self.jh = patch("analyzer.watchlist_history.journal_db_path", return_value=self.db)
        self.jl = patch("analyzer.watchlist_learning.journal_db_path", return_value=self.db)
        self.jb = patch("analyzer.broker_truth.learning.journal_db_path", return_value=self.db)
        self.bts = patch(
            "analyzer.broker_truth.store.broker_truth_db_path",
            return_value=Path(self.tmp.name) / "broker.db",
        )
        self.sp = patch("analyzer.watchlist_learning.strategy_path", return_value=self.strat)
        for p in (self.jp, self.je, self.jh, self.jl, self.jb, self.bts, self.sp):
            p.start()
        reset_watchlist_strategy()
        self._seed_outcomes()

    def tearDown(self):
        for p in (self.bts, self.jb, self.sp, self.jl, self.jh, self.je, self.jp):
            p.stop()
        self.tmp.cleanup()

    def _seed_outcomes(self) -> None:
        from analyzer.watchlist_eod import init_watchlist_outcomes
        from analyzer.watchlist_history import init_watchlist_history

        init_watchlist_outcomes()
        init_watchlist_history()
        with sqlite3.connect(self.db) as conn:
            for sym, outcome, atr in [
                ("A", "target_hit", 2.5),
                ("B", "target_hit", 2.2),
                ("C", "target_hit", 2.0),
                ("D", "flat_positive", 1.8),
                ("E", "stop_hit", 1.2),
                ("F", "stop_hit", 1.1),
                ("G", "stop_hit", 1.0),
                ("H", "stop_hit", 1.3),
            ]:
                conn.execute(
                    """
                    INSERT INTO watchlist_outcomes (
                        id, trade_date, symbol, entry, stop_loss, target,
                        session_high, session_low, session_close, outcome, note, scored_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"wo_2026-07-01_{sym}", "2026-07-01", sym, 100, 95, 110,
                        112, 99, 108, outcome, "test", "now",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO watchlist_daily_snapshots (
                        id, trade_date, prep_date, symbol, rank, entry, stop_loss,
                        target, prep_score, market_bias, saved_at,
                        checklist_passed, atr_pct, rsi, volume_ratio,
                        sector_tailwind, macd_bullish
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"snap_2026-07-01_{sym}", "2026-07-01", "2026-06-30", sym, 1,
                        100, 95, 110, 50, "BULLISH", "now",
                        4, atr, 58, 1.2, 1, 1,
                    ),
                )

    def test_report_win_rate(self):
        report = build_watchlist_learning_report(days=14)
        self.assertEqual(report.samples, 8)
        self.assertEqual(report.wins, 4)
        self.assertEqual(report.losses, 4)
        self.assertAlmostEqual(report.win_rate_pct, 50.0)

    def test_tighten_on_low_win_rate(self):
        report = build_watchlist_learning_report()
        tuned = apply_watchlist_strategy_tuning(report)
        self.assertTrue(tuned.changes or tuned.strategy["min_atr_pct"] >= DEFAULT_STRATEGY["min_atr_pct"])
        gates = get_watchlist_strategy()
        self.assertGreaterEqual(gates["min_checklist_passed"], DEFAULT_STRATEGY["min_checklist_passed"])


if __name__ == "__main__":
    unittest.main()
