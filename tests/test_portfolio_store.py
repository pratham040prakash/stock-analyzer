"""Tests for portfolio persistence."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from analyzer.portfolio_store import (
    clear_saved_portfolio,
    holding_from_dict,
    holding_to_dict,
    import_from_dict,
    import_to_dict,
    load_saved_portfolio,
    make_manual_holding,
    save_portfolio,
)
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult


class TestPortfolioStore(unittest.TestCase):
    def test_make_manual_holding_nse(self):
        h = make_manual_holding("RELIANCE", 10, 2500.0)
        self.assertIsNotNone(h)
        assert h is not None
        self.assertEqual(h.tradingsymbol, "RELIANCE")
        self.assertEqual(h.yahoo_symbol, "RELIANCE.NS")
        self.assertEqual(h.quantity, 10)
        self.assertEqual(h.average_price, 2500.0)

    def test_make_manual_holding_rejects_empty(self):
        self.assertIsNone(make_manual_holding("", 5, 100.0))
        self.assertIsNone(make_manual_holding("TCS", 0, 100.0))

    def test_roundtrip_save_load(self):
        imp = ZerodhaImportResult(
            source="manual",
            holdings=[
                ZerodhaHolding(
                    kite_symbol="NSE:TCS-EQ",
                    tradingsymbol="TCS",
                    exchange="NSE",
                    quantity=5,
                    average_price=3500.0,
                    yahoo_symbol="TCS.NS",
                )
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("analyzer.portfolio_store.STORE_DIR", Path(tmp)):
                save_portfolio(imp, profile="testuser")
                loaded = load_saved_portfolio(profile="testuser")
                self.assertIsNotNone(loaded)
                assert loaded is not None
                self.assertEqual(len(loaded.holdings), 1)
                self.assertEqual(loaded.holdings[0].tradingsymbol, "TCS")
                self.assertEqual(loaded.holdings[0].quantity, 5)

    def test_holding_dict_roundtrip(self):
        h = make_manual_holding("INFY.NS", 20, None)
        assert h is not None
        d = holding_to_dict(h)
        h2 = holding_from_dict(d)
        self.assertEqual(h2.tradingsymbol, h.tradingsymbol)
        self.assertEqual(h2.quantity, h.quantity)

    def test_import_dict_roundtrip(self):
        imp = ZerodhaImportResult(source="csv", holdings=[make_manual_holding("SBIN", 100, 600.0)])  # type: ignore[list-item]
        d = import_to_dict(imp)
        imp2 = import_from_dict(d)
        self.assertEqual(len(imp2.holdings), 1)
        self.assertEqual(imp2.source, "csv")

    def test_clear_saved_portfolio(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("analyzer.portfolio_store.STORE_DIR", Path(tmp)):
                path = Path(tmp) / "test.json"
                path.write_text("{}", encoding="utf-8")
                with mock.patch("analyzer.portfolio_store.store_path", return_value=path):
                    clear_saved_portfolio(profile="test")
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
