"""Tests for chart-based market risk."""

import unittest

import pandas as pd

from analyzer.indicators import add_indicators
from analyzer.market_risk import _trend_from_chart, assess_market_risk


class TestMarketRisk(unittest.TestCase):
    def _sample_df(self, n: int = 120) -> pd.DataFrame:
        idx = pd.date_range("2024-01-01", periods=n, freq="B")
        close = pd.Series(range(100, 100 + n), index=idx, dtype=float)
        df = pd.DataFrame({
            "Open": close,
            "High": close + 2,
            "Low": close - 2,
            "Close": close,
            "Volume": 1_000_000,
        })
        return add_indicators(df)

    def test_uptrend_detected(self):
        df = self._sample_df()
        trend = _trend_from_chart(df)
        self.assertEqual(trend.direction, "Uptrend")

    def test_risk_assessment_bounds(self):
        df = self._sample_df()
        assessment = assess_market_risk(df, "TEST.NS", name="Test Co")
        self.assertGreaterEqual(assessment.risk_score, 0)
        self.assertLessEqual(assessment.risk_score, 100)
        self.assertIn(assessment.risk_level, ("Low", "Moderate", "High", "Very High"))

    def test_learning_mode_zero_allocation_cap(self):
        df = self._sample_df()
        assessment = assess_market_risk(df, "TEST.NS", goal="learning", experience="new")
        self.assertEqual(assessment.max_suggested_allocation_pct, 0.0)

    def test_expensive_iv_raises_risk_for_trading(self):
        from analyzer.options_analytics import OptionsAnalytics

        df = self._sample_df()
        iv = OptionsAnalytics(atm_iv=25.0, iv_rank=85.0, iv_band="expensive", guidance="IV high")
        base = assess_market_risk(df, "TEST.NS", goal="long_term", experience="new")
        with_iv = assess_market_risk(
            df, "TEST.NS", goal="trading", experience="new", options_analytics=iv
        )
        self.assertGreater(with_iv.risk_score, base.risk_score)


if __name__ == "__main__":
    unittest.main()
