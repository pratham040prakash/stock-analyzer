"""RC-001 — render-level integration tests for APEX V2 surfaces."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import (
    DecisionArtifact,
    DecisionExplainability,
    DecisionVerdict,
    UncertaintyVector,
)
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_assembly import assemble_morning_brief_view_model
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.decision_card import project_decision_card
from ui.components.morning_brief_ui import recommendation_contract_from_brief
from ui.components.plan_canvas import TradePlanView, _render_plan_execution_details
from ui.components.today_brief_experience import (
    _render_understand_popover,
    render_today_brief_experience,
)
from ui.components.today_intelligence import TodayCommandCenter

REPO_ROOT = Path(__file__).resolve().parent.parent


def _snapshot(**overrides) -> ContextSnapshot:
    base = dict(
        timestamp="2026-08-05T09:00:00+05:30",
        market_regime="Neutral",
        market_phase="regular",
        market_breadth="mixed",
        volatility_state="normal",
        liquidity_state="normal",
        market_session=MappingProxyType({"phase": "regular", "is_open": True}),
        sector_strength=MappingProxyType({}),
        industry_strength=MappingProxyType({}),
        macro_state=MappingProxyType({}),
        global_market_state=MappingProxyType({}),
        risk_mode="NEUTRAL",
        trading_restrictions=(),
        confidence=0.72,
        snapshot_id="ctx1",
        context_hash="",
    )
    base.update(overrides)
    return ContextSnapshot(**base)


def _decision_artifact(**overrides) -> DecisionArtifact:
    base = dict(
        decision_id="d1",
        timestamp="2026-08-05T09:00:00",
        verdict=DecisionVerdict.WAIT,
        reason="Range-bound session — patience beats forcing a trade.",
        evidence_packet_id="ep1",
        confidence=0.65,
        uncertainty=UncertaintyVector(),
        capital_recommendation="Hold cash; no new MIS risk today.",
        execution_recommendation="No entries until breadth improves.",
        explainability=DecisionExplainability(
            why="Range-bound session.",
            why_now="Pre-open volatility is elevated.",
            why_not="Chasing opens adds slippage without edge.",
        ),
        invalidation_conditions=("Nifty breaks above prior day high with volume",),
        alternative_actions=("Review RELIANCE plan only if setup triggers",),
    )
    base.update(overrides)
    return DecisionArtifact(**base)


def _build_brief(**overrides):
    decision = overrides.get("decision")
    if decision is None and overrides.get("with_decision"):
        decision = _decision_artifact()
    return assemble_morning_brief_view_model(
        market="NSE",
        context=overrides.get("snapshot", _snapshot()),
        decision=decision,
        decision_source=overrides.get("decision_source", "equity"),
        broker=overrides.get("broker", BrokerSnapshot(state="connected", holdings_count=2)),
        mis=overrides.get(
            "mis",
            MisTradeAdvisory(verdict="NO_TRADE", emoji="⏸", headline="", summary="Range", score=40),
        ),
        os_report=overrides.get("os_report", InvestmentOS()),
        pins=[],
        prefs=MagicMock(capital=50000),
        built_at="09:12 IST",
        scenario=overrides.get("scenario", MorningBriefScenario.NORMAL),
        stale=overrides.get("stale", False),
        stale_reason=overrides.get("stale_reason", ""),
        context_from_cache=False,
        context_cache_age=None,
        data_error=overrides.get("data_error", ""),
        evidence_packet=overrides.get("evidence_packet"),
    )


def _command_center() -> TodayCommandCenter:
    return TodayCommandCenter(
        opportunity_name="RELIANCE",
        entry_direction="Long",
        selection_reason="Structure aligns with plan.",
        price_status="Near trigger",
        market_gate="Neutral session",
        market_support="Markets are balanced today.",
        portfolio_lines=(),
        risk_warnings=(),
        next_watch="RELIANCE trigger",
        ai_recommendation="Wait for confirmation.",
        best_ticker="RELIANCE",
    )


def _streamlit_mocks(mock_st):
    mock_st.markdown.side_effect = lambda md, **kw: None
    mock_st.columns.return_value = (MagicMock(), MagicMock())
    mock_st.button.return_value = False
    mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
    mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
    mock_st.expander.return_value.__enter__ = MagicMock(return_value=None)
    mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
    mock_st.radio.return_value = "Simple"


class ReviewDepthSingleSourceTest(unittest.TestCase):
    def test_today_brief_wires_decision_depth_panel(self):
        text = (REPO_ROOT / "ui/components/today_brief_experience.py").read_text(encoding="utf-8")
        self.assertIn("render_decision_depth_panel", text)
        self.assertIn("render_understand_popover", text)
        self.assertNotIn("build_recommendation_explanation_view", text)
        self.assertNotIn("render_recommendation_explanation(", text)
        self.assertNotIn("build_investment_thesis_view", text)
        self.assertNotIn("render_investment_thesis(", text)

    def test_plan_canvas_wires_decision_depth_panel(self):
        text = (REPO_ROOT / "ui/components/plan_canvas.py").read_text(encoding="utf-8")
        self.assertIn("render_decision_depth_panel", text)


class UnderstandPopoverIntegrationTest(unittest.TestCase):
    @patch("ui.components.today_brief_experience.render_decision_depth_panel")
    @patch("ui.components.today_brief_experience.render_understand_popover")
    def test_understand_popover_reuses_review_depth_compositor(
        self,
        mock_understand,
        mock_depth_panel,
    ):
        brief = _build_brief(with_decision=True)
        decision = _decision_artifact()
        contract = recommendation_contract_from_brief(brief, decision=decision)
        mis = MisTradeAdvisory(verdict="NO_TRADE", emoji="", headline="", summary="", score=40)

        _render_understand_popover(
            contract=contract,
            confidence_pct=65,
            brief=brief,
            decision=decision,
            mis=mis,
        )

        mock_understand.assert_called_once()
        extra_body = mock_understand.call_args.kwargs["extra_body"]
        self.assertIsNotNone(extra_body)
        extra_body()
        mock_depth_panel.assert_called_once_with(
            brief=brief,
            contract=contract,
            decision=decision,
            mis=mis,
            key_prefix="apex_cmd_understand",
            include_section_header=False,
        )


class HomeCommandCenterIntegrationTest(unittest.TestCase):
    @patch("ui.components.today_brief_experience.build_today_command_center")
    @patch("ui.components.today_brief_experience.render_decision_depth_panel")
    @patch("ui.components.today_brief_experience.st")
    def test_home_command_center_composition(
        self,
        mock_st,
        mock_depth_panel,
        mock_build_center,
    ):
        html_chunks: list[str] = []

        def capture(md, **kw):
            html_chunks.append(str(md))

        mock_st.markdown.side_effect = capture
        mock_st.columns.return_value = (MagicMock(), MagicMock())
        mock_st.button.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.radio.return_value = "Simple"
        mock_build_center.return_value = _command_center()

        brief = _build_brief(with_decision=True)
        decision = _decision_artifact()
        card = project_decision_card(brief)
        snapshot = _snapshot()
        mis = MisTradeAdvisory(verdict="NO_TRADE", emoji="", headline="", summary="", score=40)

        render_today_brief_experience(
            cached={"built_at": "09:12 IST", "prefs": MagicMock(capital=50000)},
            brief=brief,
            card=card,
            broker=BrokerSnapshot(state="connected", user_name="Alex Investor"),
            snapshot=snapshot,
            mis=mis,
            domain_decision=decision,
            pins=[],
            os_report=InvestmentOS(),
            prefs=MagicMock(capital=50000),
            pulse=None,
            portfolio=None,
            journal_today_pnl=None,
        )

        joined = "\n".join(html_chunks)
        self.assertIn('role="main"', joined)
        self.assertIn("apex-command-hero", joined)
        self.assertIn("apex-status-strip", joined)
        self.assertIn("apex-verdict-title", joined)
        mock_depth_panel.assert_called_once()
        self.assertEqual(
            mock_depth_panel.call_args.kwargs["key_prefix"],
            "apex_cmd_understand",
        )
        self.assertFalse(mock_depth_panel.call_args.kwargs["include_section_header"])


class ReviewWorkspaceIntegrationTest(unittest.TestCase):
    @patch("ui.components.plan_canvas.render_decision_depth_panel")
    @patch("ui.components.plan_canvas.st")
    def test_review_workspace_reuses_review_depth_compositor(self, mock_st, mock_depth_panel):
        _streamlit_mocks(mock_st)
        mock_st.link_button.return_value = None

        brief = _build_brief(with_decision=True)
        decision = _decision_artifact()
        plan = TradePlanView(
            has_plan=True,
            symbol="RELIANCE",
            side="LONG",
            mentor_opening="Wait for the trigger.",
            reason="Structure holds.",
            entry_line="Buy above ₹2,850",
            stop_line="Stop ₹2,815",
            max_loss_line="Maximum loss ₹350",
            target_line="Target ₹2,930",
            lifecycle_line="Valid through close.",
            kite_url="https://kite.zerodha.com/markets/equity/RELIANCE",
        )
        snapshot = _snapshot()
        mis = MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70)

        _render_plan_execution_details(
            plan,
            brief=brief,
            decision=decision,
            mis=mis,
            snapshot=snapshot,
            pins=[
                PinnedPlan("RELIANCE", 2850.0, 2815.0, 2930.0, "2026-08-05", side="LONG"),
            ],
        )

        mock_depth_panel.assert_called_once()
        kwargs = mock_depth_panel.call_args.kwargs
        self.assertEqual(kwargs["key_prefix"], "apex_plan_depth")
        self.assertTrue(kwargs.get("include_section_header", True))


if __name__ == "__main__":
    unittest.main()
