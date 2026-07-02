"""Tests for watchlist pins, live plan, and EOD scoring."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.watchlist_eod import score_session_plan
from analyzer.watchlist_plan_tracker import assess_live_plan
from analyzer.watchlist_pins import (
    clear_pins,
    is_pinned,
    load_pinned_plans,
    pin_pick,
    toggle_pin,
    unpin_pick,
)
from analyzer.watchlist_telegram import format_pinned_watchlist_telegram


class TestWatchlistPins(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "pins.json"
        self.patcher = patch("analyzer.watchlist_pins.PINS_PATH", self.path)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.tmp.cleanup()

    def test_pin_and_unpin(self):
        ok, _ = pin_pick("RELIANCE", entry=2850, stop_loss=2820, target=2920)
        self.assertTrue(ok)
        self.assertTrue(is_pinned("RELIANCE"))
        self.assertEqual(len(load_pinned_plans()), 1)
        unpin_pick("RELIANCE")
        self.assertFalse(is_pinned("RELIANCE"))

    def test_max_pins(self):
        pin_pick("A", entry=100, stop_loss=95, target=110, max_pins=2)
        pin_pick("B", entry=100, stop_loss=95, target=110, max_pins=2)
        ok, msg = pin_pick("C", entry=100, stop_loss=95, target=110, max_pins=2)
        self.assertFalse(ok)
        self.assertIn("Max", msg)
        clear_pins()
        self.assertEqual(len(load_pinned_plans()), 0)

    def test_toggle(self):
        pinned, _ = toggle_pin("TCS", entry=4000, stop_loss=3950, target=4100)
        self.assertTrue(pinned)
        pinned, _ = toggle_pin("TCS", entry=4000, stop_loss=3950, target=4100)
        self.assertFalse(pinned)


class TestLivePlan(unittest.TestCase):
    def test_near_target(self):
        s = assess_live_plan(2918, entry=2850, stop_loss=2820, target=2920, symbol="REL")
        self.assertIn(s.label, ("Near target", "At/above target"))

    def test_below_entry(self):
        s = assess_live_plan(2835, entry=2850, stop_loss=2820, target=2920, symbol="REL")
        self.assertEqual(s.label, "Below entry")

    def test_at_stop(self):
        s = assess_live_plan(2815, entry=2850, stop_loss=2820, target=2920, symbol="REL")
        self.assertEqual(s.label, "At/below stop")


class TestEodScore(unittest.TestCase):
    def test_target_hit(self):
        outcome, note = score_session_plan(
            entry=100, stop_loss=95, target=110,
            session_high=112, session_low=99, session_close=108,
        )
        self.assertEqual(outcome, "target_hit")

    def test_stop_hit(self):
        outcome, _ = score_session_plan(
            entry=100, stop_loss=95, target=110,
            session_high=102, session_low=94, session_close=96,
        )
        self.assertEqual(outcome, "stop_hit")


class TestWatchlistTelegram(unittest.TestCase):
    def test_format(self):
        from analyzer.watchlist_pins import PinnedPlan

        msg = format_pinned_watchlist_telegram([
            PinnedPlan("RELIANCE", 2850, 2820, 2920, "2026-07-01"),
        ], market_bias="BULLISH")
        self.assertIn("RELIANCE", msg)
        self.assertIn("2,850", msg)


if __name__ == "__main__":
    unittest.main()
