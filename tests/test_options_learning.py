"""Tests for options learning and NSE option history parsing."""

import unittest

from analyzer.nse_option_history import _extract_rows, _rows_to_ohlc
from analyzer.options_watchlist_learning import (
    DEFAULT_OPTIONS_STRATEGY,
    get_options_premium_strategy,
)


class TestOptionsLearning(unittest.TestCase):
    def test_defaults(self):
        strat = get_options_premium_strategy()
        self.assertEqual(strat["stop_mult"], DEFAULT_OPTIONS_STRATEGY["stop_mult"])


class TestNseOptionHistory(unittest.TestCase):
    def test_rows_to_ohlc(self):
        rows = [
            {
                "CH_TRADE_HIGH_PRICE": "120.5",
                "CH_TRADE_LOW_PRICE": "80.0",
                "CH_CLOSING_PRICE": "110.0",
            }
        ]
        ohlc = _rows_to_ohlc(rows)
        self.assertEqual(ohlc, (120.5, 80.0, 110.0))

    def test_extract_data_key(self):
        payload = {"data": [{"CH_CLOSING_PRICE": "50"}]}
        self.assertEqual(len(_extract_rows(payload)), 1)


if __name__ == "__main__":
    unittest.main()
