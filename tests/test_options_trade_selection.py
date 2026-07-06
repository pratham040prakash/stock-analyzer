"""Tests for single options leg selection."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.options_trade_selection import (
    is_option_selected,
    load_selected_option,
    toggle_option_selected,
)


class TestOptionsTradeSelection(unittest.TestCase):
    def test_toggle_one_leg(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selected_option.json"
            with patch("analyzer.options_trade_selection.SELECT_PATH", path):
                with patch("analyzer.options_trade_selection.session_target_date", return_value="2026-07-07"):
                    ok, _ = toggle_option_selected("NIFTY", "CE", 24500)
                    self.assertTrue(ok)
                    self.assertTrue(is_option_selected("NIFTY", "CE", 24500))
                    pick = load_selected_option()
                    self.assertEqual(pick["fno_symbol"], "NIFTY")

                    ok2, _ = toggle_option_selected("BANKNIFTY", "PE", 52000)
                    self.assertTrue(ok2)
                    self.assertFalse(is_option_selected("NIFTY", "CE", 24500))
                    self.assertTrue(is_option_selected("BANKNIFTY", "PE", 52000))

                    ok3, _ = toggle_option_selected("BANKNIFTY", "PE", 52000)
                    self.assertFalse(ok3)
                    self.assertIsNone(load_selected_option())


if __name__ == "__main__":
    unittest.main()
