"""Tests for expected profit helpers."""

import unittest

from analyzer.watchlist_profit import (
    equity_target_profit_one_share,
    format_expected_profit,
    options_target_profit_one_lot,
)


class TestWatchlistProfit(unittest.TestCase):
    def test_equity_one_share(self):
        self.assertEqual(equity_target_profit_one_share(100, 110), 10.0)
        self.assertIsNone(equity_target_profit_one_share(100, 95))

    def test_options_one_lot(self):
        self.assertEqual(options_target_profit_one_lot(75, 112.5, 75), 2812.5)
        self.assertIsNone(options_target_profit_one_lot(75, 70, 75))

    def test_format(self):
        self.assertEqual(format_expected_profit(1234.5), "₹1,234.50")
        self.assertEqual(format_expected_profit(None), "—")


if __name__ == "__main__":
    unittest.main()
