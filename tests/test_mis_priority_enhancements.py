"""Tests for trade selection, sector concentration, and related MIS enhancements."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.trade_selection import (
    clear_selection,
    effective_trade_plans,
    is_selected,
    load_selected_symbols,
    set_selected_symbols,
    toggle_selected,
)
from analyzer.watchlist_pins import PinnedPlan
from analyzer.watchlist_sector import sector_concentration_warning
from analyzer.watchlist_telegram import format_combined_prep_telegram, format_pinned_watchlist_telegram


class TestTradeSelection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "selected.json"
        self.p1 = patch("analyzer.trade_selection.SELECT_PATH", self.path)
        self.p2 = patch("analyzer.trade_selection.session_target_date", return_value="2026-07-07")
        self.p1.start()
        self.p2.start()

    def tearDown(self):
        self.p2.stop()
        self.p1.stop()
        self.tmp.cleanup()

    def test_toggle_max_two(self):
        ok, _ = toggle_selected("RELIANCE", max_selected=2)
        self.assertTrue(ok)
        ok, _ = toggle_selected("TCS", max_selected=2)
        self.assertTrue(ok)
        ok, msg = toggle_selected("INFY", max_selected=2)
        self.assertFalse(ok)
        self.assertIn("Max", msg)
        self.assertEqual(load_selected_symbols(), ["RELIANCE", "TCS"])

    def test_set_and_clear(self):
        set_selected_symbols(["HDFC", "ICICI"], max_selected=2)
        self.assertTrue(is_selected("HDFC"))
        clear_selection("2026-07-07")
        self.assertEqual(load_selected_symbols(), [])

    @patch("analyzer.trade_selection.load_pinned_plans")
    def test_effective_trade_plans_filters(self, load_pins):
        load_pins.return_value = [
            PinnedPlan("RELIANCE", 1, 1, 2, "x"),
            PinnedPlan("TCS", 1, 1, 2, "x"),
            PinnedPlan("INFY", 1, 1, 2, "x"),
        ]
        set_selected_symbols(["TCS", "INFY"], max_selected=2)
        plans = effective_trade_plans()
        self.assertEqual([p.symbol for p in plans], ["TCS", "INFY"])


class TestSectorConcentration(unittest.TestCase):
    def test_warns_on_four_same(self):
        class P:
            def __init__(self, sector):
                self.sector = sector

        picks = [P("Banking")] * 4 + [P("IT")]
        msg = sector_concentration_warning(picks, threshold=4)
        self.assertIsNotNone(msg)
        self.assertIn("Banking", msg)

    def test_no_warn_diverse(self):
        class P:
            def __init__(self, sector):
                self.sector = sector

        picks = [P("A"), P("B"), P("C"), P("D"), P("E")]
        self.assertIsNone(sector_concentration_warning(picks))


class TestTelegramEnhancements(unittest.TestCase):
    @patch("analyzer.gift_nifty.format_gift_nifty_telegram_line", return_value="*Gap cue:* test")
    @patch("analyzer.trade_selection.load_selected_symbols", return_value=["RELIANCE"])
    def test_combined_includes_gap_and_shares(self, _sel, _gap):
        msg = format_combined_prep_telegram(
            [PinnedPlan("RELIANCE", 2500.0, 2480.0, 2550.0, "2026-07-07")],
            [],
            market_bias="Bullish",
            prep_date="2026-07-06",
        )
        self.assertIn("Gap cue", msg)
        self.assertIn("RELIANCE", msg)
        self.assertIn("sh", msg)
        self.assertIn("Your 2 trades", msg)

    def test_equity_format_with_shares(self):
        msg = format_pinned_watchlist_telegram(
            [PinnedPlan("RELIANCE", 2500.0, 2480.0, 2550.0, "2026-07-07")],
            with_shares=True,
        )
        self.assertIn("RELIANCE", msg)


if __name__ == "__main__":
    unittest.main()
