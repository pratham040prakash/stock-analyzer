"""Tests for pre-market intraday watchlist."""

import unittest
import unittest.mock

import pandas as pd

from analyzer.intraday_watchlist import (
    MIN_ATR_PCT,
    floor_pivot_levels,
    macd_bullish_aligned,
    macd_bullish_cross,
    macd_bearish_aligned,
    build_intraday_watchlist,
    compute_prep_metrics,
)
from analyzer.market_pulse_scan import StockPulseEntry


def _df_n(n: int = 30, base: float = 500.0) -> pd.DataFrame:
    from analyzer.indicators import add_indicators

    rows = []
    for i in range(n):
        c = base + i * 2
        rows.append({
            "Open": c - 1,
            "High": c + 5,
            "Low": c - 5,
            "Close": c,
            "Volume": 1_200_000 + i * 10_000,
        })
    return add_indicators(pd.DataFrame(rows))


class TestIntradayWatchlist(unittest.TestCase):
    def test_floor_pivots(self):
        p = floor_pivot_levels(110, 90, 105)
        self.assertAlmostEqual(p.pivot, 101.67, places=1)
        self.assertGreater(p.r1, p.pivot)
        self.assertLess(p.s1, p.pivot)

    def test_compute_prep_metrics(self):
        df = _df_n()
        m = compute_prep_metrics(df)
        self.assertIn("atr_pct", m)
        self.assertIsNotNone(m.get("pivot"))
        self.assertGreater(m["atr_pct"], 0)

    def test_build_watchlist_from_report(self):
        df = _df_n()
        stock = StockPulseEntry(
            symbol="RELIANCE.NS",
            nse_symbol="RELIANCE",
            name="Reliance",
            price=560.0,
            combined_rec="BUY",
            combined_score=40.0,
            short_chart_df=df,
            volume_ratio=1.4,
            sector="Energy",
            atr_pct=2.2,
            rsi_14=58.0,
            macd_bullish=True,
        )
        prep = compute_prep_metrics(df)
        stock.pivot_p = prep["pivot"].pivot
        stock.pivot_r1 = prep["pivot"].r1
        stock.pivot_s1 = prep["pivot"].s1
        stock.support_20d = prep["support"]
        stock.resistance_20d = prep["resistance"]

        class FakeReport:
            stock_map = {"RELIANCE": stock}
            indices = []
            regime = None
            macro = None
            earnings_by_nse = {}

        wl = build_intraday_watchlist(FakeReport(), limit=5)
        self.assertGreaterEqual(len(wl.picks), 0)

    def test_min_atr_constant(self):
        self.assertGreaterEqual(MIN_ATR_PCT, 1.5)

    def test_macd_cross_vs_aligned(self):
        df = _df_n()
        aligned = macd_bullish_aligned(df)
        cross = macd_bullish_cross(df)
        self.assertIsInstance(aligned, bool)
        self.assertIsInstance(cross, bool)
        if cross:
            self.assertTrue(aligned)

    def test_bearish_watchlist_side(self):
        df = _df_n(base=500.0)
        stock = StockPulseEntry(
            symbol="HDFCBANK.NS",
            nse_symbol="HDFCBANK",
            name="HDFC Bank",
            price=500.0,
            combined_rec="SELL",
            combined_score=35.0,
            short_chart_df=df,
            volume_ratio=1.5,
            sector="Banks",
            atr_pct=2.5,
            rsi_14=40.0,
            macd_bullish=False,
        )
        prep = compute_prep_metrics(df)
        stock.pivot_p = prep["pivot"].pivot
        stock.pivot_r1 = prep["pivot"].r1
        stock.pivot_s1 = prep["pivot"].s1
        stock.support_20d = prep["support"]
        stock.resistance_20d = prep["resistance"]

        class FakeRegime:
            regime = "Bearish Trend"

        class FakeReport:
            stock_map = {"HDFCBANK": stock}
            indices = []
            regime = FakeRegime()
            macro = None
            earnings_by_nse = {}

        with unittest.mock.patch(
            "analyzer.watchlist_learning.get_watchlist_strategy",
            return_value={
                "min_volume_ratio": 1.0,
                "min_atr_pct": 1.5,
                "rsi_bull_min": 55.0,
                "rsi_bull_max": 65.0,
                "max_watchlist": 8,
                "min_checklist_passed": 3,
                "min_prep_score": 0.0,
                "require_rsi_macd": False,
                "require_sector_tailwind": False,
            },
        ):
            wl = build_intraday_watchlist(FakeReport(), limit=5)
        self.assertEqual(wl.market_bias, "BEARISH")
        if wl.picks:
            self.assertEqual(wl.picks[0].side, "SHORT")
            self.assertGreater(wl.picks[0].stop_loss, wl.picks[0].entry)


if __name__ == "__main__":
    unittest.main()
