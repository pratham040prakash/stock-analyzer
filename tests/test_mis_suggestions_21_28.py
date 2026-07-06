"""Tests for MIS/Suggestions items 21–28."""

from __future__ import annotations

import unittest

from analyzer.confidence_calibration import build_confidence_calibration
from analyzer.whatsapp_export import whatsapp_share_url
from analyzer.watchlist_history import DEFAULT_KEEP_DAYS, init_watchlist_history


class TestMisSuggestions2128(unittest.TestCase):
    def test_retention_180_days(self):
        self.assertEqual(DEFAULT_KEEP_DAYS, 180)

    def test_confidence_calibration_empty(self):
        init_watchlist_history()
        buckets = build_confidence_calibration(days=30)
        self.assertEqual(len(buckets), 5)

    def test_whatsapp_url_encodes(self):
        url = whatsapp_share_url("TCS entry 3500")
        self.assertIn("wa.me", url)
        self.assertIn("text=", url)


if __name__ == "__main__":
    unittest.main()
