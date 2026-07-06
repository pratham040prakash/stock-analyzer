"""Tests for delivery quality classification."""

import unittest

from analyzer.delivery_quality import (
    DeliverySnapshot,
    _classify_quality,
    _parse_delivery_csv,
    should_downgrade_for_delivery,
)


class TestDeliveryQuality(unittest.TestCase):
    def test_strong_delivery(self):
        q, sig, _, flags = _classify_quality(62.0, 1.1, 0.5, 50.0)
        self.assertEqual(q, "strong")
        self.assertEqual(sig, "bullish")
        self.assertTrue(flags)

    def test_speculative_high_volume(self):
        q, sig, _, _ = _classify_quality(18.0, 2.5, 2.0, None)
        self.assertEqual(q, "speculative")
        self.assertEqual(sig, "bearish")

    def test_skip_swing_on_speculative(self):
        snap = DeliverySnapshot(
            nse_symbol="X",
            delivery_pct=15.0,
            delivery_quantity=100,
            quantity_traded=1000,
            quality="speculative",
        )
        self.assertTrue(
            should_downgrade_for_delivery(snap, "short", filter_weak_delivery=True)
        )

    def test_parse_delivery_csv(self):
        sample = (
            '"Symbol  ","Series  ","Date  ","% Dly Qt to Traded Qty  "\n'
            '"RELIANCE","EQ","03-Jul-2026","66.10"\n'
        )
        rows = _parse_delivery_csv(sample)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["DELIV_PER"], 66.1)


if __name__ == "__main__":
    unittest.main()
