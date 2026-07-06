"""Tests for T1/T2/T3 trade ladder."""

import unittest

from analyzer.trade_ladder import (
    assess_equity_ladder,
    assess_options_ladder,
    build_equity_ladder,
    build_options_ladder,
)


class TestTradeLadder(unittest.TestCase):
    def test_equity_long_ladder_levels(self):
        ladder = build_equity_ladder("LONG", 1000.0, 990.0, 1015.0, pivot_r2=1030.0)
        self.assertEqual(ladder.target, 1015.0)
        self.assertEqual(ladder.target2, 1030.0)
        self.assertGreater(ladder.target3, ladder.target2)
        self.assertEqual(ladder.stops_after[0], 1000.0)

    def test_t1_hit_moves_stop_to_breakeven(self):
        ladder = build_equity_ladder("LONG", 1000.0, 990.0, 1015.0)
        status = assess_equity_ladder(1016.0, ladder, symbol="X")
        self.assertEqual(status.label, "T1 hit — book 40%")
        self.assertEqual(status.active_stop, 1000.0)
        self.assertEqual(status.stage, 1)

    def test_t2_hit_trails_stop_to_t1(self):
        ladder = build_equity_ladder("LONG", 1000.0, 990.0, 1015.0)
        t2 = ladder.target2
        status = assess_equity_ladder(t2 + 1, ladder, symbol="X")
        self.assertEqual(status.label, "T2 hit — trail to T3")
        self.assertEqual(status.active_stop, 1015.0)
        self.assertIn("Move stop", status.detail)
        self.assertIn("1,015", status.detail)

    def test_stop_trail_telegram_has_amounts(self):
        ladder = build_equity_ladder("LONG", 1000.0, 990.0, 1015.0)
        from analyzer.trade_ladder import format_stop_trail_telegram
        text = format_stop_trail_telegram(ladder)
        self.assertIn("990", text)
        self.assertIn("1,000", text)
        self.assertIn("1,015", text)

    def test_options_premium_ladder(self):
        ladder = build_options_ladder(100.0)
        self.assertEqual(ladder.target, 150.0)
        self.assertEqual(ladder.target2, 200.0)
        self.assertEqual(ladder.target3, 250.0)
        status = assess_options_ladder(151.0, ladder, label="NIFTY CE")
        self.assertIn("T1", status.label)

    def test_equity_short_ladder_levels(self):
        ladder = build_equity_ladder("SHORT", 1000.0, 1010.0, 990.0, pivot_r2=980.0)
        self.assertEqual(ladder.target, 990.0)
        self.assertGreater(ladder.initial_stop, ladder.entry)
        self.assertLess(ladder.target, ladder.entry)

    def test_short_near_stop(self):
        ladder = build_equity_ladder("SHORT", 1000.0, 1010.0, 990.0)
        status = assess_equity_ladder(1009.0, ladder, symbol="X")
        self.assertEqual(status.label, "Near stop")

    def test_short_t1_hit(self):
        ladder = build_equity_ladder("SHORT", 1000.0, 1010.0, 990.0)
        status = assess_equity_ladder(989.0, ladder, symbol="X")
        self.assertEqual(status.label, "T1 hit — book 40%")
        self.assertEqual(status.stage, 1)


if __name__ == "__main__":
    unittest.main()
