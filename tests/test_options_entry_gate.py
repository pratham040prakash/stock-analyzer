"""Tests for 9:45 OR + OTM options entry gate."""

import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from analyzer.options_entry_gate import (
    BLOCK_OTM_PCT,
    assess_option_entry_gate,
    assess_pick_entry_gate,
    gate_label_short,
)

IST = ZoneInfo("Asia/Kolkata")


class TestOptionsEntryGate(unittest.TestCase):
    def test_before_945_observe(self):
        now = datetime(2026, 7, 9, 9, 30, tzinfo=IST)
        gate = assess_option_entry_gate(
            "PE",
            fno_symbol="BANKNIFTY",
            strike=55000,
            spot=57200,
            or_high=57244,
            or_low=56800,
            now=now,
        )
        self.assertEqual(gate.phase, "observe")
        self.assertFalse(gate.allowed)
        self.assertIn("9:45", gate.headline)

    def test_pe_do_not_enter_above_or_high(self):
        now = datetime(2026, 7, 9, 10, 0, tzinfo=IST)
        gate = assess_option_entry_gate(
            "PE",
            fno_symbol="BANKNIFTY",
            strike=56800,
            spot=57300,
            or_high=57244,
            or_low=56800,
            now=now,
        )
        self.assertEqual(gate.phase, "do_not_enter")
        self.assertIn("DO NOT ENTER PE", gate.headline)

    def test_pe_enter_ok_below_or_low(self):
        now = datetime(2026, 7, 9, 10, 0, tzinfo=IST)
        gate = assess_option_entry_gate(
            "PE",
            fno_symbol="BANKNIFTY",
            strike=55000,
            spot=56750,
            or_high=57244,
            or_low=56800,
            now=now,
        )
        self.assertEqual(gate.phase, "enter_ok")
        self.assertTrue(gate.allowed)

    def test_ce_do_not_enter_below_or_low(self):
        now = datetime(2026, 7, 9, 10, 0, tzinfo=IST)
        gate = assess_option_entry_gate(
            "CE",
            fno_symbol="NIFTY",
            strike=24500,
            spot=24300,
            or_high=24450,
            or_low=24350,
            now=now,
        )
        self.assertEqual(gate.phase, "do_not_enter")
        self.assertIn("DO NOT ENTER CE", gate.headline)

    def test_otm_block_above_threshold(self):
        now = datetime(2026, 7, 9, 10, 0, tzinfo=IST)
        # PE strike 55000 vs spot 57200 => ~3.85% OTM
        gate = assess_option_entry_gate(
            "PE",
            fno_symbol="BANKNIFTY",
            strike=55000,
            spot=57200,
            or_high=58000,
            or_low=56500,
            now=now,
        )
        self.assertEqual(gate.phase, "do_not_enter")
        self.assertIn("OTM", gate.headline)
        self.assertGreaterEqual(gate.otm_pct or 0, BLOCK_OTM_PCT)

    def test_gate_label_short(self):
        gate = assess_option_entry_gate(
            "PE",
            fno_symbol="BANKNIFTY",
            strike=56800,
            spot=57300,
            or_high=57244,
            or_low=56800,
            now=datetime(2026, 7, 9, 10, 0, tzinfo=IST),
        )
        label = gate_label_short(gate)
        self.assertIn(gate.emoji, label)
        self.assertIn("DO NOT ENTER", label)

    @patch("analyzer.options_entry_gate.get_live_ltp", return_value=(57300.0, "kite"))
    @patch(
        "analyzer.options_entry_gate.fetch_symbol_opening_range",
        return_value=(57244.0, 56800.0),
    )
    def test_assess_pick_entry_gate(self, _or, _ltp):
        pick = SimpleNamespace(fno_symbol="BANKNIFTY", option_type="PE", strike=56800)
        gate = assess_pick_entry_gate(
            pick,
            now=datetime(2026, 7, 9, 10, 0, tzinfo=IST),
        )
        self.assertIsNotNone(gate)
        self.assertEqual(gate.phase, "do_not_enter")


if __name__ == "__main__":
    unittest.main()
