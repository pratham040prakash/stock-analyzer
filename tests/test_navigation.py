"""Tests for deferred tab navigation."""

import unittest
from unittest.mock import MagicMock, patch

from ui.navigation import _NAV_REQUEST_KEY, apply_pending_nav_tab, request_nav_tab


class TestNavigation(unittest.TestCase):
    def test_apply_pending_sets_nav_tab(self):
        state = {_NAV_REQUEST_KEY: "Suggestions", "nav_tab": "Market Pulse"}
        mock_st = MagicMock()
        mock_st.session_state = state

        with patch("ui.navigation.st", mock_st):
            apply_pending_nav_tab()

        self.assertNotIn(_NAV_REQUEST_KEY, state)
        self.assertEqual(state["nav_tab"], "Suggestions")
        self.assertEqual(state["nav_group"], "🎯 Suggestions")

    def test_apply_pending_noop(self):
        state = {"nav_tab": "Suggestions"}
        mock_st = MagicMock()
        mock_st.session_state = state

        with patch("ui.navigation.st", mock_st):
            apply_pending_nav_tab()

        self.assertEqual(state["nav_tab"], "Suggestions")

    def test_request_nav_tab_queues_and_reruns(self):
        state: dict = {}
        mock_st = MagicMock()
        mock_st.session_state = state

        with patch("ui.navigation.st", mock_st):
            request_nav_tab("Track Record", intraday_ticker="TCS")

        self.assertEqual(state[_NAV_REQUEST_KEY], "Track Record")
        self.assertEqual(state["intraday_ticker"], "TCS")
        mock_st.rerun.assert_called_once()


if __name__ == "__main__":
    unittest.main()
