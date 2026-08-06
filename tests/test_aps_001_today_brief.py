"""APS-001 Today's Brief — recommendation contract and surface projection tests."""

from __future__ import annotations

import unittest
from types import MappingProxyType
from unittest.mock import MagicMock

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
from analyzer.context_engine.models import ContextSnapshot
from ui.broker.state import BrokerSnapshot
from ui.components.decision_card import hero_session_ribbon_html, project_decision_card
from ui.components.morning_brief_ui import recommendation_contract_from_brief


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


def _build_brief(**overrides):
    decision = overrides.get("decision")
    if decision is None and overrides.get("with_decision"):
        decision = DecisionArtifact(
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


class APS001RecommendationContractTest(unittest.TestCase):
    def test_contract_order_and_sections(self):
        packet = MagicMock(
            items=[
                MagicMock(
                    label="Breadth",
                    category=MagicMock(value="Market"),
                    type=MagicMock(value="FACT"),
                    source=MagicMock(value="internal_model"),
                    confidence=MagicMock(value="high"),
                    value="Weak",
                    explanation="",
                )
            ],
            conflicts=[
                MagicMock(
                    category=MagicMock(value="Momentum"),
                    description="Short-term momentum conflicts with risk mode",
                    severity="medium",
                )
            ],
            gaps=[],
        )
        art = DecisionArtifact(
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
        brief = _build_brief(decision=art, evidence_packet=packet)
        contract = recommendation_contract_from_brief(brief, decision=art)

        self.assertTrue(contract.why)
        self.assertTrue(contract.trade_offs)
        self.assertTrue(contract.suggested_next_step)
        self.assertTrue(any("Hold cash" in step for step in contract.suggested_next_step))
        self.assertTrue(any("Chasing opens" in item for item in contract.trade_offs))
        self.assertTrue(contract.what_could_change)
        self.assertTrue(contract.help_simple)
        self.assertGreaterEqual(len(contract.help_professional), len(contract.help_simple))

    def test_session_ribbon_html(self):
        brief = _build_brief(
            snapshot=_snapshot(
                risk_mode="RISK-OFF",
                trading_restrictions=("No new MIS until cooldown ends",),
            )
        )
        html = hero_session_ribbon_html(brief.risk.session_ribbon)
        self.assertIn("vc-session-ribbon", html)
        self.assertIn("RISK-OFF", html)

    def test_connect_hides_hero_intel(self):
        brief = _build_brief(
            broker=BrokerSnapshot(state="not_configured"),
            scenario=MorningBriefScenario.NO_BROKER,
        )
        card = project_decision_card(brief)
        self.assertEqual(card.verdict_key, "connect")


if __name__ == "__main__":
    unittest.main()
