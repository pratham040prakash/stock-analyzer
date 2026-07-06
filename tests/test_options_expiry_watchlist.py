"""Tests for options expiry watchlist."""

import unittest
from unittest.mock import MagicMock, patch

from analyzer.options_expiry_watchlist import (
    OptionsExpiryPick,
    _premium_plan,
    _recommended_side,
    build_options_expiry_watchlist,
)


class TestOptionsExpiryWatchlist(unittest.TestCase):
    def test_premium_plan(self):
        stop, target, ladder = _premium_plan(100.0)
        self.assertEqual(stop, 65.0)
        self.assertEqual(target, 150.0)
        self.assertEqual(ladder.target2, 200.0)
        self.assertEqual(ladder.target3, 250.0)
        self.assertIsNone(_premium_plan(None)[0])

    def test_recommended_side(self):
        self.assertEqual(_recommended_side("BUY CE"), "CE")
        self.assertEqual(_recommended_side("STRONG PE"), "PE")
        self.assertIsNone(_recommended_side("NO TRADE"))

    @patch("analyzer.nse_session.is_nse_available", return_value=False)
    def test_nse_unavailable(self, _mock):
        wl = build_options_expiry_watchlist()
        self.assertFalse(wl.nse_available)
        self.assertEqual(wl.picks, [])

    @patch("analyzer.options_expiry_watchlist._scan_one_index")
    @patch("analyzer.nse_session.is_nse_available", return_value=True)
    def test_build_with_ce_pe_rows(self, _nse, mock_scan):
        ce = OptionsExpiryPick(
            rank=0,
            fno_symbol="NIFTY",
            name="Nifty 50",
            expiry="07-Jul-2026",
            spot=25000.0,
            signal="BUY CE",
            option_type="CE",
            strike=25050.0,
            premium=120.0,
            lot_size=75,
            lot_cost=9000.0,
            stop_premium=78.0,
            target_premium=180.0,
            iv=12.5,
            recommended=True,
            reason="ce",
        )
        pe = OptionsExpiryPick(
            rank=0,
            fno_symbol="NIFTY",
            name="Nifty 50",
            expiry="07-Jul-2026",
            spot=25000.0,
            signal="BUY CE",
            option_type="PE",
            strike=24950.0,
            premium=95.0,
            lot_size=75,
            lot_cost=7125.0,
            stop_premium=61.75,
            target_premium=142.5,
            iv=11.0,
            recommended=False,
            reason="pe",
        )
        mock_scan.return_value = ([ce, pe], MagicMock(), None)
        wl = build_options_expiry_watchlist(max_lot_cost=10000)
        self.assertEqual(len(wl.picks), 4)  # 2 indices × CE+PE
        types = {p.option_type for p in wl.picks}
        self.assertEqual(types, {"CE", "PE"})
        self.assertEqual(mock_scan.call_count, 2)


if __name__ == "__main__":
    unittest.main()
