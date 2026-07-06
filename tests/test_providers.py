"""Tests for data provider routing."""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from analyzer.providers.router import data_source_status, fetch_intraday_bars
from analyzer.providers.types import IntradayMeta


class TestDataProviders(unittest.TestCase):
    def test_data_source_status_without_kite(self):
        with patch("analyzer.providers.router.is_kite_configured", return_value=False):
            status = data_source_status()
        self.assertFalse(status["kite_configured"])
        self.assertEqual(status["primary_intraday"], "Yahoo Finance")

    def test_fetch_intraday_prefers_kite(self):
        idx = pd.date_range("2026-01-02 09:15", periods=5, freq="5min", tz="Asia/Kolkata")
        df = pd.DataFrame(
            {"Open": 100, "High": 101, "Low": 99, "Close": 100.5, "Volume": 1000},
            index=idx,
        )
        meta = IntradayMeta(
            symbol="RELIANCE.NS",
            interval="5m",
            session_date="2026-01-02",
            bars=5,
            source="Kite",
            market={},
        )
        with patch("analyzer.providers.router.is_kite_live", return_value=True):
            with patch("analyzer.providers.router.fetch_kite_intraday", return_value=(df, meta)):
                out_df, out_meta = fetch_intraday_bars("RELIANCE", "5m", "india")
        self.assertEqual(out_meta.source, "Kite")
        self.assertEqual(len(out_df), 5)


if __name__ == "__main__":
    unittest.main()
