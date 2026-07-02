"""Tests for affordable index option picks."""

import unittest

from analyzer.affordable_invest import (
    _recommended_index_side,
    INDEX_AFFORDABLE_TARGETS,
)
from analyzer.nse_options import (
    DEFAULT_INDEX_LOT_SIZES,
    NSEOptionChain,
    NSEOptionLeg,
    format_leg_with_lot_cost,
    get_fno_lot_size,
    option_lot_buy_cost,
    pick_affordable_strikes,
)


def _leg(opt: str, strike: float, ltp: float, oi: int = 5000, vol: int = 800) -> NSEOptionLeg:
    return NSEOptionLeg(
        option_type=opt,
        strike=strike,
        expiry="2026-04-24",
        ltp=ltp,
        bid=ltp * 0.99,
        ask=ltp * 1.01,
        open_interest=oi,
        oi_change=100,
        volume=vol,
        iv=18.0,
    )


class TestAffordableIndexOptions(unittest.TestCase):
    def test_index_targets(self):
        symbols = [t[0] for t in INDEX_AFFORDABLE_TARGETS]
        self.assertIn("NIFTY", symbols)
        self.assertIn("BANKNIFTY", symbols)

    def test_pick_affordable_strikes(self):
        chain = NSEOptionChain(
            symbol="NIFTY",
            instrument_type="index",
            spot=24000.0,
            expiry="2026-04-24",
            legs=[
                _leg("CE", 24000, 2500),
                _leg("CE", 24200, 4500),
                _leg("PE", 23900, 1800),
                _leg("PE", 23800, 3200),
            ],
        )
        ce, pe = pick_affordable_strikes(chain, max_premium=3000)
        self.assertIsNotNone(ce)
        self.assertIsNotNone(pe)
        assert ce is not None and pe is not None
        self.assertLessEqual(ce.ltp or 0, 3000)
        self.assertLessEqual(pe.ltp or 0, 3000)
        self.assertEqual(ce.strike, 24000)
        self.assertEqual(pe.strike, 23900)

    def test_recommended_side_ce(self):
        ce = _leg("CE", 24100, 1200)
        pe = _leg("PE", 23900, 900)
        text, total = _recommended_index_side("BUY CE", ce, pe, 3000, lot_size=75)
        self.assertIn("Pick CE", text)
        self.assertIn("1,200", text)
        self.assertIn("1 lot cost", text)
        self.assertEqual(total, 1200 * 75)

    def test_option_lot_buy_cost(self):
        self.assertEqual(option_lot_buy_cost(100.0, 75), 7500.0)
        self.assertEqual(option_lot_buy_cost(50.0, 30), 1500.0)
        self.assertIsNone(option_lot_buy_cost(None, 75))

    def test_format_leg_with_lot_cost(self):
        leg = _leg("CE", 24000, 100.0)
        text = format_leg_with_lot_cost(leg, 24000.0, 75)
        self.assertIn("1 lot (75 qty)", text)
        self.assertIn("7,500", text)

    def test_default_lot_sizes(self):
        self.assertEqual(DEFAULT_INDEX_LOT_SIZES["NIFTY"], 75)
        self.assertEqual(DEFAULT_INDEX_LOT_SIZES["BANKNIFTY"], 30)
        # Fallback when NSE unavailable in tests
        self.assertEqual(get_fno_lot_size("NIFTY"), 75)
        self.assertEqual(get_fno_lot_size("BANKNIFTY"), 30)


if __name__ == "__main__":
    unittest.main()
