"""APEX-013 E0.5 — Decision Snapshot ledger validation sprint."""

from __future__ import annotations

import logging
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
    estimate_payload_bytes,
    measure_write_latency_ms,
    percentile,
    read_ledger_stats,
    snapshot_parity_mismatches,
    user_visible_from_brief,
    user_visible_from_snapshot,
)
from analyzer.intelligence_lab.snapshot_store import (
    ImmutableSnapshotError,
    fetch_decision_snapshot,
    persist_decision_snapshot_safe,
    save_decision_snapshot,
)
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief import (
    MorningBriefDomain,
    domain_from_cache_bundle,
    domain_to_cache_bundle,
    view_model_from_domain,
)
from analyzer.use_cases.morning_brief_assembly import assemble_morning_brief_view_model
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
        snapshot_id="ctx-prod-1",
        context_hash="hash-prod-1",
    )


def _domain(*, broker: BrokerSnapshot | None = None, decision: DecisionArtifact | None = None) -> MorningBriefDomain:
    return MorningBriefDomain(
        market="NSE",
        context=_context(),
        decision=decision,
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


def _trade_artifact() -> DecisionArtifact:
    return DecisionArtifact(
        decision_id="dec-prod-1",
        timestamp="2026-08-05T09:00:00",
        verdict=DecisionVerdict.ACT,
        reason="RELIANCE lines up with structure and timing.",
        evidence_packet_id="ep-prod-1",
        confidence=0.85,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        trade_allowed=True,
        decision_version="1.0",
    )


def _assemble_brief(domain: MorningBriefDomain):
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
    return assemble_morning_brief_view_model(
        market=domain.market,
        context=domain.context,
        decision=domain.decision,
        decision_source=domain.decision_source,
        broker=domain.broker,
        mis=domain.mis,
        os_report=domain.os_report,
        pins=domain.pins,
        prefs=domain.prefs,
        built_at=domain.built_at,
        scenario=domain.scenario,
        stale=domain.stale,
        stale_reason=domain.stale_reason,
        context_from_cache=domain.context_from_cache,
        context_cache_age=domain.context_cache_age,
        data_error=domain.data_error,
        evidence_packet=packet,
    )


class LedgerValidationFixture(unittest.TestCase):
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


class TestOneSnapshotPerProduction(LedgerValidationFixture):
    """Objective 1: exactly one snapshot per production Morning Brief."""

    def test_streamlit_production_then_rehydrate_records_once(self):
        domain = _domain(decision=_trade_artifact())
        bundle = domain_to_cache_bundle(domain)
        with patch(
            "analyzer.intelligence_lab.snapshot_store.persist_decision_snapshot_safe",
            wraps=persist_decision_snapshot_safe,
        ) as mock_persist:
            view_model_from_domain(domain, broker=domain.broker, record_snapshot=True)
            for _ in range(5):
                load_brief_from_cache(bundle, broker=domain.broker)
                view_model_from_domain(
                    domain_from_cache_bundle(bundle, broker=domain.broker),
                    broker=domain.broker,
                    record_snapshot=False,
                )
            self.assertEqual(mock_persist.call_count, 1)

    def test_build_morning_brief_path_records_once_per_call(self):
        domain = _domain(decision=_trade_artifact())
        with patch(
            "analyzer.intelligence_lab.snapshot_store.persist_decision_snapshot_safe",
            wraps=persist_decision_snapshot_safe,
        ) as mock_persist:
            view_model_from_domain(domain, broker=domain.broker, record_snapshot=True)
            self.assertEqual(mock_persist.call_count, 1)
            rows = read_ledger_stats(self.store)
            self.assertEqual(rows["snapshot_count"], 1)


class TestCacheRehydrationNeverRecords(LedgerValidationFixture):
    """Objective 2: cache rehydration never creates snapshots."""

    def test_load_brief_from_cache_never_persists(self):
        domain = _domain(decision=_trade_artifact())
        bundle = domain_to_cache_bundle(domain)
        with patch("analyzer.intelligence_lab.snapshot_store.persist_decision_snapshot_safe") as mock_persist:
            for _ in range(10):
                load_brief_from_cache(bundle, broker=domain.broker)
            mock_persist.assert_not_called()

    def test_view_model_without_flag_never_persists(self):
        domain = _domain(decision=_trade_artifact())
        with patch("analyzer.intelligence_lab.snapshot_store.persist_decision_snapshot_safe") as mock_persist:
            view_model_from_domain(domain, broker=domain.broker, record_snapshot=False)
            view_model_from_domain(domain, broker=domain.broker)
            mock_persist.assert_not_called()


class TestSnapshotImmutability(LedgerValidationFixture):
    """Objective 3: snapshot immutability."""

    def test_duplicate_snapshot_id_rejected(self):
        domain = _domain(decision=_trade_artifact())
        brief = _assemble_brief(domain)
        payload = build_payload_for_brief(brief, domain=domain, snapshot_id="fixed-id")
        save_decision_snapshot(payload)
        with self.assertRaises(ImmutableSnapshotError):
            save_decision_snapshot(payload)

    def test_no_update_path_in_store(self):
        text = Path("analyzer/intelligence_lab/snapshot_store.py").read_text(encoding="utf-8")
        self.assertNotIn("UPDATE decision_snapshots", text)
        self.assertNotIn("INSERT OR REPLACE", text)


class TestSnapshotUserParity(LedgerValidationFixture):
    """Objective 4: snapshot matches Morning Brief shown to user (same assembly)."""

    def test_snapshot_matches_decision_card_when_same_brief(self):
        domain = _domain(decision=_trade_artifact())
        brief = _assemble_brief(domain)
        payload = build_payload_for_brief(brief, domain=domain)
        self.assertEqual(snapshot_parity_mismatches(brief, payload), [])

    def test_persisted_snapshot_matches_user_visible_fields(self):
        domain = _domain(decision=_trade_artifact())
        brief = _assemble_brief(domain)
        sid = persist_decision_snapshot_safe(brief, domain=domain, broker=domain.broker)
        assert sid is not None
        loaded = fetch_decision_snapshot(sid)
        assert loaded is not None
        self.assertEqual(snapshot_parity_mismatches(brief, loaded), [])

    def test_broker_reconnect_after_snapshot_does_not_change_display(self):
        """E0.6: live broker changes must not alter frozen Morning Brief."""
        domain = _domain(
            decision=_trade_artifact(),
            broker=BrokerSnapshot(state="connected", holdings_count=2),
        )
        production_brief = view_model_from_domain(
            domain, broker=domain.broker, record_snapshot=True
        )
        self.assertEqual(read_ledger_stats(self.store)["snapshot_count"], 1)

        disconnected = BrokerSnapshot(state="not_configured")
        bundle = domain_to_cache_bundle(domain)
        display_brief = load_brief_from_cache(bundle, broker=disconnected)

        self.assertEqual(
            user_visible_from_brief(production_brief)["verdict_key"],
            user_visible_from_brief(display_brief)["verdict_key"],
        )


class TestLatencyAndStorage(LedgerValidationFixture):
    """Objectives 5: write latency and storage growth."""

    def test_write_latency_within_budget(self):
        domain = _domain(decision=_trade_artifact())
        brief = _assemble_brief(domain)
        samples = measure_write_latency_ms(brief, domain=domain, broker=domain.broker, iterations=30)
        p95 = percentile(samples, 95)
        self.assertLess(p95, 250.0, f"p95 write latency {p95:.2f}ms exceeds 250ms budget")

    def test_storage_per_snapshot_bounded(self):
        domain = _domain(decision=_trade_artifact())
        brief = _assemble_brief(domain)
        payload = build_payload_for_brief(brief, domain=domain)
        size = estimate_payload_bytes(payload)
        self.assertGreater(size, 500)
        self.assertLess(size, 16_384, f"payload {size} bytes exceeds 16KB sanity bound")


class TestFailOpen(LedgerValidationFixture):
    """Objective 6: fail-open under persistence failures."""

    def test_persist_failure_returns_none_and_brief_succeeds(self):
        domain = _domain(decision=_trade_artifact())
        with patch(
            "analyzer.intelligence_lab.snapshot_store.save_decision_snapshot",
            side_effect=OSError("disk full"),
        ):
            brief = view_model_from_domain(domain, broker=domain.broker, record_snapshot=True)
        self.assertIsNotNone(brief.decision.verdict_key)
        self.assertEqual(read_ledger_stats(self.store)["snapshot_count"], 0)

    def test_persist_failure_logs_exception(self):
        domain = _domain(decision=_trade_artifact())
        with patch(
            "analyzer.intelligence_lab.snapshot_store.save_decision_snapshot",
            side_effect=RuntimeError("locked"),
        ), self.assertLogs("analyzer.intelligence_lab.snapshot_store", level="ERROR") as logs:
            view_model_from_domain(domain, broker=domain.broker, record_snapshot=True)
        self.assertTrue(any("snapshot persist failed" in m for m in logs.output))


class TestLedgerHealthReport(LedgerValidationFixture):
    """Objective 7: ledger health report generation."""

    def test_health_report_structure(self):
        from analyzer.intelligence_lab.ledger_health import build_ledger_health_report

        domain = _domain(decision=_trade_artifact())
        brief = _assemble_brief(domain)
        for _ in range(5):
            persist_decision_snapshot_safe(brief, domain=domain, broker=domain.broker)
        report = build_ledger_health_report(db_path=self.store)
        self.assertEqual(report.status, "HEALTHY")
        self.assertEqual(report.snapshot_count, 5)
        self.assertIn("1", report.schema_versions)
        self.assertGreater(report.avg_payload_bytes, 0)
        self.assertGreater(len(report.checks_passed), 0)


if __name__ == "__main__":
    unittest.main()
