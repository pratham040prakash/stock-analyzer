"""Tests for Morning Brief application use case (ETS-003b v0.2)."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief import (
    build_morning_brief,
    domain_from_cache_bundle,
    domain_to_cache_bundle,
    load_morning_brief_domain,
    pick_decision,
    view_model_from_domain,
)
from analyzer.use_cases.morning_brief_assembly import assemble_evidence_section
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from ui.broker.state import BrokerSnapshot


def _snapshot(**overrides) -> ContextSnapshot:
    session = overrides.pop("market_session", {"phase": "regular", "is_open": True, "date": "2026-08-05"})
    return ContextSnapshot(
        timestamp=datetime.now().isoformat(),
        market_regime=overrides.get("market_regime", "Neutral"),
        market_phase=overrides.get("market_phase", "regular"),
        market_breadth="mixed",
        volatility_state="normal",
        liquidity_state="normal",
        market_session=MappingProxyType(dict(session)),
        sector_strength=MappingProxyType({}),
        industry_strength=MappingProxyType({}),
        macro_state=MappingProxyType({}),
        global_market_state=MappingProxyType({}),
        risk_mode=overrides.get("risk_mode", "NEUTRAL"),
        trading_restrictions=overrides.get("trading_restrictions", ()),
        confidence=0.7,
        snapshot_id="ctx_test",
        context_hash="",
    )


def _artifact(**kwargs) -> DecisionArtifact:
    defaults = dict(
        decision_id="d1",
        timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        verdict=DecisionVerdict.WAIT,
        reason="wait",
        evidence_packet_id="ep1",
        confidence=0.6,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        subject_type="equity",
    )
    defaults.update(kwargs)
    return DecisionArtifact(**defaults)


class PickDecisionTest(unittest.TestCase):
    def test_prefers_starred_equity(self):
        art = _artifact(verdict=DecisionVerdict.ACT)
        os_report = MagicMock(starred_symbol="RELIANCE", decision_artifact=art)
        mis = MagicMock(decision_artifact=art)
        picked, source = pick_decision(mis, os_report)
        self.assertEqual(picked, art)
        self.assertEqual(source, "equity")


class MorningBriefScenarioTest(unittest.TestCase):
    @patch("analyzer.use_cases.morning_brief.build_investment_os")
    @patch("analyzer.use_cases.morning_brief.build_mis_trade_advisory")
    @patch("analyzer.use_cases.morning_brief.build_context_snapshot")
    @patch("analyzer.use_cases.morning_brief.load_pinned_plans", return_value=[])
    @patch("analyzer.use_cases.morning_brief.load_intraday_prefs")
    def test_weekend_scenario(self, mock_prefs, _pins, mock_ctx, mock_mis, mock_os):
        mock_prefs.return_value = MagicMock()
        mock_ctx.return_value = _snapshot(market_session={"phase": "weekend", "is_open": False})
        mock_mis.return_value = MisTradeAdvisory(
            verdict="NO_TRADE", emoji="⏸", headline="", summary="", score=0
        )
        mock_os.return_value = InvestmentOS()
        brief = build_morning_brief(
            market="NSE",
            broker=BrokerSnapshot(state="connected", holdings_count=1),
            use_cache=False,
        )
        self.assertEqual(brief.meta.scenario, MorningBriefScenario.WEEKEND.value)

    @patch("analyzer.use_cases.morning_brief.build_investment_os")
    @patch("analyzer.use_cases.morning_brief.build_mis_trade_advisory")
    @patch("analyzer.use_cases.morning_brief.build_context_snapshot")
    @patch("analyzer.use_cases.morning_brief.load_pinned_plans", return_value=[])
    @patch("analyzer.use_cases.morning_brief.load_intraday_prefs")
    def test_no_broker_scenario(self, mock_prefs, _pins, mock_ctx, mock_mis, mock_os):
        mock_prefs.return_value = MagicMock()
        mock_ctx.return_value = _snapshot()
        mock_mis.return_value = MisTradeAdvisory(
            verdict="NO_TRADE", emoji="⏸", headline="", summary="", score=0
        )
        mock_os.return_value = InvestmentOS()
        brief = build_morning_brief(
            market="NSE",
            broker=BrokerSnapshot(state="not_configured"),
            use_cache=False,
        )
        self.assertEqual(brief.meta.scenario, MorningBriefScenario.NO_BROKER.value)
        self.assertFalse(brief.trust.portfolio_sync_status.personalized)

    @patch("analyzer.use_cases.morning_brief.fetch_evidence_packet_safe", return_value=None)
    @patch("analyzer.use_cases.morning_brief.build_investment_os")
    @patch("analyzer.use_cases.morning_brief.build_mis_trade_advisory")
    @patch("analyzer.use_cases.morning_brief.build_context_snapshot")
    @patch("analyzer.use_cases.morning_brief.load_pinned_plans", return_value=[])
    @patch("analyzer.use_cases.morning_brief.load_intraday_prefs")
    def test_act_without_evidence_downgrades(
        self, mock_prefs, _pins, mock_ctx, mock_mis, mock_os, _fetch
    ):
        mock_prefs.return_value = MagicMock()
        mock_ctx.return_value = _snapshot()
        art = _artifact(verdict=DecisionVerdict.ACT, confidence=0.85, evidence_packet_id="")
        mock_mis.return_value = MisTradeAdvisory(
            verdict="TRADE_OK", emoji="✅", headline="", summary="", score=80
        )
        os = InvestmentOS(starred_symbol="RELIANCE")
        os.decision_artifact = art
        mock_os.return_value = os
        brief = build_morning_brief(
            market="NSE",
            broker=BrokerSnapshot(state="connected"),
            use_cache=False,
        )
        self.assertEqual(brief.decision.verdict_key, "wait")
        self.assertTrue(any("Evidence" in g for g in brief.trust.gaps))


class TrustFirstViewModelTest(unittest.TestCase):
    @patch("analyzer.use_cases.morning_brief.build_investment_os")
    @patch("analyzer.use_cases.morning_brief.build_mis_trade_advisory")
    @patch("analyzer.use_cases.morning_brief.build_context_snapshot")
    @patch("analyzer.use_cases.morning_brief.load_pinned_plans", return_value=[])
    @patch("analyzer.use_cases.morning_brief.load_intraday_prefs")
    @patch("analyzer.use_cases.morning_brief.fetch_evidence_packet_safe")
    def test_view_model_has_decision_evidence_trust(
        self, mock_fetch, mock_prefs, _pins, mock_ctx, mock_mis, mock_os
    ):
        mock_prefs.return_value = MagicMock()
        mock_ctx.return_value = _snapshot()
        art = _artifact(reason="Range day — wait for clarity")
        mock_mis.return_value = MisTradeAdvisory(
            verdict="NO_TRADE", emoji="⏸", headline="", summary="Range", score=40
        )
        os = InvestmentOS(starred_symbol="TCS")
        os.decision_artifact = art
        mock_os.return_value = os
        mock_fetch.return_value = MagicMock(items=[], conflicts=[], gaps=[])

        brief = build_morning_brief(
            market="NSE",
            broker=BrokerSnapshot(state="connected", holdings_count=2),
            use_cache=False,
        )
        self.assertTrue(brief.decision.reason)
        self.assertTrue(brief.trust.why_this_is_recommended)
        self.assertIsNotNone(brief.evidence)
        self.assertIn(brief.decision.confidence_band, ("high", "medium", "low", "unknown"))

    def test_evidence_section_marks_act_gap(self):
        art = _artifact(verdict=DecisionVerdict.ACT, evidence_packet_id="")
        section = assemble_evidence_section(art, None)
        self.assertFalse(section.evidence_available)
        self.assertIn("Evidence unavailable", section.gap_note)


class CacheBehaviourTest(unittest.TestCase):
    @patch("analyzer.use_cases.morning_brief.build_investment_os")
    @patch("analyzer.use_cases.morning_brief.build_mis_trade_advisory")
    @patch("analyzer.use_cases.morning_brief.build_context_snapshot")
    @patch("analyzer.use_cases.morning_brief.get_cached")
    @patch("analyzer.use_cases.morning_brief.load_pinned_plans", return_value=[])
    @patch("analyzer.use_cases.morning_brief.load_intraday_prefs")
    @patch("analyzer.use_cases.morning_brief.fetch_evidence_packet_safe", return_value=None)
    def test_bundle_roundtrip(
        self, _fetch, mock_prefs, _pins, mock_get_cached, mock_ctx, mock_mis, mock_os
    ):
        snap = _snapshot()
        mock_get_cached.return_value = snap
        mock_ctx.return_value = snap
        mock_prefs.return_value = MagicMock()
        mock_mis.return_value = MisTradeAdvisory(
            verdict="NO_TRADE", emoji="⏸", headline="", summary="", score=0
        )
        mock_os.return_value = InvestmentOS()

        domain = load_morning_brief_domain(
            market="NSE",
            broker=BrokerSnapshot(state="connected"),
            use_cache=True,
        )
        bundle = domain_to_cache_bundle(domain)
        rehydrated = domain_from_cache_bundle(bundle, broker=BrokerSnapshot(state="connected"))
        vm = view_model_from_domain(rehydrated)
        self.assertEqual(vm.meta.market, "NSE")
        self.assertIsNotNone(vm.decision)


if __name__ == "__main__":
    unittest.main()
