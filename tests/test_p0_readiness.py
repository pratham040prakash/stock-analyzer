"""P0 production readiness — Today trust gating (no contradictory hero intel)."""

from __future__ import annotations

import unittest
from types import MappingProxyType
from unittest.mock import MagicMock

from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_assembly import assemble_morning_brief_view_model
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from analyzer.context_engine.models import ContextSnapshot
from ui.broker.state import BrokerSnapshot
from ui.components.decision_card import (
    below_fold_intel_sections,
    hero_failure_html,
    hero_intel_sections,
    project_decision_card,
    today_intel_actions_allowed,
)


def _snapshot() -> ContextSnapshot:
    return ContextSnapshot(
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


def _build_brief(**overrides):
    return assemble_morning_brief_view_model(
        market="NSE",
        context=overrides.get("snapshot", _snapshot()),
        decision=overrides.get("decision"),
        decision_source=overrides.get("decision_source", "none"),
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


class P0TodayTrustGatingTest(unittest.TestCase):
    def test_connect_hides_hero_intel(self):
        brief = _build_brief(
            broker=BrokerSnapshot(state="not_configured"),
            scenario=MorningBriefScenario.NO_BROKER,
        )
        card = project_decision_card(brief)
        self.assertEqual(card.verdict_key, "connect")
        self.assertEqual(hero_intel_sections(card), ())

    def test_rest_hides_hero_intel(self):
        brief = _build_brief(scenario=MorningBriefScenario.WEEKEND)
        card = project_decision_card(brief)
        self.assertEqual(card.verdict_key, "rest")
        self.assertEqual(hero_intel_sections(card), ())

    def test_trade_shows_hero_intel_when_opportunity_visible(self):
        art = DecisionArtifact(
            decision_id="d1",
            timestamp="2026-08-05T09:00:00",
            verdict=DecisionVerdict.ACT,
            reason="RELIANCE lines up.",
            evidence_packet_id="ep1",
            confidence=0.85,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=True,
        )
        packet = MagicMock(
            items=[
                MagicMock(
                    label="Regime",
                    category=MagicMock(value="Market"),
                    type=MagicMock(value="FACT"),
                    source=MagicMock(value="internal_model"),
                    confidence=MagicMock(value="high"),
                    value="Trend",
                    explanation="",
                )
            ],
            conflicts=[],
            gaps=[],
        )
        brief = _build_brief(
            decision=art,
            decision_source="equity",
            os_report=InvestmentOS(starred_symbol="RELIANCE"),
            evidence_packet=packet,
        )
        card = project_decision_card(brief)
        self.assertEqual(hero_intel_sections(card), ("opportunity", "do_next", "risk"))
        self.assertTrue(today_intel_actions_allowed(card))

    def test_failure_message_hides_intel_and_surfaces_html(self):
        brief = _build_brief(
            scenario=MorningBriefScenario.DATA_UNAVAILABLE,
            data_error="Context engine timed out",
        )
        card = project_decision_card(brief)
        self.assertTrue(card.failure_message)
        self.assertEqual(hero_intel_sections(card), ())
        html = hero_failure_html(card)
        self.assertIn("vc-failure", html)
        self.assertIn("timed out", html)

    def test_connect_below_fold_is_market_only(self):
        brief = _build_brief(
            broker=BrokerSnapshot(state="not_configured"),
            scenario=MorningBriefScenario.NO_BROKER,
        )
        card = project_decision_card(brief)
        self.assertEqual(below_fold_intel_sections(card), ("market",))


if __name__ == "__main__":
    unittest.main()
