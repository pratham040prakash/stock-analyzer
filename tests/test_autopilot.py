"""Tests for Autopilot status and post-close scan scheduler."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class TestPostCloseScan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "post_close.json"
        self.p = patch("analyzer.post_close_scan_scheduler.STATE_PATH", self.path)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()

    @patch("analyzer.post_close_scan_scheduler.session_target_date", return_value="2026-07-07")
    def test_was_sent(self, _d):
        from analyzer.post_close_scan_scheduler import (
            mark_post_close_scan_sent,
            was_post_close_scan_sent,
        )

        self.assertFalse(was_post_close_scan_sent("2026-07-07"))
        mark_post_close_scan_sent("2026-07-07", equity_count=5)
        self.assertTrue(was_post_close_scan_sent("2026-07-07"))


class TestMorningSuggestions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "morning.json"
        self.p = patch("analyzer.morning_suggestions_scheduler.STATE_PATH", self.path)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()

    @patch("analyzer.morning_suggestions_scheduler.session_target_date", return_value="2026-07-07")
    def test_was_sent(self, _d):
        from analyzer.morning_suggestions_scheduler import (
            mark_morning_suggestions_sent,
            was_morning_suggestions_sent,
        )

        mark_morning_suggestions_sent("2026-07-07")
        self.assertTrue(was_morning_suggestions_sent("2026-07-07"))


class TestAutopilotStatus(unittest.TestCase):
    @patch("analyzer.autopilot_status.is_macos", return_value=True)
    @patch("analyzer.autopilot_status.launchd_plist_installed", return_value=False)
    @patch("analyzer.autopilot_status.session_target_date", return_value="2026-07-07")
    @patch("analyzer.autopilot_status.prep_session_key", return_value="2026-07-07")
    @patch("analyzer.autopilot_status.prep_status_for", return_value={"options": True, "equity": True})
    @patch("analyzer.autopilot_status.was_morning_options_rescan_sent", return_value=False)
    def test_morning_options_not_done_from_nightly_prep(self, _rescan, _prep, _a, _b, _c, _d):
        from analyzer.autopilot_status import build_autopilot_status

        status = build_autopilot_status()
        morning = next(s for s in status.steps if s.key == "morning_options")
        self.assertFalse(morning.done_today)

    @patch("analyzer.autopilot_status.is_macos", return_value=True)
    @patch("analyzer.autopilot_status.launchd_plist_installed", return_value=False)
    @patch("analyzer.autopilot_status.session_target_date", return_value="2026-07-07")
    @patch("analyzer.autopilot_status.prep_session_key", return_value="2026-07-07")
    def test_build_status(self, _a, _b, _c, _d):
        from analyzer.autopilot_status import build_autopilot_status

        status = build_autopilot_status()
        self.assertEqual(status.trade_date, "2026-07-07")
        self.assertEqual(len(status.steps), 10)
        self.assertEqual(status.schedules_total, 10)
        self.assertEqual(status.schedules_installed, 0)


if __name__ == "__main__":
    unittest.main()
