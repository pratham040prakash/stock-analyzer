"""Tests for affordable invest picks under price cap."""

import unittest

from analyzer.affordable_invest import (
    AffordableInvestPick,
    affordable_from_pulse_report,
    rank_affordable_investments,
)
from analyzer.chart_horizon import HorizonAnalysis
from analyzer.market_pulse_scan import MarketPulseReport, StockPulseEntry


def _stock(
    nse: str,
    price: float,
    combined: float = 25.0,
    long_score: float = 30.0,
    short_score: float = 20.0,
    combined_rec: str = "BUY",
    long_action: str = "ACCUMULATE",
    short_action: str = "BUY",
    ltp_source: str = "Kite",
) -> StockPulseEntry:
    return StockPulseEntry(
        symbol=f"{nse}.NS",
        nse_symbol=nse,
        name=f"{nse} Ltd",
        price=price,
        combined_rec=combined_rec,
        combined_score=combined,
        short_term=HorizonAnalysis(
            horizon="short",
            action=short_action,
            score=short_score,
            timeframe="2–8 weeks",
            entry_hint="Near support",
            stop_hint="5% below",
            target_hint="+10%",
            summary="Swing ok",
        ),
        long_term=HorizonAnalysis(
            horizon="long",
            action=long_action,
            score=long_score,
            timeframe="1–3 years",
            entry_hint="SIP on dips",
            stop_hint="SMA-200",
            target_hint="Trend",
            summary="Quality",
        ),
        ltp_source=ltp_source,
        what_to_do="Multi-timeframe alignment",
    )


class TestAffordableInvest(unittest.TestCase):
    def test_filters_above_price_cap(self):
        stocks = [_stock("TCS", 4100), _stock("SBIN", 850)]
        picks = rank_affordable_investments(stocks, max_price_inr=3000)
        self.assertEqual(len(picks), 1)
        self.assertEqual(picks[0].nse_symbol, "SBIN")

    def test_ranks_by_invest_score(self):
        stocks = [
            _stock("ITC", 450, combined=15, long_score=18),
            _stock("SBIN", 850, combined=35, long_score=40, long_action="CORE BUY"),
        ]
        picks = rank_affordable_investments(stocks, max_price_inr=3000)
        self.assertEqual(picks[0].nse_symbol, "SBIN")

    def test_excludes_sell(self):
        stocks = [_stock("XYZ", 100, combined_rec="SELL", long_action="SELL", long_score=-10)]
        self.assertEqual(rank_affordable_investments(stocks), [])

    def test_from_pulse_report(self):
        report = MarketPulseReport(
            indices=[],
            market_verdict="",
            index_options=[],
            top_stocks=[],
            stock_map={
                "INFY": _stock("INFY", 1800),
                "RELIANCE": _stock("RELIANCE", 2900),
            },
        )
        picks = affordable_from_pulse_report(report, limit=5)
        self.assertEqual(len(picks), 2)
        self.assertIsInstance(picks[0], AffordableInvestPick)


if __name__ == "__main__":
    unittest.main()
