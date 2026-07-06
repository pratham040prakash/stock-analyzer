"""Tests for watchlist pins, live plan, and EOD scoring."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.watchlist_eod import score_session_plan
from analyzer.watchlist_plan_tracker import assess_live_plan
from analyzer.watchlist_pins import (
    TOP_TOMORROW_PICKS,
    clear_pins,
    is_pinned,
    load_pinned_plans,
    pin_pick,
    sync_auto_top_picks,
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

    def test_sync_auto_top_picks(self):
        class _Pick:
            def __init__(self, sym, entry, stop, target, side="LONG"):
                self.nse_symbol = sym
                self.entry = entry
                self.stop_loss = stop
                self.target = target
                self.side = side

        picks = [
            _Pick("RELIANCE", 2850, 2820, 2920),
            _Pick("TCS", 4000, 4100, 3900, side="SHORT"),
            _Pick("INFY", 1800, 1780, 1850),
        ]
        synced = sync_auto_top_picks(picks, limit=TOP_TOMORROW_PICKS)
        self.assertEqual(len(synced), 3)
        self.assertTrue(is_pinned("RELIANCE"))
        short = [p for p in synced if p.symbol == "TCS"][0]
        self.assertEqual(short.side, "SHORT")
        raw = self.path.read_text(encoding="utf-8")
        self.assertIn('"auto": true', raw)


class TestLivePlan(unittest.TestCase):
    def test_near_target(self):
        s = assess_live_plan(2918, entry=2850, stop_loss=2820, target=2920, symbol="REL")
        self.assertIn(s.label, ("Near T1", "Near target", "At/above target", "T1 hit — book 40%"))

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

    def test_short_target_hit(self):
        outcome, note = score_session_plan(
            entry=100, stop_loss=105, target=90,
            session_high=103, session_low=88, session_close=92,
            side="SHORT",
        )
        self.assertEqual(outcome, "target_hit")
        self.assertIn("Low", note)

    def test_short_stop_hit(self):
        outcome, _ = score_session_plan(
            entry=100, stop_loss=105, target=90,
            session_high=106, session_low=95, session_close=104,
            side="SHORT",
        )
        self.assertEqual(outcome, "stop_hit")

    def test_short_live_near_stop(self):
        s = assess_live_plan(
            1009, entry=1000, stop_loss=1010, target=990,
            symbol="X", side="SHORT",
        )
        self.assertEqual(s.label, "Near stop")

    def test_short_position_hint(self):
        from analyzer.watchlist_position_size import equity_position_hint

        hint = equity_position_hint(
            "HDFCBANK",
            entry=1000,
            stop_loss=1015,
            target=970,
            allocated_inr=50_000,
            max_risk_pct=1.0,
            max_concurrent_trades=2,
            per_trade_budget_inr=25_000,
            side="SHORT",
        )
        self.assertTrue(hint.suggested_shares and hint.suggested_shares > 0)
        self.assertTrue(hint.can_enter)


class TestWatchlistTelegram(unittest.TestCase):
    def test_format(self):
        from analyzer.watchlist_pins import PinnedPlan

        msg = format_pinned_watchlist_telegram([
            PinnedPlan("RELIANCE", 2850, 2820, 2920, "2026-07-01"),
        ], market_bias="BULLISH")
        self.assertIn("RELIANCE", msg)
        self.assertIn("2,850", msg)
        self.assertIn("LONG", msg)

    def test_format_short(self):
        from analyzer.watchlist_pins import PinnedPlan

        msg = format_pinned_watchlist_telegram([
            PinnedPlan(
                "HDFCBANK", 1000, 1010, 990, "2026-07-01", side="SHORT",
            ),
        ], market_bias="BEARISH")
        self.assertIn("SHORT", msg)
        self.assertIn("HDFCBANK", msg)


if __name__ == "__main__":
    unittest.main()
