"""Tests for Investopedia-style intraday stock screening."""

import unittest

import pandas as pd

from analyzer.intraday_stock_picker import (
    IDEAL_RANGE_MAX_PCT,
    MIN_AVG_DAILY_VOLUME,
    combined_intraday_rank,
    score_correlation,
    score_liquidity,
    score_volatility,
    screen_intraday_stock,
)


def _ohlcv(closes: list[float], volumes: list[int] | None = None) -> pd.DataFrame:
    vols = volumes or [1_000_000] * len(closes)
    return pd.DataFrame({
        "Open": closes,
        "High": [c * 1.02 for c in closes],
        "Low": [c * 0.98 for c in closes],
        "Close": closes,
        "Volume": vols,
    })


class TestIntradayStockPicker(unittest.TestCase):
    def test_liquidity_high_volume(self):
        score, ok, notes = score_liquidity(2_500_000, 1.8)
        self.assertTrue(ok)
        self.assertGreaterEqual(score, 32)
        self.assertTrue(any("Liquid" in n or "Very liquid" in n for n in notes))

    def test_liquidity_fails_low_volume(self):
        score, ok, _ = score_liquidity(50_000, 1.0)
        self.assertFalse(ok)
        self.assertLess(score, 10)

    def test_volatility_sweet_spot(self):
        score, ok, notes = score_volatility(3.5, None)
        self.assertTrue(ok)
        self.assertEqual(score, 30.0)
        self.assertTrue(any("Ideal" in n for n in notes))

    def test_volatility_too_high(self):
        score, ok, _ = score_volatility(10.0, None)
        self.assertFalse(ok)
        self.assertLess(score, 10)

    def test_correlation_aligned_with_nifty(self):
        score, notes = score_correlation(0.65, "BULLISH", "BUY")
        self.assertEqual(score, 20.0)
        self.assertTrue(any("aligned" in n.lower() for n in notes))

    def test_screen_intraday_stock(self):
        daily = _ohlcv([100 + i * 0.5 for i in range(30)], [800_000] * 30)
        nifty = _ohlcv([20000 + i * 10 for i in range(30)])
        result = screen_intraday_stock(
            nse_symbol="RELIANCE",
            daily_df=daily,
            intraday_df=None,
            relative_volume=1.6,
            nifty_df=nifty,
            trade_action="BUY",
            nifty_bias="BULLISH",
        )
        self.assertGreater(result.composite_score, 40)
        self.assertTrue(result.passed_liquidity)
        self.assertTrue(result.passed_volatility)

    def test_combined_rank(self):
        self.assertGreater(combined_intraday_rank(50, 80), combined_intraday_rank(50, 40))

    def test_constants(self):
        self.assertGreaterEqual(MIN_AVG_DAILY_VOLUME, 500_000)
        self.assertGreater(IDEAL_RANGE_MAX_PCT, 2.0)


if __name__ == "__main__":
    unittest.main()
