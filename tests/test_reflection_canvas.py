"""Reflection Canvas (Phase 3) helper tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from analyzer.context_engine.models import ContextSnapshot
from ui.broker.state import BrokerSnapshot
from ui.components.reflection_canvas import (
    _coaching_insight,
    _forward_line,
    _resolve_trader_state,
    _trader_narrative,
    build_reflection_view,
)


class ReflectionCanvasHelpersTest(unittest.TestCase):
    def test_four_state_words_only(self):
        from ui.components.reflection_canvas import _STATE_TOKENS

        self.assertEqual(len(_STATE_TOKENS), 4)
        self.assertEqual(set(_STATE_TOKENS.keys()), {"growing", "steady", "rebuilding", "focused"})

    def test_rebuilding_on_loss_streak(self):
        mis = MagicMock(loss_streak_days=2, flags=())
        snap = MagicMock(risk_mode="NEUTRAL", market_session={}, market_phase="regular")
        key = _resolve_trader_state(mis, snap, [], [])
        self.assertEqual(key, "rebuilding")

    def test_coaching_insight_waiting(self):
        text = _coaching_insight("focused", mis=MagicMock(loss_streak_days=0), journal=[])
        self.assertIn("waiting", text.lower())

    def test_narrative_is_trader_not_portfolio(self):
        lines = _trader_narrative(
            "steady",
            mis=MagicMock(loss_streak_days=0, flags=()),
            journal=[],
            learning=[],
        )
        joined = " ".join(lines).lower()
        self.assertNotIn("diversified", joined)
        self.assertNotIn("holdings", joined)

    def test_build_reflection_has_forward_line(self):
        snap = ContextSnapshot(
            timestamp="t",
            market_regime="n",
            market_phase="regular",
            market_breadth="m",
            volatility_state="n",
            liquidity_state="n",
            market_session={"phase": "regular"},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={},
            risk_mode="NEUTRAL",
            trading_restrictions=(),
            confidence=0.7,
        )
        view = build_reflection_view(
            broker=BrokerSnapshot(state="connected"),
            mis=MagicMock(loss_streak_days=0, flags=()),
            snapshot=snap,
            os_report=MagicMock(starred_symbol="", next_step=""),
            portfolio=None,
            journal=[],
            learning=[],
        )
        self.assertTrue(view.forward_line)
        self.assertTrue(view.coaching_insight)
        self.assertEqual(view.primary_label, "I'm good")

    def test_forward_line_mentions_tomorrow(self):
        snap = ContextSnapshot(
            timestamp="t",
            market_regime="n",
            market_phase="regular",
            market_breadth="m",
            volatility_state="n",
            liquidity_state="n",
            market_session={"phase": "regular"},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={},
            risk_mode="NEUTRAL",
            trading_restrictions=(),
            confidence=0.7,
        )
        line = _forward_line(
            snapshot=snap,
            os_report=MagicMock(starred_symbol=""),
            mis=MagicMock(loss_streak_days=0),
        )
        self.assertIn("Tomorrow", line)


if __name__ == "__main__":
    unittest.main()
