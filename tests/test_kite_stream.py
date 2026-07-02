"""Tests for Kite WebSocket subscription helpers."""

import unittest
from unittest.mock import patch

from analyzer.india import NIFTY_50
from analyzer.kite_stream import (
    nifty50_kite_symbols,
    start_kite_ticker_on_app_start,
    ws_subscription_status,
)


class TestKiteStream(unittest.TestCase):
    def test_nifty50_kite_symbols_count(self):
        symbols = nifty50_kite_symbols()
        self.assertEqual(len(symbols), len(NIFTY_50))
        self.assertTrue(all(s.startswith("NSE:") and s.endswith("-EQ") for s in symbols))
        self.assertIn("NSE:RELIANCE-EQ", symbols)

    def test_start_on_app_start_skips_without_credentials(self):
        with patch("analyzer.kite_stream.load_env_credentials", return_value={"api_key": "", "access_token": ""}):
            self.assertFalse(start_kite_ticker_on_app_start())

    def test_start_on_app_start_nifty50_when_open(self):
        with patch("analyzer.kite_stream.load_env_credentials", return_value={"api_key": "k", "access_token": "t"}):
            with patch(
                "analyzer.kite_stream.market_session_status",
                return_value={"is_open": True},
            ):
                with patch("analyzer.kite_stream.start_kite_ticker_for_nifty50", return_value=True) as mock_n50:
                    self.assertTrue(start_kite_ticker_on_app_start())
        mock_n50.assert_called_once()

    def test_start_on_app_start_index_only_when_closed(self):
        with patch("analyzer.kite_stream.load_env_credentials", return_value={"api_key": "k", "access_token": "t"}):
            with patch(
                "analyzer.kite_stream.market_session_status",
                return_value={"is_open": False},
            ):
                with patch("analyzer.kite_stream.start_kite_ticker_background", return_value=True) as mock_bg:
                    self.assertTrue(start_kite_ticker_on_app_start())
        mock_bg.assert_called_once()

    def test_ws_subscription_status_shape(self):
        status = ws_subscription_status()
        self.assertIn("market_open", status)
        self.assertIn("subscribed_tokens", status)
        self.assertIn("nifty50_mode", status)
        self.assertIn("ws_active", status)


if __name__ == "__main__":
    unittest.main()
