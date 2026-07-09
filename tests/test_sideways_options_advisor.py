"""Tests for sideways options strategy advisor."""

import unittest
from unittest.mock import patch

from analyzer.sideways_options_advisor import (
    advise_sideways_strategy,
    build_iron_condor,
    build_iron_butterfly,
    build_short_strangle,
)


class TestSidewaysOptionsAdvisor(unittest.TestCase):
    def test_iron_condor_legs_four(self):
        legs = build_iron_condor(
            fno_symbol="NIFTY",
            range_high=24550,
            range_low=24400,
        )
        self.assertEqual(len(legs), 4)
        sells = [l for l in legs if l.action == "sell"]
        self.assertEqual(len(sells), 2)

    def test_iron_butterfly_atm(self):
        legs = build_iron_butterfly(fno_symbol="NIFTY", spot=24520)
        strikes = {l.strike for l in legs if l.action == "sell"}
        self.assertEqual(len(strikes), 1)

    def test_single_ce_sideways_suggests_bear_call_spread(self):
        advice = advise_sideways_strategy(
            fno_symbol="BANKNIFTY",
            option_type="CE",
            strike=57500,
            spot=57200,
            or_high=57300,
            or_low=56800,
            iv_rank=75,
            iv_band="expensive",
        )
        self.assertEqual(advice.strategy_id, "bear_call_spread")
        self.assertTrue(advice.blocks_directional)

    def test_single_pe_sideways_suggests_bull_put_spread(self):
        advice = advise_sideways_strategy(
            fno_symbol="NIFTY",
            option_type="PE",
            strike=24400,
            spot=24500,
            or_high=24550,
            or_low=24400,
            iv_rank=72,
            iv_band="expensive",
        )
        self.assertEqual(advice.strategy_id, "bull_put_spread")

    @patch("analyzer.sideways_options_advisor.detect_nifty_regime")
    def test_high_iv_range_suggests_iron_condor(self, mock_regime):
        mock_regime.return_value = type("R", (), {"regime": "Range-bound"})()
        advice = advise_sideways_strategy(
            fno_symbol="NIFTY",
            ce_strike=24600,
            pe_strike=24400,
            spot=24500,
            or_high=24580,
            or_low=24420,
            iv_rank=78,
            iv_band="expensive",
        )
        self.assertEqual(advice.strategy_id, "iron_condor")
        self.assertEqual(len(advice.legs), 4)

    def test_low_iv_wait(self):
        advice = advise_sideways_strategy(
            fno_symbol="NIFTY",
            ce_strike=24600,
            pe_strike=24400,
            spot=24500,
            or_high=24580,
            or_low=24420,
            iv_rank=20,
            iv_band="cheap",
        )
        self.assertEqual(advice.strategy_id, "wait_breakout")

    def test_short_strangle_two_legs(self):
        legs = build_short_strangle(
            fno_symbol="NIFTY",
            range_high=24600,
            range_low=24400,
        )
        self.assertEqual(len(legs), 2)


if __name__ == "__main__":
    unittest.main()
