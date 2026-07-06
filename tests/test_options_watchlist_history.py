"""Tests for options watchlist snapshot and scoring."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.options_expiry_watchlist import OptionsExpiryPick
from analyzer.options_watchlist_history import (
    build_options_session_rows,
    fetch_options_snapshots_for_date,
    save_options_watchlist_snapshot,
    score_options_daily_watchlist,
    session_target_date,
)
from analyzer.watchlist_eod import score_session_plan


def _fake_option_pick(**kw) -> OptionsExpiryPick:
    defaults = dict(
        rank=1,
        fno_symbol="NIFTY",
        name="Nifty 50",
        expiry="07-Jul-2026",
        spot=24300.0,
        signal="BUY CE",
        option_type="CE",
        strike=24300.0,
        premium=75.0,
        lot_size=75,
        lot_cost=5625.0,
        stop_premium=48.75,
        target_premium=112.5,
        iv=12.0,
        recommended=True,
        reason="test",
    )
    defaults.update(kw)
    return OptionsExpiryPick(**defaults)


class TestOptionsWatchlistHistory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "journal.db"
        self.jp = patch("analyzer.suggestion_journal.journal_db_path", return_value=self.db)
        self.jh = patch("analyzer.options_watchlist_history.journal_db_path", return_value=self.db)
        self.jp.start()
        self.jh.start()

    def tearDown(self):
        self.jh.stop()
        self.jp.stop()
        self.tmp.cleanup()

    def test_save_and_fetch_snapshot(self):
        n = save_options_watchlist_snapshot([_fake_option_pick()])
        self.assertEqual(n, 1)
        snaps = fetch_options_snapshots_for_date(session_target_date())
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0].fno_symbol, "NIFTY")
        self.assertAlmostEqual(snaps[0].entry, 75.0)

    def test_score_premium_target_hit(self):
        save_options_watchlist_snapshot([_fake_option_pick()])
        trade_date = session_target_date()
        with patch("analyzer.options_watchlist_history.can_score_trade_date", return_value=True):
            with patch(
                "analyzer.options_watchlist_history.fetch_option_premium_ohlc",
                return_value=(120.0, 70.0, 110.0),
            ):
                scored = score_options_daily_watchlist(trade_date=trade_date)
        self.assertEqual(len(scored), 1)
        self.assertEqual(scored[0].outcome, "target_hit")

        _, rows = build_options_session_rows(trade_date)
        self.assertTrue(rows[0].scored)
        self.assertEqual(rows[0].outcome, "target_hit")

    def test_premium_score_plan(self):
        outcome, _ = score_session_plan(
            entry=75, stop_loss=48.75, target=112.5,
            session_high=115, session_low=70, session_close=108,
        )
        self.assertEqual(outcome, "target_hit")


if __name__ == "__main__":
    unittest.main()
