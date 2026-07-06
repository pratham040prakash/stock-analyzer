"""Tests for MIS session Telegram reminders."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from analyzer.session_reminders import (
    format_open_reminder,
    format_square_off_reminder,
    run_session_reminders,
)

IST = ZoneInfo("Asia/Kolkata")


class TestSessionReminders(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "state.json"
        self.sp = patch("analyzer.session_reminders.STATE_PATH", self.state)
        self.sp.start()

    def tearDown(self):
        self.sp.stop()
        self.tmp.cleanup()

    def test_format_messages(self):
        self.assertIn("9:15", format_open_reminder())
        self.assertIn("3:20", format_square_off_reminder())
        self.assertIn("options expiry", format_open_reminder().lower())

    def test_early_square_off(self):
        from analyzer.session_reminders import format_early_square_off_reminder

        self.assertIn("3:15", format_early_square_off_reminder())

    @patch("analyzer.telegram_notify.send_telegram_broadcast")
    @patch("analyzer.telegram_notify.telegram_configured", return_value=True)
    def test_force_open(self, _cfg, broadcast):
        broadcast.return_value = (True, "")
        count, status = run_session_reminders(force="open")
        self.assertEqual(count, 1)
        self.assertIn("Sent", status)
        broadcast.assert_called_once()


if __name__ == "__main__":
    unittest.main()
