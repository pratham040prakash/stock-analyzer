"""Tests for data & intelligence enhancements (items 1–12)."""

from __future__ import annotations

import unittest

from analyzer.alpha_ai_report import _buy_decision, _confidence_pct
from analyzer.asset_class import classify_asset, assert_supported_equity
from analyzer.dcf_model import build_dcf, format_dcf_markdown
from analyzer.etf_analyzer import build_etf_profile
from analyzer.penny_stocks import PENNY_CANDIDATE_SYMBOLS


class TestAssetClass(unittest.TestCase):
    def test_blocks_crypto(self):
        ac = classify_asset("BTC-USD", {"quoteType": "CRYPTOCURRENCY"})
        self.assertFalse(ac.supported)
        with self.assertRaises(ValueError):
            assert_supported_equity("BTC-USD", {"quoteType": "CRYPTOCURRENCY"})

    def test_blocks_forex(self):
        ac = classify_asset("INR=X", {"quoteType": "CURRENCY"})
        self.assertEqual(ac.asset_class, "forex")
        self.assertFalse(ac.supported)

    def test_etf_supported(self):
        ac = classify_asset("NIFTYBEES.NS", {"quoteType": "ETF", "longName": "Nifty Bees"})
        self.assertEqual(ac.asset_class, "etf")
        self.assertTrue(ac.supported)

    def test_equity_supported(self):
        ac = classify_asset("TCS.NS", {"quoteType": "EQUITY"})
        self.assertTrue(ac.supported)


class TestBuyDecisionAndConfidence(unittest.TestCase):
    def test_strong_buy_yes_on_high_conviction(self):
        decision, _ = _buy_decision("STRONG BUY", 15, 10, "high")
        self.assertEqual(decision, "YES")

    def test_confidence_penalized_by_gaps(self):
        low = _confidence_pct(20, ["a", "b", "c", "d"], "medium")
        high = _confidence_pct(20, [], "medium")
        self.assertLess(low, high)


class TestDCF(unittest.TestCase):
    def test_dcf_fair_value(self):
        dcf = build_dcf(
            "TEST.NS",
            free_cashflow=1_000_000_000,
            shares_outstanding=100_000_000,
            earnings_growth=0.10,
            current_price=80,
        )
        self.assertIsNotNone(dcf.fair_value)
        md = format_dcf_markdown(dcf)
        self.assertIn("DCF fair value", md)
        self.assertTrue(len(dcf.sensitivity) >= 9)


class TestETF(unittest.TestCase):
    def test_etf_profile(self):
        p = build_etf_profile(
            "NIFTYBEES.NS",
            {"quoteType": "ETF", "longName": "Nippon India ETF Nifty 50 BeES", "annualReportExpenseRatio": 0.05},
        )
        self.assertIsNotNone(p)
        self.assertTrue(p.is_etf)


class TestPennyUniverse(unittest.TestCase):
    def test_delisted_removed(self):
        for bad in ("DHANI", "RELCAPITAL", "JPASSOCIAT", "HLVLTD", "GAYAPROJ"):
            self.assertNotIn(bad, PENNY_CANDIDATE_SYMBOLS)


if __name__ == "__main__":
    unittest.main()
