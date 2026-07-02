"""Tests for affordable index option picks."""

import unittest

from analyzer.affordable_invest import (
    _recommended_index_side,
    INDEX_AFFORDABLE_TARGETS,
)
from analyzer.nse_options import NSEOptionChain, NSEOptionLeg, pick_affordable_strikes


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
        text = _recommended_index_side("BUY CE", ce, pe, 3000)
        self.assertIn("Pick CE", text)
        self.assertIn("1,200", text)


if __name__ == "__main__":
    unittest.main()
