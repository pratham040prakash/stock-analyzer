"""Tests for position sizing, EOD summary, nightly scheduler."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from analyzer.watchlist_position_size import equity_position_hint, format_shares_cell

IST = ZoneInfo("Asia/Kolkata")


class TestWatchlistPositionSize(unittest.TestCase):
    def test_shares_from_risk_budget(self):
        hint = equity_position_hint(
            "RELIANCE",
            entry=2500.0,
            stop_loss=2480.0,
            target=2550.0,
            allocated_inr=25_000.0,
            max_risk_pct=1.0,
        )
        self.assertGreater(hint.suggested_shares or 0, 0)
        self.assertEqual(format_shares_cell(hint), str(hint.suggested_shares))

    def test_wide_stop_skips(self):
        hint = equity_position_hint(
            "PENNY",
            entry=10.0,
            stop_loss=5.0,
            target=15.0,
            allocated_inr=25_000.0,
            max_risk_pct=1.0,
        )
        self.assertFalse(hint.can_enter)


class TestNightlyScheduler(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sched.json"
        self.p = patch("analyzer.nightly_prep_scheduler.STATE_PATH", self.path)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()

    @patch("analyzer.nightly_prep_scheduler.session_target_date", return_value="2026-07-07")
    def test_was_sent(self, _d):
        from analyzer.nightly_prep_scheduler import mark_nightly_prep_sent, was_nightly_prep_sent

        self.assertFalse(was_nightly_prep_sent("2026-07-07"))
        mark_nightly_prep_sent("2026-07-07")
        self.assertTrue(was_nightly_prep_sent("2026-07-07"))


class TestMisEodSummary(unittest.TestCase):
    def test_format_empty(self):
        from analyzer.mis_eod_summary import MisEodSummary, format_mis_eod_telegram

        msg = format_mis_eod_telegram(MisEodSummary(trade_date="2026-07-03"))
        self.assertIn("2026-07-03", msg)
        self.assertIn("Did targets hit", msg)

    def test_trade_date_weekday(self):
        from analyzer.mis_eod_summary import mis_eod_trade_date

        mon = datetime(2026, 7, 6, 16, 0, tzinfo=IST)
        self.assertEqual(mis_eod_trade_date(mon), "2026-07-06")
        sat = datetime(2026, 7, 4, 16, 0, tzinfo=IST)
        self.assertIsNone(mis_eod_trade_date(sat))


if __name__ == "__main__":
    unittest.main()
