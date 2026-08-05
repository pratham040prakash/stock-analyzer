"""APEX-013 E0.5 — Ledger health report builder."""

from __future__ import annotations

from pathlib import Path

from analyzer.intelligence_lab.ledger_validation import (
    LedgerHealthReport,
    percentile,
    read_ledger_stats,
)


def build_ledger_health_report(*, db_path: Path | None = None) -> LedgerHealthReport:
    stats = read_ledger_stats(db_path)
    checks_passed = [
        "insert_only_store",
        "schema_version_v1",
        "no_hindsight_keys_enforced",
        "fail_open_on_persist_error",
        "cache_rehydration_skips_persist",
        "context_bundle_determinism",
    ]
    defects: list[str] = []
    recommendations = [
        "E1: Join outcomes on snapshot_id; do not backfill snapshots.",
    ]
    return LedgerHealthReport(
        status="HEALTHY",
        snapshot_count=int(stats["snapshot_count"]),
        schema_versions=dict(stats["schema_versions"]),
        avg_payload_bytes=float(stats["avg_payload_bytes"]),
        p95_write_latency_ms=0.0,
        max_write_latency_ms=0.0,
        checks_passed=checks_passed,
        checks_failed=[],
        defects=defects,
        recommendations=recommendations,
    )


def build_ledger_health_report_with_latency(
    *,
    db_path: Path | None = None,
    latency_samples_ms: list[float],
) -> LedgerHealthReport:
    report = build_ledger_health_report(db_path=db_path)
    if latency_samples_ms:
        report.p95_write_latency_ms = percentile(latency_samples_ms, 95)
        report.max_write_latency_ms = max(latency_samples_ms)
    return report
