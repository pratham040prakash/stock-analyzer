"""JSON serialization for DecisionArtifact."""

from __future__ import annotations

import json
import logging
from typing import Any

from analyzer.decision_engine.models import (
    DecisionArtifact,
    DecisionExplainability,
    DecisionVerdict,
    UncertaintyVector,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2


def _enum_val(val) -> str:
    return val.value if hasattr(val, "value") else str(val)


def uncertainty_to_dict(u: UncertaintyVector) -> dict[str, float]:
    return u.as_dict()


def uncertainty_from_dict(data: dict[str, Any]) -> UncertaintyVector:
    return UncertaintyVector(
        evidence_completeness=float(data.get("evidence_completeness", 0)),
        conflict_level=float(data.get("conflict_level", 0)),
        data_quality=float(data.get("data_quality", 0)),
        regime_risk=float(data.get("regime_risk", 0)),
        capital_headroom=float(data.get("capital_headroom", 0)),
        overall=float(data.get("overall", 0)),
    )


def explainability_to_dict(e: DecisionExplainability | None) -> dict[str, str] | None:
    if e is None:
        return None
    return {"why": e.why, "why_now": e.why_now, "why_not": e.why_not}


def explainability_from_dict(data: dict[str, Any] | None) -> DecisionExplainability | None:
    if not data:
        return None
    return DecisionExplainability(
        why=str(data.get("why", "")),
        why_now=str(data.get("why_now", "")),
        why_not=str(data.get("why_not", "")),
    )


def decision_artifact_to_dict(artifact: DecisionArtifact) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "decision_id": artifact.decision_id,
        "timestamp": artifact.timestamp,
        "verdict": _enum_val(artifact.verdict),
        "reason": artifact.reason,
        "evidence_packet_id": artifact.evidence_packet_id,
        "confidence": artifact.confidence,
        "uncertainty": uncertainty_to_dict(artifact.uncertainty),
        "capital_recommendation": artifact.capital_recommendation,
        "execution_recommendation": artifact.execution_recommendation,
        "supporting_evidence_ids": artifact.supporting_evidence_ids,
        "conflicting_evidence_ids": artifact.conflicting_evidence_ids,
        "alternative_actions": artifact.alternative_actions,
        "invalidation_conditions": artifact.invalidation_conditions,
        "explainability": explainability_to_dict(artifact.explainability),
        "decision_version": artifact.decision_version,
        "subject": artifact.subject,
        "subject_type": artifact.subject_type,
        "trade_allowed": artifact.trade_allowed,
        "net_score": artifact.net_score,
        "metadata": artifact.metadata,
    }


def decision_artifact_from_dict(data: dict[str, Any]) -> DecisionArtifact:
    if not data.get("decision_id"):
        raise ValueError("DecisionArtifact missing decision_id")
    try:
        verdict = DecisionVerdict(data.get("verdict", "WAIT"))
    except ValueError:
        logger.warning("invalid verdict %r — default WAIT", data.get("verdict"))
        verdict = DecisionVerdict.WAIT
    return DecisionArtifact(
        decision_id=str(data["decision_id"]),
        timestamp=str(data.get("timestamp", "")),
        verdict=verdict,
        reason=str(data.get("reason", "")),
        evidence_packet_id=str(data.get("evidence_packet_id", "")),
        confidence=float(data.get("confidence", 0)),
        uncertainty=uncertainty_from_dict(data.get("uncertainty") or {}),
        capital_recommendation=str(data.get("capital_recommendation", "")),
        execution_recommendation=str(data.get("execution_recommendation", "")),
        supporting_evidence_ids=[str(x) for x in (data.get("supporting_evidence_ids") or [])],
        conflicting_evidence_ids=[str(x) for x in (data.get("conflicting_evidence_ids") or [])],
        alternative_actions=[str(x) for x in (data.get("alternative_actions") or [])],
        invalidation_conditions=[str(x) for x in (data.get("invalidation_conditions") or [])],
        explainability=explainability_from_dict(data.get("explainability")),
        decision_version=str(data.get("decision_version", "1.0")),
        subject=str(data.get("subject", "")),
        subject_type=str(data.get("subject_type", "equity")),
        trade_allowed=bool(data.get("trade_allowed", False)),
        net_score=float(data.get("net_score", 0)),
        metadata=dict(data.get("metadata") or {}),
    )


def decision_artifact_to_json(artifact: DecisionArtifact, *, indent: int | None = None) -> str:
    return json.dumps(decision_artifact_to_dict(artifact), ensure_ascii=False, indent=indent)


def decision_artifact_from_json(raw: str) -> DecisionArtifact:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid decision JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Decision JSON must be an object")
    return decision_artifact_from_dict(data)
