"""Tests for watchlist Telegram formatting."""

import unittest

from analyzer.options_expiry_watchlist import OptionsExpiryPick
from analyzer.watchlist_pins import PinnedPlan
from analyzer.watchlist_telegram import (
    format_options_watchlist_telegram,
    format_pinned_watchlist_telegram,
)


class TestWatchlistTelegram(unittest.TestCase):
    def test_equity_format(self):
        msg = format_pinned_watchlist_telegram(
            [PinnedPlan("RELIANCE", 2500.0, 2480.0, 2550.0, "2026-07-03")],
            prep_date="2026-07-03",
        )
        self.assertIn("RELIANCE", msg)
        self.assertIn("₹2,500", msg)

    def test_options_format(self):
        pick = OptionsExpiryPick(
            rank=1,
            fno_symbol="NIFTY",
            name="Nifty",
            expiry="10-Jul-2026",
            spot=25000.0,
            signal="BUY CE",
            option_type="CE",
            strike=25050.0,
            premium=120.0,
            lot_size=75,
            lot_cost=9000.0,
            stop_premium=78.0,
            target_premium=180.0,
            iv=12.0,
            recommended=True,
            reason="test",
        )
        msg = format_options_watchlist_telegram([pick], prep_date="2026-07-03")
        self.assertIn("NIFTY", msg)
        self.assertIn("★ CE", msg)
        self.assertIn("₹120.00", msg)


if __name__ == "__main__":
    unittest.main()
