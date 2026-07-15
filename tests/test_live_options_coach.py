"""Tests for live options coach."""

import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from analyzer.live_options_coach import (
    build_live_options_coach,
    suggest_strike,
)

IST = ZoneInfo("Asia/Kolkata")


class TestLiveOptionsCoach(unittest.TestCase):
    def test_pe_invalidated_above_or_high(self):
        now = datetime(2026, 7, 9, 10, 30, tzinfo=IST)
        with patch("analyzer.live_options_coach.get_live_ltp", return_value=(57300.0, {})):
            with patch(
                "analyzer.live_options_coach.fetch_symbol_opening_range",
                return_value=(57244.0, 56800.0),
            ):
                with patch("analyzer.live_options_coach._cached_chain", return_value=None):
                    snap = build_live_options_coach(
                        fno_symbol="BANKNIFTY",
                        option_type="PE",
                        strike=56800,
                        now=now,
                    )
        self.assertEqual(snap.primary_emoji, "🔴")
        self.assertIn("Exit", snap.primary_action)

    def test_inside_or_suggests_credit_for_ce(self):
        now = datetime(2026, 7, 9, 10, 30, tzinfo=IST)
        from analyzer.sideways_options_advisor import SidewaysStrategyAdvice

        sideways = SidewaysStrategyAdvice(
            strategy_id="bear_call_spread",
            strategy_name="Bear Call Spread (credit)",
            market_view="Sideways",
            risk_profile="defined",
            iv_tier="mid",
            spot=24550.0,
            range_high=24600.0,
            range_low=24500.0,
            range_pct=0.4,
            fno_symbol="NIFTY",
            blocks_directional=True,
            action="Consider bear call spread instead of buying CE",
            emoji="🟡",
        )
        with patch("analyzer.live_options_coach.get_live_ltp", return_value=(24550.0, {})):
            with patch(
                "analyzer.live_options_coach.fetch_symbol_opening_range",
                return_value=(24600.0, 24500.0),
            ):
                with patch("analyzer.live_options_coach._cached_chain", return_value=None):
                    with patch(
                        "analyzer.live_options_coach.advise_from_chain",
                        return_value=sideways,
                    ):
                        snap = build_live_options_coach(
                            fno_symbol="NIFTY",
                            option_type="CE",
                            strike=24600,
                            now=now,
                        )
        categories = [s.category for s in snap.signals]
        self.assertIn("sideways", categories)
        self.assertTrue(snap.sideways.blocks_directional)

    def test_suggest_strike_atm(self):
        with patch("analyzer.live_options_coach.get_live_ltp", return_value=(24537.0, {})):
            atm = suggest_strike("NIFTY", "CE")
        self.assertEqual(atm, 24550.0)


if __name__ == "__main__":
    unittest.main()
