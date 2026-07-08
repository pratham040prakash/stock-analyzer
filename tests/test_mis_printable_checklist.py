"""Tests for printable MIS checklist formatter."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.mis_printable_checklist import (
    format_printable_mis_checklist,
    gather_printable_checklist_context,
)
from analyzer.options_expiry_watchlist import OptionsExpiryPick
from analyzer.watchlist_pins import PinnedPlan


class TestMisPrintableChecklist(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pins = self.root / "pinned_watchlist.json"
        self.prefs = self.root / "prefs.json"
        self.select = self.root / "selected_trades.json"
        self.opt_select = self.root / "selected_option.json"
        self.pins.write_text(
            """{
  "prep_date": "2026-07-05",
  "picks": [
    {"symbol": "TCS", "entry": 4000, "stop_loss": 3950, "target": 4100, "side": "LONG"},
    {"symbol": "INFY", "entry": 1800, "stop_loss": 1770, "target": 1860, "side": "LONG"}
  ]
}""",
            encoding="utf-8",
        )
        self.prefs.write_text(
            """{
  "capital": 50000,
  "allocation_pct": 50,
  "max_risk_pct": 1.0,
  "max_trades": 2
}""",
            encoding="utf-8",
        )
        self.select.write_text(
            '{"trade_date": "2026-07-07", "symbols": ["TCS"], "auto": false}',
            encoding="utf-8",
        )
        self.patches = [
            patch("analyzer.watchlist_pins.PINS_PATH", self.pins),
            patch("analyzer.intraday_prefs.PREFS_PATH", self.prefs),
            patch("analyzer.trade_selection.SELECT_PATH", self.select),
            patch("analyzer.options_trade_selection.SELECT_PATH", self.opt_select),
            patch("analyzer.watchlist_history.session_target_date", return_value="2026-07-07"),
            patch("analyzer.mis_printable_checklist.session_target_date", return_value="2026-07-07"),
            patch("analyzer.trade_selection.session_target_date", return_value="2026-07-07"),
            patch("analyzer.options_trade_selection.session_target_date", return_value="2026-07-07"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_includes_equity_levels_and_capital(self):
        opt = OptionsExpiryPick(
            rank=1,
            fno_symbol="NIFTY",
            name="Nifty",
            expiry="10-Jul-2026",
            spot=25000,
            signal="BUY CE",
            option_type="CE",
            strike=25050,
            premium=100,
            lot_size=75,
            lot_cost=7500,
            stop_premium=65,
            target_premium=150,
            iv=12,
            recommended=True,
            reason="",
            target2_premium=200,
            target3_premium=250,
        )
        msg = format_printable_mis_checklist(
            options_picks=[opt],
            market_bias="BULLISH",
            include_live_cues=False,
        )
        self.assertIn("TCS", msg)
        self.assertIn("₹4,000", msg)
        self.assertIn("BULLISH", msg)
        self.assertIn("NIFTY", msg)
        self.assertIn("₹100", msg)
        self.assertIn("₹50,000", msg)
        self.assertIn("Prep all tonight", msg)
        self.assertIn("3:20 PM", msg)

    def test_gather_context_selected_symbols(self):
        ctx = gather_printable_checklist_context(include_live_cues=False)
        self.assertEqual(ctx.selected_symbols, ["TCS"])
        self.assertEqual(len(ctx.equity_plans), 2)
        self.assertAlmostEqual(ctx.allocated_inr, 25000.0)

    def test_blank_placeholders_when_no_picks(self):
        self.pins.write_text('{"prep_date": "", "picks": []}', encoding="utf-8")
        with patch("analyzer.mis_printable_checklist.fetch_snapshots_for_date", return_value=[]):
            msg = format_printable_mis_checklist(include_live_cues=False, market_bias="")
        self.assertIn("#1 __________", msg)
        self.assertIn("MY 2 TRADES: TCS", msg)


if __name__ == "__main__":
    unittest.main()
