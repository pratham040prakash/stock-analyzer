"""Tests for enhancement batch — P&L, stale snapshot, journal link."""

import unittest

from analyzer.sideways_options_advisor import (
    MultiLegPnlEstimate,
    StrategyLeg,
    advise_sideways_strategy,
    build_iron_condor,
    estimate_strategy_pnl,
)
from analyzer.trade_journal_link import build_lesson_prefill
from analyzer.intraday_journal import IntradayTradeLog


class TestEnhancementBatch(unittest.TestCase):
    def test_estimate_iron_condor_pnl(self):
        legs = build_iron_condor(
            fno_symbol="NIFTY",
            range_high=24600,
            range_low=24400,
        )
        advice = advise_sideways_strategy(
            fno_symbol="NIFTY",
            ce_strike=24600,
            pe_strike=24400,
            spot=24500,
            or_high=24580,
            or_low=24420,
            iv_rank=78,
            iv_band="expensive",
        )
        advice.legs = legs
        advice.risk_profile = "defined"
        pnl = estimate_strategy_pnl(advice, net_credit_per_unit=12.5)
        self.assertIsInstance(pnl, MultiLegPnlEstimate)
        self.assertEqual(pnl.lot_size, 75)
        self.assertIsNotNone(pnl.max_profit_per_lot_inr)

    def test_build_lesson_prefill(self):
        trade = IntradayTradeLog(
            id="t1",
            trade_date="2026-07-09",
            symbol="RELIANCE",
            action="LONG",
            entry=1400.0,
            stop_loss=1380.0,
            target=1450.0,
            price_at_log=1395.0,
            shares=10,
            notes="Chased entry",
            created_at="2026-07-09 10:15 IST",
        )
        pre = build_lesson_prefill(trade)
        self.assertIn("RELIANCE", pre["symbol"])
        self.assertEqual(pre["entry"], 1400.0)


if __name__ == "__main__":
    unittest.main()
