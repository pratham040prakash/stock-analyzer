"""Tests for Decision Card projection (ETS-003b v0.2)."""

from __future__ import annotations

import unittest
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_assembly import assemble_morning_brief_view_model
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from analyzer.context_engine.models import ContextSnapshot
from ui.broker.state import BrokerSnapshot
from ui.components.decision_card import project_decision_card


def _snapshot(phase: str = "regular") -> ContextSnapshot:
    return ContextSnapshot(
        timestamp="2026-08-05T09:00:00+05:30",
        market_regime="Neutral",
        market_phase=phase,
        market_breadth="mixed",
        volatility_state="normal",
        liquidity_state="normal",
        market_session=MappingProxyType({"phase": phase, "is_open": phase == "regular"}),
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


def _build_brief(**overrides):
    snapshot = overrides.get("snapshot", _snapshot())
    scenario = overrides.get("scenario", MorningBriefScenario.NORMAL)
    broker = overrides.get("broker", BrokerSnapshot(state="connected", holdings_count=2))
    decision = overrides.get("decision")
    mis = overrides.get(
        "mis",
        MisTradeAdvisory(verdict="NO_TRADE", emoji="⏸", headline="", summary="Range", score=40),
    )
    os_report = overrides.get("os_report", InvestmentOS())
    return assemble_morning_brief_view_model(
        market="NSE",
        context=snapshot,
        decision=decision,
        decision_source=overrides.get("decision_source", "none"),
        broker=broker,
        mis=mis,
        os_report=os_report,
        pins=[],
        prefs=MagicMock(capital=50000),
        built_at="09:12 IST",
        scenario=scenario,
        stale=overrides.get("stale", False),
        stale_reason=overrides.get("stale_reason", ""),
        context_from_cache=False,
        context_cache_age=None,
        data_error="",
        evidence_packet=overrides.get("evidence_packet"),
    )


class DecisionCardProjectionTest(unittest.TestCase):
    def test_wait_verdict_when_no_decision(self):
        brief = _build_brief(scenario=MorningBriefScenario.DECISION_UNAVAILABLE)
        vm = project_decision_card(brief)
        self.assertEqual(vm.verdict_key, "wait")
        self.assertIn("don't make", vm.reason.lower())

    def test_trade_on_act_with_evidence(self):
        art = DecisionArtifact(
            decision_id="d1",
            timestamp="2026-08-05T09:00:00",
            verdict=DecisionVerdict.ACT,
            reason="Setup ready",
            evidence_packet_id="ep1",
            confidence=0.85,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=True,
        )
        packet = MagicMock(items=[MagicMock(
            label="Regime",
            category=MagicMock(value="Market"),
            type=MagicMock(value="FACT"),
            source=MagicMock(value="internal_model"),
            confidence=MagicMock(value="high"),
            value="Trend",
            explanation="",
        )], conflicts=[], gaps=[])
        brief = _build_brief(
            decision=art,
            decision_source="equity",
            os_report=InvestmentOS(starred_symbol="RELIANCE"),
            evidence_packet=packet,
        )
        vm = project_decision_card(brief)
        self.assertEqual(vm.verdict_key, "trade")
        self.assertTrue(vm.trust_summary)
        self.assertTrue(vm.evidence_teaser)

    def test_connect_when_no_broker(self):
        brief = _build_brief(
            broker=BrokerSnapshot(state="not_configured"),
            scenario=MorningBriefScenario.NO_BROKER,
        )
        vm = project_decision_card(brief)
        self.assertEqual(vm.verdict_key, "connect")
        self.assertFalse(vm.portfolio_ready)

    def test_stale_label_surfaces(self):
        brief = _build_brief(stale=True, stale_reason="Recommendation is from a prior session")
        vm = project_decision_card(brief)
        self.assertTrue(vm.stale)
        self.assertIn("prior session", vm.stale_label)

    def test_act_without_evidence_projects_wait(self):
        art = DecisionArtifact(
            decision_id="d1",
            timestamp="2026-08-05T09:00:00",
            verdict=DecisionVerdict.ACT,
            reason="Setup",
            evidence_packet_id="",
            confidence=0.85,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
        )
        brief = _build_brief(decision=art, os_report=InvestmentOS(starred_symbol="RELIANCE"))
        vm = project_decision_card(brief)
        self.assertEqual(vm.verdict_key, "wait")


if __name__ == "__main__":
    unittest.main()
