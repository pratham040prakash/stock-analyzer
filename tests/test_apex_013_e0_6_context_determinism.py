"""APEX-013 E0.6 — Context determinism (eliminate context drift)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.intelligence_lab.ledger_validation import (
    build_payload_for_brief,
    snapshot_parity_mismatches,
    user_visible_from_brief,
)
from analyzer.intelligence_lab.ledger_validation import read_ledger_stats
from analyzer.intelligence_lab.snapshot_store import persist_decision_snapshot_safe
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.decision_context_bundle import CONTEXT_BUNDLE_VERSION, DecisionContextBundle
from analyzer.use_cases.morning_brief import (
    MorningBriefDomain,
    domain_from_cache_bundle,
    domain_to_cache_bundle,
    view_model_from_domain,
)
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from ui.broker.state import BrokerSnapshot
from ui.components.morning_brief_ui import load_brief_from_cache


def _context() -> ContextSnapshot:
    return ContextSnapshot(
        timestamp="2026-08-05T09:00:00+05:30",
        market_regime="Neutral",
        market_phase="regular",
        market_breadth="mixed",
        volatility_state="normal",
        liquidity_state="normal",
        market_session=MappingProxyType({"phase": "regular", "is_open": True, "date": "2026-08-05"}),
        sector_strength=MappingProxyType({}),
        industry_strength=MappingProxyType({}),
        macro_state=MappingProxyType({}),
        global_market_state=MappingProxyType({}),
        risk_mode="NEUTRAL",
        trading_restrictions=(),
        confidence=0.85,
        snapshot_id="ctx-e06",
        context_hash="hash-e06",
    )


def _trade_artifact() -> DecisionArtifact:
    return DecisionArtifact(
        decision_id="dec-e06",
        timestamp="2026-08-05T09:00:00",
        verdict=DecisionVerdict.ACT,
        reason="RELIANCE lines up.",
        evidence_packet_id="ep-e06",
        confidence=0.85,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        trade_allowed=True,
        decision_version="1.0",
    )


def _domain(*, broker: BrokerSnapshot | None = None) -> MorningBriefDomain:
    return MorningBriefDomain(
        market="NSE",
        context=_context(),
        decision=_trade_artifact(),
        decision_source="equity",
        broker=broker or BrokerSnapshot(state="connected", holdings_count=2),
        mis=MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
        os_report=InvestmentOS(starred_symbol="RELIANCE", next_step="Buy above ₹2,850"),
        pins=[],
        prefs=IntradayPrefs(capital=100_000, max_risk_pct=1.8),
        built_at="09:12 IST",
        scenario=MorningBriefScenario.NORMAL,
        stale=False,
        stale_reason="",
        context_from_cache=False,
        context_cache_age=None,
        data_error="",
    )


class ContextDeterminismFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name) / "decision_snapshots.db"
        self.path_patch = patch(
            "analyzer.intelligence_lab.snapshot_store.snapshot_store_path",
            return_value=self.store,
        )
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.addCleanup(self.tmp.cleanup)

        self.evidence_patch = patch(
            "analyzer.use_cases.decision_context_bundle.fetch_evidence_packet_safe",
            return_value=MagicMock(items=[], conflicts=[], gaps=[]),
        )
        self.evidence_patch.start()
        self.addCleanup(self.evidence_patch.stop)


class TestContextBundleDeterminism(ContextDeterminismFixture):
    """Same frozen context → same view model → same snapshot → same UI projection."""

    def test_same_bundle_produces_identical_view_models(self):
        domain = _domain()
        ctx = DecisionContextBundle.freeze(domain)
        brief_a = ctx.assemble_view_model()
        brief_b = ctx.assemble_view_model()
        self.assertEqual(brief_a.decision.verdict_key, brief_b.decision.verdict_key)
        self.assertEqual(brief_a.decision.verdict_display, brief_b.decision.verdict_display)

    def test_snapshot_matches_display_from_same_bundle(self):
        domain = _domain()
        ctx = DecisionContextBundle.freeze(domain)
        brief = ctx.assemble_view_model(record_snapshot=True)
        display = DecisionContextBundle.from_cache_dict(ctx.to_cache_dict()).assemble_view_model()
        self.assertEqual(
            user_visible_from_brief(brief),
            user_visible_from_brief(display),
        )

    def test_cache_bundle_includes_context_version(self):
        domain = _domain()
        bundle = domain_to_cache_bundle(domain)
        self.assertEqual(bundle["_context_bundle_version"], CONTEXT_BUNDLE_VERSION)
        self.assertIn("broker", bundle)


class TestBrokerReconnectImmunity(ContextDeterminismFixture):
    """Broker reconnect/disconnect after snapshot must not change historical decision."""

    def test_broker_reconnect_does_not_change_display(self):
        domain = _domain(broker=BrokerSnapshot(state="connected", holdings_count=2))
        production = view_model_from_domain(domain, record_snapshot=True)
        bundle = domain_to_cache_bundle(domain)
        live = BrokerSnapshot(state="not_configured")
        display = load_brief_from_cache(bundle, broker=live)
        self.assertEqual(
            user_visible_from_brief(production)["verdict_key"],
            user_visible_from_brief(display)["verdict_key"],
        )

    def test_broker_disconnect_does_not_change_snapshot(self):
        domain = _domain(broker=BrokerSnapshot(state="connected", holdings_count=2))
        brief = view_model_from_domain(domain, record_snapshot=True)
        stats_before = read_ledger_stats(self.store)
        load_brief_from_cache(
            domain_to_cache_bundle(domain),
            broker=BrokerSnapshot(state="disconnected"),
        )
        stats_after = read_ledger_stats(self.store)
        self.assertEqual(stats_before, stats_after)
        self.assertEqual(stats_before["snapshot_count"], 1)

    def test_domain_from_cache_ignores_live_broker(self):
        domain = _domain(broker=BrokerSnapshot(state="connected", holdings_count=2))
        bundle = domain_to_cache_bundle(domain)
        rehydrated = domain_from_cache_bundle(
            bundle, broker=BrokerSnapshot(state="not_configured")
        )
        self.assertEqual(rehydrated.broker.state, "connected")


class TestCacheReloadNoDrift(ContextDeterminismFixture):
    """Cache reload uses frozen context — no drift."""

    def test_ten_rehydrations_identical(self):
        domain = _domain()
        bundle = domain_to_cache_bundle(domain)
        baseline = user_visible_from_brief(load_brief_from_cache(bundle))
        for _ in range(10):
            reloaded = user_visible_from_brief(
                load_brief_from_cache(bundle, broker=BrokerSnapshot(state="not_configured"))
            )
            self.assertEqual(baseline, reloaded)


class TestSingleAssemblyPath(ContextDeterminismFixture):
    """No duplicate assembly paths introduced."""

    def test_view_model_from_domain_delegates_to_context_bundle(self):
        text = Path("analyzer/use_cases/morning_brief.py").read_text(encoding="utf-8")
        self.assertIn("DecisionContextBundle.freeze(domain).assemble_view_model", text)
        self.assertNotIn("if broker_snap.to_dict() != domain.broker.to_dict():", text)

    def test_domain_from_cache_no_broker_recompute(self):
        text = Path("analyzer/use_cases/morning_brief.py").read_text(encoding="utf-8")
        self.assertNotIn("if broker_snap.to_dict() != bundle.get(\"_broker_at_build\"):", text)

    def test_ui_does_not_own_persistence(self):
        text = Path("ui/components/home_dashboard.py").read_text(encoding="utf-8")
        self.assertNotIn("record_snapshot=True", text)
        self.assertNotIn("persist_decision_snapshot", text)

    def test_partner_data_persists_in_application_layer(self):
        text = Path("ui/components/partner_data.py").read_text(encoding="utf-8")
        self.assertIn("DecisionContextBundle.freeze", text)
        self.assertIn("assemble_view_model(record_snapshot=True)", text)
        self.assertIn("load_morning_brief_domain", text)


class TestSnapshotParityAfterE06(ContextDeterminismFixture):
    def test_persisted_snapshot_matches_frozen_display(self):
        domain = _domain()
        brief = view_model_from_domain(domain, record_snapshot=True)
        display = load_brief_from_cache(domain_to_cache_bundle(domain))
        payload = build_payload_for_brief(brief, domain=domain)
        self.assertEqual(snapshot_parity_mismatches(brief, payload), [])
        self.assertEqual(
            user_visible_from_brief(brief),
            user_visible_from_brief(display),
        )


if __name__ == "__main__":
    unittest.main()
