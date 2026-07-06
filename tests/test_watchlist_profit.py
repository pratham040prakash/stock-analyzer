"""Tests for SHORT profit helper."""

import unittest

from analyzer.watchlist_profit import equity_target_profit_one_share


class TestWatchlistProfit(unittest.TestCase):
    def test_long_profit(self):
        self.assertEqual(equity_target_profit_one_share(100, 110, side="LONG"), 10.0)

    def test_short_profit(self):
        self.assertEqual(equity_target_profit_one_share(100, 90, side="SHORT"), 10.0)

    def test_short_inferred_from_levels(self):
        self.assertEqual(equity_target_profit_one_share(100, 90), 10.0)


if __name__ == "__main__":
    unittest.main()
