"""Tests for Alpha AI institutional report."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from analyzer.alpha_ai_report import build_alpha_ai_report, _probabilities_from_scores, compare_alpha_reports


class TestAlphaAIReport(unittest.TestCase):
    def test_probabilities_sum(self):
        p = _probabilities_from_scores(25, 20, 15)
        self.assertAlmostEqual(sum(p.values()), 100.0, places=0)

    @patch("analyzer.alpha_ai_report.generate_advice")
    @patch("analyzer.alpha_ai_report.fetch_stock_data")
    def test_build_report_structure(self, mock_fetch, mock_advice):
        dates = pd.date_range("2024-01-01", periods=120, freq="B")
        rng = pd.Series(range(120), index=dates)
        df = pd.DataFrame(
            {
                "Open": 100 + rng * 0.1,
                "High": 101 + rng * 0.1,
                "Low": 99 + rng * 0.1,
                "Close": 100 + rng * 0.1,
                "Volume": 1_000_000,
            },
            index=dates,
        )
        mock_fetch.return_value = (
            df,
            {
                "symbol": "TCS.NS",
                "name": "Tata Consultancy Services",
                "sector": "Technology",
                "industry": "IT Services",
                "nse_symbol": "TCS",
                "longBusinessSummary": "IT services company.",
            },
        )
        mock_advice.return_value = MagicMock(
            final_action="BUY",
            conviction="medium",
            time_horizon="Medium (months)",
            position_hint="3-5% max",
            entry_zone="₹3,800–3,900",
            stop_loss="₹3,700",
            target="₹4,100",
            risk_reward="1:2",
            summary="Quality compounder; wait for dip.",
            risks=["FX headwinds"],
            bullish_factors=[],
            bearish_factors=[],
        )

        with patch("analyzer.alpha_ai_report.add_indicators", side_effect=lambda x: x), patch(
            "analyzer.alpha_ai_report.analyze_combined"
        ) as mock_combined:
            tech = MagicMock(
                composite_score=20,
                recommendation="BUY",
                confidence="medium",
                support=95,
                resistance=110,
                current_price=100,
            )
            fund = MagicMock(composite_score=25, metrics=[])
            mock_combined.return_value = MagicMock(
                technical=tech,
                fundamental=fund,
                combined_score=22,
                combined_recommendation="BUY",
            )
            report = build_alpha_ai_report("TCS", market="india", period="1y")

        self.assertEqual(report.symbol, "TCS.NS")
        self.assertGreater(report.overall_score, 0)
        if report.evidence_packet is not None:
            self.assertGreater(len(report.evidence_packet.items), 0)
        self.assertIn(report.recommendation, ("Strong Buy", "Buy", "Accumulate", "Hold", "Reduce", "Sell", "Avoid"))
        self.assertIn(report.buy_decision, ("YES", "NO", "WAIT"))
        self.assertTrue(report.snapshot)
        self.assertTrue(report.business_overview)
        self.assertTrue(report.final_verdict_detail)


if __name__ == "__main__":
    unittest.main()
