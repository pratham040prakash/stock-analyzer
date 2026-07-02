"""Tests for beginner intraday tips."""

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.intraday_beginner_tips import (
    DEFAULT_INTRADAY_ALLOCATION_PCT,
    build_capital_budget,
    penny_stock_intraday_warning,
    session_timing_advice,
    ten_intraday_tips,
)

IST = ZoneInfo("Asia/Kolkata")


class TestIntradayBeginnerTips(unittest.TestCase):
    def test_capital_budget_half_allocation(self):
        b = build_capital_budget(10_000, allocation_pct=50, max_concurrent_trades=2)
        self.assertEqual(b.allocated_inr, 5_000)
        self.assertEqual(b.per_trade_budget_inr, 2_500)

    def test_opening_phase_blocks_entries(self):
        dt = datetime(2026, 4, 10, 9, 25, tzinfo=IST)
        adv = session_timing_advice(dt)
        self.assertEqual(adv.phase, "opening")
        self.assertFalse(adv.allow_new_entries)

    def test_core_phase_allows_entries(self):
        dt = datetime(2026, 4, 10, 11, 0, tzinfo=IST)
        adv = session_timing_advice(dt)
        self.assertEqual(adv.phase, "core")
        self.assertTrue(adv.allow_new_entries)

    def test_penny_warning(self):
        self.assertIsNotNone(penny_stock_intraday_warning(15.0))
        self.assertIsNone(penny_stock_intraday_warning(250.0))

    def test_ten_tips_count(self):
        self.assertEqual(len(ten_intraday_tips()), 10)

    def test_daily_checklist_has_phases(self):
        from analyzer.intraday_beginner_tips import daily_mis_checklist_items

        items = daily_mis_checklist_items()
        self.assertGreaterEqual(len(items), 10)
        phases = {i.phase for i in items}
        self.assertIn("night_before", phases)
        self.assertIn("during_session", phases)

    def test_default_allocation(self):
        self.assertEqual(DEFAULT_INTRADAY_ALLOCATION_PCT, 50.0)


if __name__ == "__main__":
    unittest.main()
