"""Tests for grouped navigation and onboarding."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.onboarding_state import dismiss_onboarding, is_onboarding_dismissed, is_tour_complete, reset_onboarding
from ui.theme import DEFAULT_NAV_TAB, NAV_GROUPS, NAV_TABS, ensure_tab_in_group, nav_group_for_tab


class TestNavGroups(unittest.TestCase):
    def test_all_tabs_in_groups(self):
        grouped = [t for tabs in NAV_GROUPS.values() for t in tabs]
        self.assertEqual(sorted(grouped), sorted(NAV_TABS))

    def test_suggestions_in_core_group(self):
        self.assertIn("Suggestions", NAV_GROUPS["🎯 Suggestions"])
        self.assertIn("Track Record", NAV_GROUPS["🎯 Suggestions"])

    def test_group_for_tab(self):
        self.assertEqual(nav_group_for_tab("Suggestions"), "🎯 Suggestions")
        self.assertEqual(nav_group_for_tab("Varsity TA"), "📚 Learn")

    def test_ensure_tab_in_group(self):
        self.assertEqual(
            ensure_tab_in_group("Suggestions", "🎯 Suggestions"),
            "Suggestions",
        )
        self.assertEqual(
            ensure_tab_in_group("Varsity TA", "🎯 Suggestions"),
            "Suggestions",
        )

    def test_default_tab(self):
        self.assertEqual(DEFAULT_NAV_TAB, "Suggestions")


class TestOnboardingState(unittest.TestCase):
    def test_dismiss_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "onboarding.json"
            with patch("analyzer.onboarding_state.STATE_PATH", path):
                self.assertFalse(is_onboarding_dismissed())
                dismiss_onboarding()
                self.assertTrue(is_onboarding_dismissed())
                self.assertTrue(is_tour_complete())
                reset_onboarding()
                self.assertFalse(is_onboarding_dismissed())


if __name__ == "__main__":
    unittest.main()
