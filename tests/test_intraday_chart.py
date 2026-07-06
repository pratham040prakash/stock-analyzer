"""Tests for intraday chart plan overlays."""

import unittest

import pandas as pd

from analyzer.intraday_chart import intraday_chart
from analyzer.intraday_signals import IntradayAnalysis
from analyzer.trade_ladder import build_equity_ladder


class TestIntradayPlanChart(unittest.TestCase):
    def test_chart_with_ladder_has_layout(self):
        idx = pd.date_range("2026-07-06 09:15", periods=10, freq="5min")
        df = pd.DataFrame(
            {
                "Open": [100.0 + i for i in range(10)],
                "High": [101.0 + i for i in range(10)],
                "Low": [99.0 + i for i in range(10)],
                "Close": [100.5 + i for i in range(10)],
                "Volume": [1000] * 10,
                "VWAP": [100.0 + i for i in range(10)],
                "EMA_9": [100.0 + i for i in range(10)],
                "EMA_21": [100.0 + i for i in range(10)],
            },
            index=idx,
        )
        analysis = IntradayAnalysis(
            ticker="RELIANCE.NS",
            interval="5m",
            last_price=109.5,
            vwap=105.0,
            opening_range_high=102.0,
            opening_range_low=99.5,
            rsi=55.0,
            session_bias="BULLISH",
            trade_setup="BUY",
            entry=105.0,
            stop_loss=103.0,
            target=108.0,
        )
        ladder = build_equity_ladder("LONG", 105.0, 103.0, 108.0)
        fig = intraday_chart(df, analysis, ladder=ladder)
        self.assertGreater(len(fig.layout.shapes or []), 0)


if __name__ == "__main__":
    unittest.main()
