"""APS-003 Recommendation Explanation — presentation projection tests."""

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
from analyzer.context_engine.models import ContextSnapshot
from ui.broker.state import BrokerSnapshot
from ui.components.morning_brief_ui import (
    RecommendationContract,
    recommendation_action_from_brief,
    recommendation_contract_from_brief,
)
from ui.components.recommendation_explanation import build_recommendation_explanation_view


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


class APS003RecommendationExplanationTest(unittest.TestCase):
    def test_action_mapping_buy_wait_hold_reduce_sell(self) -> None:
        base = _build_brief()
        brief_trade = replace(
            base,
            decision=replace(base.decision, verdict_key="trade", verdict_display="Buy"),
        )
        self.assertEqual(recommendation_action_from_brief(brief_trade), ("buy", "Buy"))

        brief_wait = replace(
            base,
            decision=replace(base.decision, verdict_key="wait", verdict_display="Wait"),
        )
        self.assertEqual(recommendation_action_from_brief(brief_wait), ("wait", "Wait"))

        brief_hold = replace(
            base,
            decision=replace(base.decision, verdict_key="pause", verdict_display="Hold"),
        )
        self.assertEqual(recommendation_action_from_brief(brief_hold), ("hold", "Hold"))

        decision_reduce = DecisionArtifact(
            decision_id="d2",
            timestamp="2026-08-05T09:00:00",
            verdict=DecisionVerdict.REDUCE,
            reason="Reduce exposure.",
            evidence_packet_id="ep2",
            confidence=0.5,
            uncertainty=UncertaintyVector(),
            capital_recommendation="Trim size.",
            execution_recommendation="Scale out on strength.",
        )
        brief_reduce = _build_brief(decision=decision_reduce)
        self.assertEqual(
            recommendation_action_from_brief(brief_reduce, decision=decision_reduce),
            ("reduce", "Reduce"),
        )

        brief_sell = replace(
            base,
            decision=replace(base.decision, verdict_key="wait", verdict_display="Strong Sell"),
        )
        self.assertEqual(recommendation_action_from_brief(brief_sell), ("sell", "Sell"))

    def test_explanation_sections_from_contract(self) -> None:
        brief = _build_brief(with_decision=True)
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
        contract = recommendation_contract_from_brief(brief, decision=decision)
        view = build_recommendation_explanation_view(
            brief=brief,
            contract=contract,
            decision=decision,
        )
        self.assertTrue(view.level1_simple)
        self.assertTrue(view.why)
        self.assertTrue(view.what_could_change)
        self.assertTrue(view.what_to_monitor)
        self.assertIn("No entries until breadth improves.", view.what_to_monitor)

    def test_empty_sections_stay_empty(self) -> None:
        brief = _build_brief()
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
        view = build_recommendation_explanation_view(brief=brief, contract=empty_contract)
        self.assertEqual(view.why, ())
        self.assertEqual(view.evidence, ())
        self.assertEqual(view.risks, ())
        self.assertEqual(view.what_could_change, ())
        self.assertEqual(view.what_to_monitor, ())
        self.assertEqual(view.level1_simple, "")
        self.assertEqual(view.level2_lines, ())
        self.assertEqual(view.level3_lines, ())


if __name__ == "__main__":
    unittest.main()
