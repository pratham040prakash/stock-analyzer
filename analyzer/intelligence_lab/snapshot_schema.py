"""Decision Snapshot schema v1 — flight recorder payload (APEX-013 E0)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from analyzer.context_engine.models import ContextSnapshot
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel

SNAPSHOT_SCHEMA_VERSION = "1"
MORNING_BRIEF_VERSION = "0.2"

# Keys that must never appear in a T0 snapshot (hindsight / E1+ fields).
HINDSIGHT_FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {
        "outcome",
        "outcome_score",
        "evaluation",
        "evaluation_score",
        "forward_return",
        "forward_returns",
        "future_price",
        "future_pnl",
        "pnl",
        "realized_pnl",
        "calibration",
        "learning",
        "learning_metadata",
        "threshold_suggestion",
        "threshold_suggestions",
        "ai_improvement",
        "alpha",
        "baseline",
        "hit_rate",
        "win",
        "loss",
        "regret",
    }
)


def new_snapshot_id() -> str:
    return str(uuid4())


def utc_created_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_decision_snapshot_payload(
    brief: MorningBriefViewModel,
    *,
    context: ContextSnapshot,
    decision_source: str,
    stale: bool,
    stale_reason: str,
    decision_engine_version: str,
    snapshot_id: str,
    created_at: str,
) -> dict[str, Any]:
    """Build versioned snapshot dict from MorningBriefViewModel at decision time only."""
    ctx = context
    session = dict(ctx.market_session or {})
    d = brief.decision

    return {
        "snapshot_id": snapshot_id,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "created_at": created_at,
        "market_session": {
            "market": brief.meta.market,
            "scenario": brief.meta.scenario,
            "session_phase": brief.meta.session_phase,
            "built_at_label": brief.meta.built_at,
            "context_snapshot_id": ctx.snapshot_id,
            "context_phase": ctx.market_phase,
            "is_open": session.get("is_open"),
            "session_date": session.get("date"),
        },
        "decision": {
            "decision_id": d.decision_id,
            "verdict": d.verdict,
            "verdict_display": d.verdict_display,
            "verdict_key": d.verdict_key,
            "decision_source": d.decision_source,
            "last_updated": d.last_updated,
            "valid_until": d.valid_until,
        },
        "confidence": {
            "level": d.confidence_level,
            "band": d.confidence_band,
        },
        "reason": d.reason,
        "mentor_message": d.reason,
        "cta": {
            "label": d.cta_label,
            "action": d.cta_action,
        },
        "best_opportunity": {
            "visible": brief.opportunity.visible,
            "symbol": brief.opportunity.symbol,
            "setup": brief.opportunity.setup,
            "lane": brief.opportunity.lane,
        },
        "risk": {
            "level": brief.risk.level,
            "warnings": list(brief.risk.warnings),
            "session_ribbon": list(brief.risk.session_ribbon),
        },
        "trust": {
            "why_this_is_recommended": brief.trust.why_this_is_recommended,
            "recommendation_confidence": brief.trust.recommendation_confidence,
            "stale": brief.trust.stale,
            "stale_label": brief.trust.stale_label,
            "gaps": list(brief.trust.gaps),
            "context_fresh": brief.trust.data_freshness.context_fresh,
            "decision_fresh": brief.trust.data_freshness.decision_fresh,
        },
        "portfolio_context": {
            "ready": brief.portfolio.ready,
            "holdings_count": brief.portfolio.holdings_count,
            "cash_available_inr": brief.portfolio.cash_available_inr,
            "tactical_pool_inr": brief.portfolio.tactical_pool_inr,
            "summary": brief.portfolio.summary,
        },
        "broker_sync_state": brief.trust.data_freshness.broker_sync_state,
        "evidence_summary": {
            "evidence_packet_id": brief.evidence.evidence_packet_id,
            "evidence_available": brief.evidence.evidence_available,
            "gap_note": brief.evidence.gap_note,
            "key_reasons": list(brief.evidence.key_reasons),
            "supporting_count": len(brief.evidence.supporting_signals),
            "conflicting_count": len(brief.evidence.conflicting_signals),
        },
        "context_summary": {
            "market_regime": ctx.market_regime,
            "market_phase": ctx.market_phase,
            "market_breadth": ctx.market_breadth,
            "risk_mode": ctx.risk_mode,
            "volatility_state": ctx.volatility_state,
            "context_hash": ctx.context_hash,
            "context_snapshot_id": ctx.snapshot_id,
            "trading_restrictions": list(ctx.trading_restrictions),
            "decision_source": decision_source,
            "stale": stale,
            "stale_reason": stale_reason,
        },
        "decision_engine_version": decision_engine_version,
        "morning_brief_version": MORNING_BRIEF_VERSION,
        "failure_message": brief.failure_message,
    }


def collect_forbidden_hindsight_keys(payload: dict[str, Any], *, prefix: str = "") -> list[str]:
    """Return dotted paths of forbidden hindsight keys found in payload."""
    found: list[str] = []
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else key
        if key in HINDSIGHT_FORBIDDEN_KEYS:
            found.append(path)
        if isinstance(value, dict):
            found.extend(collect_forbidden_hindsight_keys(value, prefix=path))
    return found
