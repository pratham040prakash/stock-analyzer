"""Tests for setup wizard, session phase, pick display."""

import unittest
from unittest.mock import patch

from analyzer.intraday_watchlist import IntradayWatchlistPick, ProChecklist
from analyzer.watchlist_pick_display import format_pick_why


class TestSessionPhase(unittest.TestCase):
    @patch("analyzer.session_phase.market_session_status", return_value={"phase": "open"})
    def test_live(self, _):
        from analyzer.session_phase import suggestions_ui_phase

        self.assertEqual(suggestions_ui_phase(), "live")

    @patch("analyzer.session_phase.can_score_trade_date", return_value=True)
    @patch("analyzer.session_phase.market_session_status", return_value={"phase": "after_hours"})
    def test_post_close(self, _m, _c):
        from analyzer.session_phase import suggestions_ui_phase

        self.assertEqual(suggestions_ui_phase(), "post_close")


class TestPickDisplay(unittest.TestCase):
    def test_format_why(self):
        p = IntradayWatchlistPick(
            rank=1,
            nse_symbol="TCS",
            name="TCS",
            price=100.0,
            sector="IT",
            prep_score=50.0,
            market_bias="NEUTRAL",
            checklist=ProChecklist(True, True, False, True, True, 4, notes=["Vol spike"]),
            entry=100.0,
            stop_loss=98.0,
            target=105.0,
            pivot=None,
            support=None,
            resistance=None,
            atr_pct=2.0,
            rsi=60.0,
            macd_bullish=True,
            volume_ratio=1.8,
            sector_tailwind=False,
            breakout_note="",
            news_note="",
            can_enter=True,
            plan_summary="",
        )
        why = format_pick_why(p)
        self.assertIn("ATR", why)
        self.assertIn("RSI", why)


class TestSetupStatus(unittest.TestCase):
    @patch("analyzer.setup_status.telegram_configured", return_value=True)
    @patch("analyzer.setup_status.load_env_credentials", return_value={"api_key": "x"})
    def test_setup_steps(self, _e, _t):
        from analyzer.setup_status import build_setup_status

        steps = build_setup_status()
        self.assertEqual(len(steps), 4)
        self.assertTrue(steps[0].done)


if __name__ == "__main__":
    unittest.main()
