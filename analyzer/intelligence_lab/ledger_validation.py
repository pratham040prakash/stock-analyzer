"""APEX-013 E0.5 — Ledger validation helpers (no outcome scoring)."""

from __future__ import annotations

import json
import sqlite3
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from analyzer.intelligence_lab.snapshot_schema import build_decision_snapshot_payload
from analyzer.intelligence_lab.snapshot_store import persist_decision_snapshot_safe, snapshot_store_path
from analyzer.use_cases.morning_brief import MorningBriefDomain
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from ui.broker.state import BrokerSnapshot
from ui.components.decision_card import project_decision_card


@dataclass
class LedgerHealthReport:
    """Validation summary for CTO review — E0.5 only."""

    status: str
    snapshot_count: int
    schema_versions: dict[str, int]
    avg_payload_bytes: float
    p95_write_latency_ms: float
    max_write_latency_ms: float
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "snapshot_count": self.snapshot_count,
            "schema_versions": self.schema_versions,
            "avg_payload_bytes": round(self.avg_payload_bytes, 1),
            "p95_write_latency_ms": round(self.p95_write_latency_ms, 3),
            "max_write_latency_ms": round(self.max_write_latency_ms, 3),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "defects": self.defects,
            "recommendations": self.recommendations,
        }


def user_visible_from_brief(brief: MorningBriefViewModel) -> dict[str, Any]:
    """Fields the Today hero surfaces via DecisionCardViewModel."""
    card = project_decision_card(brief)
    opp = card.best_opportunity
    return {
        "verdict_display": card.verdict_word,
        "verdict_key": card.verdict_key,
        "reason": card.reason,
        "confidence_level": card.confidence_level,
        "confidence_band": card.confidence_band,
        "cta_label": card.cta_label,
        "cta_action": card.cta_action,
        "opportunity_visible": bool(opp and opp.visible),
        "opportunity_symbol": opp.symbol if opp else "",
        "opportunity_setup": opp.setup if opp else "",
        "risk_level": card.risk_level,
        "failure_message": card.failure_message,
        "stale": card.stale,
        "stale_label": card.stale_label,
        "scenario": card.scenario,
        "trust_summary": card.trust_summary,
        "decision_id": brief.decision.decision_id,
        "decision_verdict": card.decision_verdict,
    }


def user_visible_from_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """User-visible slice reconstructed from a stored snapshot payload."""
    decision = payload.get("decision") or {}
    opp = payload.get("best_opportunity") or {}
    trust = payload.get("trust") or {}
    confidence = payload.get("confidence") or {}
    cta = payload.get("cta") or {}
    return {
        "verdict_display": decision.get("verdict_display"),
        "verdict_key": decision.get("verdict_key"),
        "reason": payload.get("reason"),
        "confidence_level": confidence.get("level"),
        "confidence_band": confidence.get("band"),
        "cta_label": cta.get("label"),
        "cta_action": cta.get("action"),
        "opportunity_visible": bool(opp.get("visible")),
        "opportunity_symbol": opp.get("symbol") or "",
        "opportunity_setup": opp.get("setup") or "",
        "risk_level": (payload.get("risk") or {}).get("level"),
        "failure_message": payload.get("failure_message"),
        "stale": trust.get("stale"),
        "stale_label": trust.get("stale_label"),
        "scenario": (payload.get("market_session") or {}).get("scenario"),
        "trust_summary": trust.get("why_this_is_recommended"),
        "decision_id": decision.get("decision_id"),
        "decision_verdict": decision.get("verdict"),
    }


def snapshot_parity_mismatches(
    brief: MorningBriefViewModel,
    payload: dict[str, Any],
) -> list[str]:
    """Return human-readable mismatches between brief and snapshot user-visible fields."""
    visible = user_visible_from_brief(brief)
    stored = user_visible_from_snapshot(payload)
    mismatches: list[str] = []
    for key in visible:
        if visible[key] != stored.get(key):
            mismatches.append(f"{key}: brief={visible[key]!r} snapshot={stored.get(key)!r}")
    return mismatches


def build_payload_for_brief(
    brief: MorningBriefViewModel,
    *,
    domain: MorningBriefDomain,
    snapshot_id: str = "validation-id",
    created_at: str = "2026-08-05T09:00:00+00:00",
) -> dict[str, Any]:
    from analyzer.decision_engine.models import DECISION_VERSION

    return build_decision_snapshot_payload(
        brief,
        context=domain.context,
        decision_source=domain.decision_source,
        stale=domain.stale,
        stale_reason=domain.stale_reason,
        decision_engine_version=(
            domain.decision.decision_version if domain.decision else DECISION_VERSION
        ),
        snapshot_id=snapshot_id,
        created_at=created_at,
    )


def measure_write_latency_ms(
    brief: MorningBriefViewModel,
    *,
    domain: MorningBriefDomain,
    broker: BrokerSnapshot,
    iterations: int = 50,
) -> list[float]:
    """Wall-clock latency samples for persist_decision_snapshot_safe."""
    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        persist_decision_snapshot_safe(brief, domain=domain, broker=broker)
        samples.append((time.perf_counter() - start) * 1000.0)
    return samples


def estimate_payload_bytes(payload: dict[str, Any]) -> int:
    return len(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def read_ledger_stats(db_path: Path | None = None) -> dict[str, Any]:
    path = db_path or snapshot_store_path()
    if not path.is_file():
        return {"snapshot_count": 0, "schema_versions": {}, "avg_payload_bytes": 0.0}

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT schema_version, payload_json FROM decision_snapshots"
        ).fetchall()
    except sqlite3.Error:
        return {"snapshot_count": 0, "schema_versions": {}, "avg_payload_bytes": 0.0}
    finally:
        conn.close()

    versions: dict[str, int] = {}
    sizes: list[int] = []
    for row in rows:
        ver = str(row["schema_version"])
        versions[ver] = versions.get(ver, 0) + 1
        sizes.append(len(str(row["payload_json"]).encode("utf-8")))

    count = len(rows)
    avg_size = sum(sizes) / count if count else 0.0
    return {
        "snapshot_count": count,
        "schema_versions": versions,
        "avg_payload_bytes": avg_size,
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[max(0, min(idx, len(ordered) - 1))]
