"""APEX-013 E0 — Decision Snapshot flight recorder tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.intelligence_lab.snapshot_schema import (
    HINDSIGHT_FORBIDDEN_KEYS,
    SNAPSHOT_SCHEMA_VERSION,
    build_decision_snapshot_payload,
    collect_forbidden_hindsight_keys,
    new_snapshot_id,
    utc_created_at,
)
from analyzer.intelligence_lab.snapshot_store import (
    ImmutableSnapshotError,
    fetch_decision_snapshot,
    persist_decision_snapshot_safe,
    save_decision_snapshot,
)
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief import MorningBriefDomain, view_model_from_domain
from analyzer.use_cases.morning_brief_assembly import assemble_morning_brief_view_model
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from ui.broker.state import BrokerSnapshot


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
        snapshot_id="ctx-1",
        context_hash="hash-1",
    )


def _domain(*, decision: DecisionArtifact | None = None) -> MorningBriefDomain:
    return MorningBriefDomain(
        market="NSE",
        context=_context(),
        decision=decision,
        decision_source="equity",
        broker=BrokerSnapshot(state="connected", holdings_count=2),
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


def _trade_brief() -> MorningBriefViewModel:
    art = DecisionArtifact(
        decision_id="dec-1",
        timestamp="2026-08-05T09:00:00",
        verdict=DecisionVerdict.ACT,
        reason="RELIANCE lines up with structure and timing.",
        evidence_packet_id="ep-1",
        confidence=0.85,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        trade_allowed=True,
        decision_version="1.0",
    )
    packet = MagicMock(items=[], conflicts=[], gaps=[])
    return assemble_morning_brief_view_model(
        market="NSE",
        context=_context(),
        decision=art,
        decision_source="equity",
        broker=BrokerSnapshot(state="connected", holdings_count=2),
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
        evidence_packet=packet,
    )


class SnapshotStoreFixture(unittest.TestCase):
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


class TestSnapshotSchema(SnapshotStoreFixture):
    def test_schema_version_present(self):
        brief = _trade_brief()
        domain = _domain()
        payload = build_decision_snapshot_payload(
            brief,
            context=domain.context,
            decision_source=domain.decision_source,
            stale=domain.stale,
            stale_reason=domain.stale_reason,
            decision_engine_version="1.0",
            snapshot_id=new_snapshot_id(),
            created_at=utc_created_at(),
        )
        self.assertEqual(payload["schema_version"], SNAPSHOT_SCHEMA_VERSION)
        self.assertIn("snapshot_id", payload)
        self.assertIn("decision_engine_version", payload)
        self.assertIn("morning_brief_version", payload)

    def test_snapshot_contains_no_hindsight_fields(self):
        brief = _trade_brief()
        domain = _domain()
        payload = build_decision_snapshot_payload(
            brief,
            context=domain.context,
            decision_source=domain.decision_source,
            stale=domain.stale,
            stale_reason=domain.stale_reason,
            decision_engine_version="1.0",
            snapshot_id=new_snapshot_id(),
            created_at=utc_created_at(),
        )
        found = collect_forbidden_hindsight_keys(payload)
        self.assertEqual(found, [])
        blob = json.dumps(payload).lower()
        for key in HINDSIGHT_FORBIDDEN_KEYS:
            self.assertNotIn(f'"{key}"', blob)


class TestSnapshotImmutability(SnapshotStoreFixture):
    def test_snapshot_is_immutable(self):
        payload = {
            "snapshot_id": new_snapshot_id(),
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "created_at": utc_created_at(),
            "market_session": {"market": "NSE"},
            "decision": {"decision_id": "d1", "verdict_key": "trade"},
            "confidence": {"level": 80, "band": "high"},
            "reason": "test",
            "mentor_message": "test",
            "cta": {"label": "Go", "action": "plan"},
            "best_opportunity": {"visible": True, "symbol": "RELIANCE", "setup": "", "lane": "MIS"},
            "risk": {"level": "low", "warnings": [], "session_ribbon": []},
            "trust": {
                "why_this_is_recommended": "",
                "recommendation_confidence": "",
                "stale": False,
                "stale_label": "",
                "gaps": [],
                "context_fresh": True,
                "decision_fresh": True,
            },
            "portfolio_context": {
                "ready": True,
                "holdings_count": 2,
                "cash_available_inr": None,
                "tactical_pool_inr": None,
                "summary": "",
            },
            "broker_sync_state": "synced",
            "evidence_summary": {
                "evidence_packet_id": "ep1",
                "evidence_available": True,
                "gap_note": "",
                "key_reasons": [],
                "supporting_count": 0,
                "conflicting_count": 0,
            },
            "context_summary": {
                "market_regime": "Neutral",
                "market_phase": "regular",
                "market_breadth": "mixed",
                "risk_mode": "NEUTRAL",
                "volatility_state": "normal",
                "context_hash": "h",
                "context_snapshot_id": "c1",
                "trading_restrictions": [],
                "decision_source": "equity",
                "stale": False,
                "stale_reason": "",
            },
            "decision_engine_version": "1.0",
            "morning_brief_version": "0.2",
            "failure_message": None,
        }
        sid = save_decision_snapshot(payload)
        with self.assertRaises(ImmutableSnapshotError):
            save_decision_snapshot(payload)
        loaded = fetch_decision_snapshot(sid)
        assert loaded is not None
        self.assertEqual(loaded["snapshot_id"], sid)

    def test_snapshot_id_uniqueness(self):
        brief = _trade_brief()
        domain = _domain()
        ids: set[str] = set()
        for _ in range(3):
            sid = persist_decision_snapshot_safe(brief, domain=domain, broker=domain.broker)
            assert sid is not None
            ids.add(sid)
        self.assertEqual(len(ids), 3)


class TestSnapshotIntegration(SnapshotStoreFixture):
    def test_serialization_roundtrip(self):
        brief = _trade_brief()
        domain = _domain()
        sid = persist_decision_snapshot_safe(brief, domain=domain, broker=domain.broker)
        assert sid is not None
        loaded = fetch_decision_snapshot(sid)
        assert loaded is not None
        self.assertEqual(loaded["decision"]["verdict_key"], brief.decision.verdict_key)
        self.assertEqual(loaded["best_opportunity"]["symbol"], brief.opportunity.symbol)
        self.assertEqual(loaded["confidence"]["level"], brief.decision.confidence_level)

    def test_repeated_morning_briefs_create_independent_snapshots(self):
        brief = _trade_brief()
        domain = _domain()
        id1 = persist_decision_snapshot_safe(brief, domain=domain, broker=domain.broker)
        id2 = persist_decision_snapshot_safe(brief, domain=domain, broker=domain.broker)
        assert id1 and id2
        self.assertNotEqual(id1, id2)

    def test_cache_rehydration_does_not_record_snapshot(self):
        domain = _domain()
        with patch(
            "analyzer.intelligence_lab.snapshot_store.persist_decision_snapshot_safe"
        ) as mock_persist:
            view_model_from_domain(domain, broker=domain.broker, record_snapshot=False)
            mock_persist.assert_not_called()

    def test_persistence_failure_does_not_break_morning_brief(self):
        domain = _domain()
        with patch(
            "analyzer.intelligence_lab.snapshot_store.save_decision_snapshot",
            side_effect=RuntimeError("disk full"),
        ):
            brief = view_model_from_domain(domain, broker=domain.broker, record_snapshot=True)
        self.assertIsNotNone(brief.decision.verdict_key)


class TestProductionPathWiring(unittest.TestCase):
    def test_view_model_from_domain_supports_record_snapshot_flag(self):
        text = Path("analyzer/use_cases/decision_context_bundle.py").read_text(encoding="utf-8")
        self.assertIn("record_snapshot: bool = False", text)
        self.assertIn("persist_decision_snapshot_safe", text)

    def test_partner_data_records_on_fresh_production(self):
        text = Path("ui/components/partner_data.py").read_text(encoding="utf-8")
        self.assertIn("assemble_view_model(record_snapshot=True)", text)


if __name__ == "__main__":
    unittest.main()
