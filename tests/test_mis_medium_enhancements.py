"""Tests for NSE holidays, auto-pick sectors, selected win rate."""

import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from analyzer.nse_holidays import is_nse_trading_day, next_nse_trading_day, skip_scheduled_job_reason
from analyzer.trade_selection import _pick_diverse_from_pins, auto_select_top_by_rank
from analyzer.watchlist_pins import PinnedPlan

IST = ZoneInfo("Asia/Kolkata")


class TestNseHolidays(unittest.TestCase):
    @patch("analyzer.nse_holidays.nse_holidays", return_value={"2026-01-26"})
    def test_republic_day_closed(self, _h):
        self.assertFalse(is_nse_trading_day("2026-01-26"))
        self.assertTrue(is_nse_trading_day("2026-01-27"))

    @patch("analyzer.nse_holidays.nse_holidays", return_value=set())
    def test_weekend_closed(self, _h):
        self.assertFalse(is_nse_trading_day(date(2026, 7, 4)))

    @patch("analyzer.nse_holidays.nse_holidays", return_value={"2026-01-26"})
    def test_skip_reason_holiday(self, _h):
        mon_holiday = datetime(2026, 1, 26, 9, 0, tzinfo=IST)
        reason = skip_scheduled_job_reason(mon_holiday)
        self.assertIsNotNone(reason)
        self.assertIn("session", reason.lower())

    @patch("analyzer.nse_holidays.nse_holidays", return_value={"2026-01-26"})
    def test_next_trading_day_skips_holiday(self, _h):
        self.assertEqual(next_nse_trading_day(date(2026, 1, 25)), date(2026, 1, 27))


class TestAutoPickSectors(unittest.TestCase):
    def test_picks_different_sectors(self):
        pins = [
            PinnedPlan("A", 1, 1, 2, "x", sector="Banking"),
            PinnedPlan("B", 1, 1, 2, "x", sector="Banking"),
            PinnedPlan("C", 1, 1, 2, "x", sector="IT"),
        ]
        syms = _pick_diverse_from_pins(pins, max_selected=2, max_same_sector=1)
        self.assertEqual(syms, ["A", "C"])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sel.json"
        self.p1 = patch("analyzer.trade_selection.SELECT_PATH", self.path)
        self.p2 = patch("analyzer.trade_selection.session_target_date", return_value="2026-07-07")
        self.p1.start()
        self.p2.start()

    def tearDown(self):
        self.p2.stop()
        self.p1.stop()
        self.tmp.cleanup()

    @patch("analyzer.trade_selection.load_pinned_plans")
    def test_auto_select_diverse(self, load_pins):
        load_pins.return_value = [
            PinnedPlan("RELIANCE", 1, 1, 2, "x", sector="Energy"),
            PinnedPlan("HDFC", 1, 1, 2, "x", sector="Banking"),
            PinnedPlan("ICICI", 1, 1, 2, "x", sector="Banking"),
        ]
        ok, msg = auto_select_top_by_rank(trade_date="2026-07-07")
        self.assertTrue(ok)
        self.assertIn("RELIANCE", msg)
        self.assertIn("HDFC", msg)
        self.assertNotIn("ICICI", msg)


class TestSelectedWinRate(unittest.TestCase):
    def test_aggregate_empty(self):
        from analyzer.watchlist_history import _aggregate_watchlist_outcomes

        report = _aggregate_watchlist_outcomes(7, [])
        self.assertEqual(report.total_picks, 0)


if __name__ == "__main__":
    unittest.main()
