"""Tests for UI search, nav, and onboarding tour."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.onboarding_state import get_tour_step, is_tour_complete, reset_onboarding, set_tour_step
from analyzer.unified_search import TAB_ALIASES, match_tab_command, unified_search


class TestUnifiedSearch(unittest.TestCase):
    def test_tab_alias(self):
        self.assertEqual(match_tab_command("alpha"), "Alpha AI")
        self.assertEqual(match_tab_command(">suggestions"), "Suggestions")

    def test_tab_aliases_nonempty(self):
        self.assertIn("alpha", TAB_ALIASES)
        self.assertIn("portfolio", TAB_ALIASES)

    @patch("analyzer.unified_search.search_indian_stocks", return_value=[])
    def test_direct_symbol(self, _mock):
        hits = unified_search("TCS")
        self.assertTrue(any("TCS" in h.symbol for h in hits))


class TestOnboardingTour(unittest.TestCase):
    def test_tour_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "onboarding.json"
            with patch("analyzer.onboarding_state.STATE_PATH", path):
                reset_onboarding()
                self.assertEqual(get_tour_step(), 0)
                self.assertFalse(is_tour_complete())
                set_tour_step(3)
                self.assertEqual(get_tour_step(), 3)
                set_tour_step(5)
                self.assertTrue(is_tour_complete())


if __name__ == "__main__":
    unittest.main()
