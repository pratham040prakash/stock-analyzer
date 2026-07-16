"""Plan Canvas (Phase 2) helper tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.watchlist_pins import PinnedPlan
from ui.components.home_dashboard import VerdictCanvasState
from ui.components.plan_canvas import (
    _lifecycle_line,
    _pick_plan_pin,
    _trigger_line,
    build_trade_plan_view,
)


class PlanCanvasHelpersTest(unittest.TestCase):
    def test_trigger_line_long(self):
        pin = PinnedPlan(
            symbol="RELIANCE",
            entry=2850.0,
            stop_loss=2815.0,
            target=2930.0,
            prep_date="2026-07-16",
            side="LONG",
        )
        self.assertEqual(_trigger_line(pin), "Buy above ₹2,850")

    def test_pick_plan_pin_prefers_starred(self):
        pins = [
            PinnedPlan("TCS", 100, 95, 110, "2026-07-16"),
            PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16"),
        ]
        os_report = MagicMock(starred_symbol="RELIANCE")
        picked = _pick_plan_pin(os_report, pins)
        self.assertEqual(picked.symbol, "RELIANCE")

    def test_lifecycle_from_restriction(self):
        snap = ContextSnapshot(
            timestamp="t",
            market_regime="n",
            market_phase="opening",
            market_breadth="m",
            volatility_state="n",
            liquidity_state="n",
            market_session={"phase": "regular"},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={},
            risk_mode="NEUTRAL",
            trading_restrictions=("Wait until 9:45 before new entries",),
            confidence=0.7,
        )
        self.assertEqual(_lifecycle_line(snap), "Earliest entry after 9:45.")

    def test_build_trade_plan_view_ordering_fields(self):
        pin = PinnedPlan(
            symbol="RELIANCE",
            entry=2850.0,
            stop_loss=2815.0,
            target=2930.0,
            prep_date="2026-07-16",
            side="LONG",
        )
        decision = DecisionArtifact(
            decision_id="d1",
            timestamp="",
            verdict=DecisionVerdict.ACT,
            reason="Momentum confirms after opening range.",
            evidence_packet_id="",
            confidence=0.8,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=True,
        )
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
            confidence=0.8,
        )
        prefs = IntradayPrefs(capital=100_000, max_risk_pct=1.8)
        state = VerdictCanvasState("trade", "Trade", "See the plan", "plan")
        plan = build_trade_plan_view(
            state=state,
            pin=pin,
            decision=decision,
            mis=MagicMock(flags=(), summary=""),
            snapshot=snap,
            prefs=prefs,
        )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertTrue(plan.mentor_opening)
        self.assertIn("Momentum", plan.reason)
        self.assertIn("Buy above", plan.entry_line)
        self.assertIn("Stop", plan.stop_line)
        self.assertIn("Maximum loss", plan.max_loss_line)
        self.assertIn("Target", plan.target_line)
        self.assertTrue(plan.lifecycle_line)


if __name__ == "__main__":
    unittest.main()
