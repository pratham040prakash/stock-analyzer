"""Tests for OR confirmation after 9:45."""

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.opening_range_confirm import confirm_or_long_entry

IST = ZoneInfo("Asia/Kolkata")


class TestOrConfirm(unittest.TestCase):
    def test_observe_before_945(self):
        now = datetime(2026, 7, 3, 9, 30, tzinfo=IST)
        r = confirm_or_long_entry(1015, entry=1010, or_high=1012, or_low=1000, now=now)
        self.assertEqual(r.phase, "observe")
        self.assertFalse(r.allow_entry)

    def test_confirmed_breakout(self):
        now = datetime(2026, 7, 3, 10, 0, tzinfo=IST)
        r = confirm_or_long_entry(1015, entry=1010, or_high=1012, or_low=1000, now=now)
        self.assertEqual(r.phase, "confirmed")
        self.assertTrue(r.allow_entry)

    def test_below_or_low(self):
        now = datetime(2026, 7, 3, 10, 0, tzinfo=IST)
        r = confirm_or_long_entry(995, entry=1010, or_high=1012, or_low=1000, now=now)
        self.assertEqual(r.phase, "invalid")


if __name__ == "__main__":
    unittest.main()
