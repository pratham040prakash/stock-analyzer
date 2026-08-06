"""APS-004 Investment Thesis — presentation projection tests."""

from __future__ import annotations

import unittest
from dataclasses import replace
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
from analyzer.use_cases.morning_brief_models import EvidenceLine, EvidenceSection
from analyzer.context_engine.models import ContextSnapshot
from ui.broker.state import BrokerSnapshot
from ui.components.investment_thesis import (
    InvestmentThesisView,
    build_investment_thesis_view,
    _view_has_content,
)
from ui.components.morning_brief_ui import (
    RecommendationContract,
    recommendation_contract_from_brief,
)


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


def _evidence_line(label: str, value: str) -> EvidenceLine:
    return EvidenceLine(
        label=label,
        value=value,
        type="FACT",
        source="internal_model",
        confidence="high",
    )


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


def _rich_brief_and_contract():
    packet = MagicMock(
        items=[
            MagicMock(
                label="Revenue growth",
                category=MagicMock(value="Fundamentals"),
                type=MagicMock(value="FACT"),
                source=MagicMock(value="internal_model"),
                confidence=MagicMock(value="high"),
                value="18% YoY",
                explanation="",
            ),
            MagicMock(
                label="Cash generation",
                category=MagicMock(value="Fundamentals"),
                type=MagicMock(value="FACT"),
                source=MagicMock(value="internal_model"),
                confidence=MagicMock(value="high"),
                value="Strong FCF",
                explanation="",
            ),
        ],
        conflicts=[
            MagicMock(
                category=MagicMock(value="Margin"),
                description="Margin pressure from input costs",
                severity="medium",
            )
        ],
        gaps=[],
    )
    decision = DecisionArtifact(
        decision_id="d1",
        timestamp="2026-08-05T09:00:00",
        verdict=DecisionVerdict.WAIT,
        reason="Quality compounder — hold through volatility.",
        evidence_packet_id="ep1",
        confidence=0.65,
        uncertainty=UncertaintyVector(),
        capital_recommendation="Hold cash; no new MIS risk today.",
        execution_recommendation="Watch quarterly earnings.",
        explainability=DecisionExplainability(
            why="Quality compounder with durable moat.",
            why_now="Valuation reasonable after pullback.",
            why_not="Near-term macro noise only.",
        ),
        invalidation_conditions=("Loss of competitive advantage", "Debt trend worsens"),
        alternative_actions=("Trim only if allocation exceeds limit",),
    )
    brief = _build_brief(decision=decision, evidence_packet=packet)
    contract = recommendation_contract_from_brief(brief, decision=decision)
    return brief, contract, decision


class APS004InvestmentThesisTest(unittest.TestCase):
    def test_thesis_rendering_from_contract(self) -> None:
        brief, contract, decision = _rich_brief_and_contract()
        view = build_investment_thesis_view(brief=brief, contract=contract, decision=decision)
        self.assertTrue(view.thesis_statement)
        self.assertEqual(view.status_key, "")
        self.assertEqual(view.status_label, "")
        self.assertTrue(view.strengths)
        self.assertTrue(view.concerns)
        self.assertTrue(view.watch_closely)
        self.assertTrue(view.sell_conditions)
        self.assertIn("Loss of competitive advantage", view.sell_conditions)

    def test_thesis_status_hidden_without_domain_field(self) -> None:
        brief, contract, decision = _rich_brief_and_contract()
        view = build_investment_thesis_view(brief=brief, contract=contract, decision=decision)
        self.assertEqual(view.status_key, "")
        self.assertEqual(view.status_label, "")

    def test_empty_strengths(self) -> None:
        brief, contract, decision = _rich_brief_and_contract()
        brief = replace(
            brief,
            evidence=replace(brief.evidence, supporting_signals=()),
        )
        view = build_investment_thesis_view(brief=brief, contract=contract, decision=decision)
        self.assertEqual(view.strengths, ())

    def test_empty_concerns(self) -> None:
        brief, contract, decision = _rich_brief_and_contract()
        brief = replace(brief, risk=replace(brief.risk, warnings=()))
        contract = replace(contract, trade_offs=(), risks=())
        brief = replace(
            brief,
            evidence=replace(brief.evidence, conflicting_signals=()),
        )
        view = build_investment_thesis_view(brief=brief, contract=contract, decision=decision)
        self.assertEqual(view.concerns, ())

    def test_empty_watch_items(self) -> None:
        brief, contract, decision = _rich_brief_and_contract()
        contract = replace(contract, suggested_next_step=())
        brief = replace(
            brief,
            trust=replace(brief.trust, gaps=()),
            evidence=replace(brief.evidence, supporting_signals=()),
        )
        view = build_investment_thesis_view(brief=brief, contract=contract, decision=decision)
        self.assertEqual(view.watch_closely, ())

    def test_empty_sell_conditions(self) -> None:
        brief, contract, _decision = _rich_brief_and_contract()
        contract = replace(contract, what_could_change=())
        view = build_investment_thesis_view(
            brief=brief,
            contract=contract,
            decision=DecisionArtifact(
                decision_id="d2",
                timestamp="2026-08-05T09:00:00",
                verdict=DecisionVerdict.WAIT,
                reason="Hold.",
                evidence_packet_id="ep2",
                confidence=0.5,
                uncertainty=UncertaintyVector(),
                capital_recommendation="Hold.",
                execution_recommendation="Wait.",
                invalidation_conditions=(),
            ),
        )
        self.assertEqual(view.sell_conditions, ())

    def test_progressive_disclosure_level3_only_when_present(self) -> None:
        brief, contract, decision = _rich_brief_and_contract()
        view = build_investment_thesis_view(brief=brief, contract=contract, decision=decision)
        self.assertTrue(view.level3_evidence)

        empty_contract = RecommendationContract(
            why=(),
            evidence=(),
            trade_offs=(),
            risks=(),
            what_could_change=(),
            suggested_next_step=(),
            help_simple=(),
            help_business=(),
            help_professional=(),
        )
        sparse = build_investment_thesis_view(
            brief=replace(
                brief,
                evidence=replace(
                    brief.evidence,
                    key_reasons=("Own for durable cash flows",),
                    supporting_signals=(),
                    conflicting_signals=(),
                ),
                trust=replace(brief.trust, gaps=(), why_this_is_recommended=""),
                risk=replace(brief.risk, warnings=()),
            ),
            contract=empty_contract,
            decision=DecisionArtifact(
                decision_id="d3",
                timestamp="2026-08-05T09:00:00",
                verdict=DecisionVerdict.WAIT,
                reason="Hold.",
                evidence_packet_id="",
                confidence=0.5,
                uncertainty=UncertaintyVector(),
                capital_recommendation="",
                execution_recommendation="",
                invalidation_conditions=(),
            ),
        )
        self.assertEqual(sparse.level3_evidence, ())
        self.assertFalse(_view_has_content(InvestmentThesisView("", "", "", (), (), (), (), ())))

    def test_fully_empty_view_has_no_content(self) -> None:
        empty = InvestmentThesisView("", "", "", (), (), (), (), ())
        self.assertFalse(_view_has_content(empty))


if __name__ == "__main__":
    unittest.main()
