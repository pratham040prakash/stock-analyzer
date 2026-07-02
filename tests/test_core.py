"""Unit tests for stock-analyzer."""

import unittest

import pandas as pd

from analyzer.backtest import ZERODHA_COST_PRESET, run_backtest
from analyzer.india import NIFTY_50, resolve_indian_candidates
from analyzer.indicators import add_indicators
from analyzer.markets import normalize_ticker
from analyzer.risk import suggest_position_size
from analyzer.zerodha import kite_to_yahoo, yahoo_to_kite


class TestZerodhaSymbols(unittest.TestCase):
    def test_kite_to_yahoo_nse(self):
        self.assertEqual(kite_to_yahoo("NSE:RELIANCE-EQ"), "RELIANCE.NS")

    def test_yahoo_to_kite(self):
        self.assertEqual(yahoo_to_kite("TCS.NS"), "NSE:TCS-EQ")


class TestIndianTickers(unittest.TestCase):
    def test_nifty_50_count(self):
        self.assertEqual(len(NIFTY_50), 50)

    def test_resolve_alias(self):
        cands = resolve_indian_candidates("SBIN")
        self.assertTrue(any("SBIN" in c for c in cands))


class TestRisk(unittest.TestCase):
    def test_position_size(self):
        pos = suggest_position_size(500_000, 100.0, 95.0)
        self.assertGreater(pos["shares"], 0)


class TestBacktest(unittest.TestCase):
    def test_run_backtest_minimal(self):
        idx = pd.date_range("2023-01-01", periods=300, freq="B")
        close = pd.Series(range(100, 400), index=idx, dtype=float)
        df = pd.DataFrame({
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": 1_000_000,
        })
        df = add_indicators(df)
        bt = run_backtest(
            df, "TEST",
            commission_pct=ZERODHA_COST_PRESET["commission_pct"],
            slippage_pct=ZERODHA_COST_PRESET["slippage_pct"],
        )
        self.assertIsNotNone(bt.strategy_return_pct)


class TestMarkets(unittest.TestCase):
    def test_normalize_india(self):
        self.assertIn(".NS", normalize_ticker("reliance", "india"))


if __name__ == "__main__":
    unittest.main()
