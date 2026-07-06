"""Tests for options premium chart."""

import unittest

import pandas as pd

from analyzer.options_premium_chart import ladder_for_pick, options_premium_chart
from analyzer.options_expiry_watchlist import OptionsExpiryPick
from analyzer.trade_ladder import build_options_ladder


class TestOptionsPremiumChart(unittest.TestCase):
    def test_premium_chart_with_ladder(self):
        idx = pd.date_range("2026-07-06 09:15", periods=8, freq="5min")
        df = pd.DataFrame(
            {
                "Open": [100.0 + i for i in range(8)],
                "High": [101.0 + i for i in range(8)],
                "Low": [99.0 + i for i in range(8)],
                "Close": [100.5 + i for i in range(8)],
                "Volume": [500] * 8,
            },
            index=idx,
        )
        ladder = build_options_ladder(100.0)
        fig = options_premium_chart(df, ladder, title="NIFTY CE")
        self.assertGreater(len(fig.layout.shapes or []), 0)

    def test_ladder_for_pick(self):
        pick = OptionsExpiryPick(
            rank=1,
            fno_symbol="NIFTY",
            name="Nifty 50",
            expiry="10-Jul-2026",
            spot=24500,
            signal="BUY CE",
            option_type="CE",
            strike=24500,
            premium=120.0,
            lot_size=75,
            lot_cost=9000,
            stop_premium=78.0,
            target_premium=180.0,
            iv=12.0,
            recommended=True,
            reason="test",
            target2_premium=240.0,
            target3_premium=300.0,
            stop_after_t1=120.0,
            stop_after_t2=180.0,
            stop_after_t3=240.0,
        )
        ladder = ladder_for_pick(pick)
        self.assertEqual(ladder.target, 180.0)
        self.assertEqual(ladder.target2, 240.0)


if __name__ == "__main__":
    unittest.main()
