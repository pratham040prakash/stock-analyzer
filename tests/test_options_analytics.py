"""Tests for IV rank / percentile analytics."""

import unittest

from analyzer.options_analytics import (
    OptionsAnalytics,
    _iv_percentile,
    _iv_rank,
    analytics_from_dict,
    analytics_to_dict,
    classify_iv_band,
    guidance_for_horizon,
    should_warn_options_entry,
)


class TestOptionsAnalytics(unittest.TestCase):
    def test_iv_rank_high(self):
        samples = [12.0, 14.0, 16.0, 18.0, 20.0]
        rank, note = _iv_rank(19.0, samples)
        self.assertIsNotNone(rank)
        self.assertGreater(rank, 60)
        self.assertIn("elevated", note)

    def test_iv_rank_low(self):
        samples = [20.0, 22.0, 24.0, 26.0, 28.0]
        rank, _ = _iv_rank(21.0, samples)
        self.assertLess(rank, 35)

    def test_iv_rank_tight_range(self):
        rank, note = _iv_rank(15.2, [15.0, 15.1, 15.2, 15.3])
        self.assertEqual(rank, 50.0)
        self.assertIn("tight", note)

    def test_iv_percentile(self):
        samples = [10.0, 12.0, 14.0, 16.0, 18.0]
        pct = _iv_percentile(15.0, samples)
        self.assertEqual(pct, 60.0)

    def test_classify_iv_band(self):
        self.assertEqual(classify_iv_band(75.0, 10), "expensive")
        self.assertEqual(classify_iv_band(25.0, 10), "cheap")
        self.assertEqual(classify_iv_band(50.0, 10), "mid")
        self.assertEqual(classify_iv_band(None, 1), "building")

    def test_should_warn_expensive_iv(self):
        snap = OptionsAnalytics(iv_band="expensive", iv_rank=80.0, atm_iv=22.0)
        self.assertTrue(should_warn_options_entry(snap, horizon="options"))

    def test_guidance_expensive_options(self):
        snap = OptionsAnalytics(iv_band="expensive", iv_rank=82.0, atm_iv=24.0)
        text = guidance_for_horizon(snap, "options")
        self.assertIn("expensive", text.lower())

    def test_serialize_roundtrip(self):
        snap = OptionsAnalytics(
            symbol="NIFTY",
            expiry="30-Jul-2026",
            atm_iv=14.5,
            iv_rank=42.0,
            iv_percentile=38.0,
            iv_band="mid",
        )
        restored = analytics_from_dict(analytics_to_dict(snap))
        self.assertEqual(restored.symbol, "NIFTY")
        self.assertEqual(restored.iv_rank, 42.0)


if __name__ == "__main__":
    unittest.main()
