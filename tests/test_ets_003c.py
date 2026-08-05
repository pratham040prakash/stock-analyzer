"""ETS-003c — Verdict Canvas trust-field binding (L0 hero projection)."""

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
    hero_l0_trust_html,
    hero_stale_html,
    project_decision_card,
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
        data_error="",
        evidence_packet=overrides.get("evidence_packet"),
    )


class ETS003cHeroProjectionTest(unittest.TestCase):
    def test_stale_badge_renders(self):
        brief = _build_brief(stale=True, stale_reason="Recommendation is from a prior session")
        card = project_decision_card(brief)
        html = hero_stale_html(card)
        self.assertIn("vc-stale", html)
        self.assertIn("prior session", html)

    def test_trust_and_evidence_teaser_bind(self):
        art = DecisionArtifact(
            decision_id="d1",
            timestamp="2026-08-05T09:00:00",
            verdict=DecisionVerdict.WAIT,
            reason="Stand down today.",
            evidence_packet_id="ep1",
            confidence=0.62,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
        )
        packet = MagicMock(
            items=[
                MagicMock(
                    label="Regime",
                    category=MagicMock(value="Market"),
                    type=MagicMock(value="FACT"),
                    source=MagicMock(value="internal_model"),
                    confidence=MagicMock(value="high"),
                    value="Sideways",
                    explanation="",
                )
            ],
            conflicts=[],
            gaps=[],
        )
        brief = _build_brief(decision=art, decision_source="equity", evidence_packet=packet)
        card = project_decision_card(brief)
        html = hero_l0_trust_html(card)
        self.assertIn("vc-trust-line", html)
        self.assertIn("vc-evidence-teaser", html)
        self.assertIn("vc-confidence-band", html)

    def test_thirty_second_fields_present_on_card(self):
        """L0 answers: act, why, trust, next action — via DecisionCardViewModel only."""
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
        card = project_decision_card(brief)
        self.assertTrue(card.verdict_word)
        self.assertTrue(card.reason)
        self.assertTrue(card.trust_summary)
        self.assertTrue(card.cta_label)
        self.assertTrue(card.evidence_teaser)


if __name__ == "__main__":
    unittest.main()
