"""Tests for Kite holdings + same-day CNC position merge."""

import unittest
from unittest.mock import MagicMock, patch

from analyzer.zerodha import (
    ZerodhaImportResult,
    _holding_from_cnc_position,
    _holding_from_kite_holdings_row,
    fetch_holdings_from_kite,
)


class TestZerodhaHoldings(unittest.TestCase):
    def test_holding_from_cnc_position(self):
        row = {
            "tradingsymbol": "JIOFIN",
            "exchange": "NSE",
            "product": "CNC",
            "quantity": 1,
            "average_price": 235.45,
            "last_price": 236.1,
            "pnl": 0.65,
        }
        h = _holding_from_cnc_position(row)
        self.assertIsNotNone(h)
        assert h is not None
        self.assertEqual(h.kite_symbol, "NSE:JIOFIN")
        self.assertEqual(h.quantity, 1.0)
        self.assertEqual(h.average_price, 235.45)

    def test_holding_from_cnc_position_skips_mis(self):
        row = {"tradingsymbol": "RELIANCE", "exchange": "NSE", "product": "MIS", "quantity": 10}
        self.assertIsNone(_holding_from_cnc_position(row))

    def test_holding_from_kite_holdings_row_includes_t1(self):
        row = {
            "tradingsymbol": "TCS-EQ",
            "exchange": "NSE",
            "quantity": 0,
            "t1_quantity": 2,
            "average_price": 3500,
            "last_price": 3600,
            "pnl": 200,
        }
        h = _holding_from_kite_holdings_row(row)
        self.assertIsNotNone(h)
        assert h is not None
        self.assertEqual(h.quantity, 2.0)

    def test_fetch_merges_same_day_cnc_when_holdings_empty(self):
        kite = MagicMock()
        kite.holdings.return_value = []
        kite.positions.return_value = {
            "net": [
                {
                    "tradingsymbol": "JIOFIN",
                    "exchange": "NSE",
                    "product": "CNC",
                    "quantity": 1,
                    "average_price": 235.45,
                    "last_price": 236.1,
                    "pnl": 0.65,
                }
            ],
            "day": [],
        }

        with patch("kiteconnect.KiteConnect", return_value=kite):
            with patch("analyzer.zerodha.load_env_credentials", return_value={
                "api_key": "k",
                "api_secret": "s",
                "access_token": "t",
            }):
                result = fetch_holdings_from_kite("k", "t")

        self.assertEqual(len(result.holdings), 1)
        self.assertEqual(result.holdings[0].tradingsymbol, "JIOFIN")
        self.assertTrue(any("same-day CNC" in n for n in result.notes))


if __name__ == "__main__":
    unittest.main()
