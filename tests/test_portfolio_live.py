"""Tests for live portfolio + Kite watchlist store."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.kite_watchlist_store import (
    load_kite_watchlist,
    merge_kite_watchlist,
    parse_watchlist_text,
    save_kite_watchlist,
)
from analyzer.portfolio_live import (
    merge_holdings_and_watchlist,
    refresh_holdings_ltp,
    sync_watchlist_from_kite_activity,
)
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult


class TestKiteWatchlistStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.p = patch("analyzer.kite_watchlist_store.STORE_DIR", self.dir)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()

    def test_parse_and_save(self):
        syms = parse_watchlist_text("NSE:TCS-EQ, RELIANCE\nSBIN")
        self.assertIn("NSE:TCS-EQ", syms)
        save_kite_watchlist(syms, profile="me")
        loaded = load_kite_watchlist(profile="me")
        self.assertEqual(len(loaded), 3)

    def test_merge_watchlist(self):
        save_kite_watchlist(["NSE:TCS-EQ"], profile="me")
        added, total = merge_kite_watchlist(["NSE:INFY-EQ", "NSE:TCS-EQ"], profile="me")
        self.assertEqual(added, 1)
        self.assertEqual(total, 2)


class TestPortfolioLive(unittest.TestCase):
    def test_refresh_holdings_ltp(self):
        imp = ZerodhaImportResult(
            holdings=[
                ZerodhaHolding(
                    kite_symbol="NSE:TCS-EQ",
                    tradingsymbol="TCS",
                    exchange="NSE",
                    quantity=5,
                    average_price=3500,
                    yahoo_symbol="TCS.NS",
                )
            ],
            source="manual",
        )
        with patch(
            "analyzer.portfolio_live.get_kite_ltp_cached",
            return_value={"NSE:TCS-EQ": 3600.0},
        ):
            out = refresh_holdings_ltp(imp)
        self.assertEqual(out.holdings[0].last_price, 3600.0)
        self.assertEqual(out.holdings[0].pnl, 500.0)

    def test_merge_holdings_and_watchlist(self):
        imp = ZerodhaImportResult(
            holdings=[
                ZerodhaHolding(
                    kite_symbol="NSE:TCS-EQ",
                    tradingsymbol="TCS",
                    exchange="NSE",
                    quantity=2,
                    yahoo_symbol="TCS.NS",
                )
            ],
            source="manual",
        )
        with patch(
            "analyzer.portfolio_live.load_kite_watchlist",
            return_value=["NSE:INFY-EQ", "NSE:TCS-EQ"],
        ):
            merged = merge_holdings_and_watchlist(imp, profile="x")
        self.assertEqual(len(merged.holdings), 2)
        self.assertEqual(merged.holdings[1].tradingsymbol, "INFY")
        self.assertEqual(merged.holdings[1].quantity, 0)

    def test_sync_watchlist_from_kite_activity(self):
        holdings = ZerodhaImportResult(
            holdings=[
                ZerodhaHolding(
                    kite_symbol="NSE:TCS-EQ",
                    tradingsymbol="TCS",
                    exchange="NSE",
                    quantity=2,
                    yahoo_symbol="TCS.NS",
                )
            ],
            source="kite",
        )
        tmp = tempfile.TemporaryDirectory()
        with patch("analyzer.kite_watchlist_store.STORE_DIR", Path(tmp.name)):
            with patch(
                "analyzer.portfolio_live.fetch_kite_activity_symbols",
                return_value=(["NSE:INFY-EQ", "NSE:TCS-EQ"], []),
            ):
                added, total, errs = sync_watchlist_from_kite_activity(
                    profile="sync",
                    holdings=holdings,
                )
        self.assertEqual(added, 1)
        self.assertEqual(total, 1)
        self.assertEqual(errs, [])
        tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
