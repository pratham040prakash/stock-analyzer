"""Tests for intraday trade level computation."""

import unittest

from analyzer.intraday_signals import IntradayAnalysis, compute_trade_levels


class TestTradeLevels(unittest.TestCase):
    def test_sell_levels_when_verdict_sell_but_setup_wait(self):
        intraday = IntradayAnalysis(
            ticker="RELIANCE",
            interval="1m",
            last_price=1000.0,
            vwap=1005.0,
            opening_range_high=1010.0,
            opening_range_low=990.0,
            rsi=45.0,
            session_bias="NEUTRAL",
            trade_setup="WAIT",
            entry=None,
            stop_loss=None,
            target=None,
        )
        entry, stop, target = compute_trade_levels(intraday, "SELL")
        self.assertIsNotNone(entry)
        self.assertIsNotNone(stop)
        self.assertIsNotNone(target)
        self.assertGreater(stop, entry)
        self.assertLess(target, entry)


if __name__ == "__main__":
    unittest.main()
