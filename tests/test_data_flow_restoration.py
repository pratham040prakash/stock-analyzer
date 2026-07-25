"""P0 data-flow restoration — loader → DTO → existing renderer contracts."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from analyzer.decision_engine.models import (
    DecisionArtifact,
    DecisionExplainability,
    DecisionVerdict,
    UncertaintyVector,
)
from analyzer.investment_os import OSModule
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.dashboard_pipeline import decision_reason, is_equity_decision
from ui.components.home_dashboard import _pick_decision, _why_advanced, _why_primary
from ui.components.today_intelligence import build_today_command_center
from ui.components.home_dashboard import VerdictCanvasState


class DataFlowRestorationTest(unittest.TestCase):
    def test_journal_pnl_reaches_portfolio_dto(self):
        state = VerdictCanvasState("wait", "Wait", "Done", "done")
        snapshot = MagicMock(
            market_regime="Neutral",
            risk_mode="NEUTRAL",
            market_phase="regular",
            market_breadth="mixed",
            volatility_state="normal",
            liquidity_state="normal",
            trading_restrictions=(),
            sector_strength={},
        )
        mis = MagicMock(flags=(), loss_streak_days=0, mtf_summary="", flow_summary="", synthesis_summary="")
        risk_mod = OSModule(
            key="risk",
            label="Risk AI",
            question="?",
            headline="2 shares · max loss ₹500",
            detail="",
            status="ok",
        )

        def module(key: str):
            if key == "risk":
                return risk_mod
            return None

        os_report = MagicMock(starred_symbol="", next_step="", max_loss_inr=500, module=module)
        holding = MagicMock(
            tradingsymbol="TCS",
            kite_symbol="TCS",
            quantity=10,
            last_price=100.0,
            average_price=95.0,
            pnl=50.0,
        )
        portfolio = MagicMock(holdings=[holding])
        prefs = MagicMock(capital=100_000, max_risk_pct=1.0)
        broker = BrokerSnapshot(state="connected", holdings_count=1, last_sync_at="09:00 IST")

        center = build_today_command_center(
            state=state,
            snapshot=snapshot,
            mis=mis,
            os_report=os_report,
            pins=[],
            pulse=None,
            portfolio=portfolio,
            prefs=prefs,
            broker=broker,
            journal_today_pnl=-250.0,
            decision=None,
        )
        joined = " ".join(center.portfolio_lines)
        self.assertIn("Today's Journal P/L", joined)
        self.assertIn("₹-250", joined)
        self.assertIn("Strongest", joined)

    def test_decision_explainability_reaches_mentor_reason(self):
        artifact = DecisionArtifact(
            decision_id="d1",
            timestamp="",
            verdict=DecisionVerdict.WAIT,
            reason="short reason",
            evidence_packet_id="",
            confidence=0.5,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            explainability=DecisionExplainability(
                why="Full explainability narrative from engine.",
                why_now="",
                why_not="",
            ),
        )
        self.assertEqual(decision_reason(artifact), "Full explainability narrative from engine.")

    def test_synthesis_pillars_reach_why_advanced(self):
        mis = MagicMock(
            flags=(),
            synthesis_pillars=["Regime supports caution", "Volume confirms wait"],
        )
        snapshot = MagicMock(trading_restrictions=())
        bullets = _why_advanced(None, mis, snapshot, pins=[])
        self.assertIn("Regime supports caution", bullets)

    def test_decision_fields_reach_why_primary(self):
        artifact = DecisionArtifact(
            decision_id="d2",
            timestamp="",
            verdict=DecisionVerdict.WAIT,
            reason="short",
            evidence_packet_id="",
            confidence=0.5,
            uncertainty=UncertaintyVector(),
            capital_recommendation="Size down to 1 lot.",
            execution_recommendation="Wait for 9:45 trigger.",
            invalidation_conditions=["Break below VWAP"],
            explainability=DecisionExplainability(
                why="Tape is choppy — wait for confirmation.",
                why_now="",
                why_not="",
            ),
        )
        bullets = _why_primary(artifact)
        self.assertIn("Tape is choppy", bullets[0])
        self.assertTrue(any("Capital:" in line for line in bullets))
        self.assertTrue(any("Execution:" in line for line in bullets))
        self.assertTrue(any("If wrong:" in line for line in bullets))

    def test_options_mis_decision_not_used_for_equity_home(self):
        equity = DecisionArtifact(
            decision_id="e1",
            timestamp="",
            verdict=DecisionVerdict.ACT,
            reason="equity ok",
            evidence_packet_id="",
            confidence=0.8,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            subject_type="equity",
        )
        options = DecisionArtifact(
            decision_id="o1",
            timestamp="",
            verdict=DecisionVerdict.WAIT,
            reason="NIFTY CE wait",
            evidence_packet_id="",
            confidence=0.5,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            subject_type="options",
        )
        os_report = MagicMock(starred_symbol="", decision_artifact=None)
        mis = MagicMock(decision_artifact=options)
        picked, source = _pick_decision(mis, os_report)
        self.assertIsNone(picked)
        self.assertEqual(source, "none")
        self.assertFalse(is_equity_decision(options))

        os_report2 = MagicMock(starred_symbol="RELIANCE", decision_artifact=equity)
        picked2, source2 = _pick_decision(mis, os_report2)
        self.assertEqual(picked2, equity)
        self.assertEqual(source2, "equity")

    def test_review_module_reaches_do_next_on_rest(self):
        state = VerdictCanvasState("rest", "Rest", "View week", "week")
        snapshot = MagicMock(
            market_regime="",
            risk_mode="CLOSED",
            market_phase="after_hours",
            market_breadth="",
            volatility_state="",
            liquidity_state="",
            trading_restrictions=(),
            sector_strength={},
        )
        review = OSModule(
            key="review",
            label="Review AI",
            question="?",
            headline="Log P&L",
            detail="Log P&L in Review AI, then scan for tomorrow.",
            status="info",
        )
        os_report = MagicMock(starred_symbol="", next_step="", max_loss_inr=0, module=lambda k: review if k == "review" else None)
        mis = MagicMock(flags=(), loss_streak_days=0, mtf_summary="", flow_summary="", synthesis_summary="")
        prefs = MagicMock(capital=0, max_risk_pct=0)
        broker = BrokerSnapshot(state="connected")

        center = build_today_command_center(
            state=state,
            snapshot=snapshot,
            mis=mis,
            os_report=os_report,
            pins=[],
            pulse=None,
            portfolio=None,
            prefs=prefs,
            broker=broker,
        )
        self.assertIn("Review AI", center.ai_recommendation)


if __name__ == "__main__":
    unittest.main()
