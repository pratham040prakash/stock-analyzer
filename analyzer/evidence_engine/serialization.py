"""JSON serialization for EvidencePacket and EvidenceItem."""

from __future__ import annotations

import json
import logging
from typing import Any

from analyzer.evidence_engine.models import (
    EvidenceCategory,
    EvidenceConfidence,
    EvidenceConflict,
    EvidenceItem,
    EvidencePacket,
    EvidenceSource,
    EvidenceType,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


def _enum_val(val) -> str:
    return val.value if hasattr(val, "value") else str(val)


def _parse_enum(enum_cls, raw, default):
    try:
        return enum_cls(raw)
    except (ValueError, TypeError):
        logger.warning("evidence: invalid %s value %r — using %s", enum_cls.__name__, raw, default)
        return default


def _parse_source(raw: str) -> EvidenceSource | str:
    try:
        return EvidenceSource(raw)
    except ValueError:
        return raw


def evidence_item_to_dict(item: EvidenceItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "category": _enum_val(item.category),
        "source": _enum_val(item.source),
        "timestamp": item.timestamp,
        "label": item.label,
        "type": _enum_val(item.type),
        "value": item.value,
        "confidence": _enum_val(item.confidence),
        "weight": item.weight,
        "explanation": item.explanation,
        "metadata": item.metadata,
    }


def evidence_item_from_dict(data: dict[str, Any]) -> EvidenceItem:
    if not data.get("id"):
        raise ValueError("EvidenceItem missing required field: id")
    return EvidenceItem(
        id=str(data["id"]),
        category=_parse_enum(EvidenceCategory, data.get("category"), EvidenceCategory.TECHNICAL),
        source=_parse_source(str(data.get("source", "unknown"))),
        timestamp=str(data.get("timestamp", "")),
        label=str(data.get("label", "")),
        type=_parse_enum(EvidenceType, data.get("type"), EvidenceType.GAP),
        value=data.get("value"),
        confidence=_parse_enum(EvidenceConfidence, data.get("confidence"), EvidenceConfidence.NONE),
        weight=float(data.get("weight", 1.0)),
        explanation=str(data.get("explanation", "")),
        metadata=dict(data.get("metadata") or {}),
    )


def evidence_conflict_to_dict(conflict: EvidenceConflict) -> dict[str, Any]:
    return {
        "id": conflict.id,
        "category": _enum_val(conflict.category),
        "item_ids": conflict.item_ids,
        "description": conflict.description,
        "severity": conflict.severity,
    }


def evidence_conflict_from_dict(data: dict[str, Any]) -> EvidenceConflict:
    if not data.get("id"):
        raise ValueError("EvidenceConflict missing required field: id")
    return EvidenceConflict(
        id=str(data["id"]),
        category=_parse_enum(EvidenceCategory, data.get("category"), EvidenceCategory.TECHNICAL),
        item_ids=[str(x) for x in (data.get("item_ids") or [])],
        description=str(data.get("description", "")),
        severity=str(data.get("severity", "low")),
    )


def evidence_packet_to_dict(packet: EvidencePacket) -> dict[str, Any]:
    gap_items = [i for i in packet.items if i.type == EvidenceType.GAP]
    return {
        "schema_version": SCHEMA_VERSION,
        "packet_id": packet.packet_id,
        "subject": packet.subject,
        "subject_type": packet.subject_type,
        "created_at": packet.created_at,
        "items": [evidence_item_to_dict(i) for i in packet.items],
        "conflicts": [evidence_conflict_to_dict(c) for c in packet.conflicts],
        "gaps": [evidence_item_to_dict(g) for g in gap_items],
        "completeness_pct": packet.completeness_pct,
        "categories_present": packet.categories_present,
        "metadata": packet.metadata,
    }


def _derive_gaps(items: list[EvidenceItem], raw_gaps: list[dict[str, Any]] | None) -> list[EvidenceItem]:
    from_items = [i for i in items if i.type == EvidenceType.GAP]
    if from_items:
        return from_items
    if not raw_gaps:
        return []
    return [evidence_item_from_dict(g) for g in raw_gaps]


def evidence_packet_from_dict(data: dict[str, Any]) -> EvidencePacket:
    if not data.get("packet_id"):
        raise ValueError("EvidencePacket missing required field: packet_id")
    items = [evidence_item_from_dict(i) for i in (data.get("items") or [])]
    gaps = _derive_gaps(items, data.get("gaps"))
    return EvidencePacket(
        packet_id=str(data["packet_id"]),
        subject=str(data.get("subject", "")),
        subject_type=str(data.get("subject_type", "equity")),
        created_at=str(data.get("created_at", "")),
        items=items,
        conflicts=[evidence_conflict_from_dict(c) for c in (data.get("conflicts") or [])],
        gaps=gaps,
        completeness_pct=float(data.get("completeness_pct", 0)),
        categories_present=[str(x) for x in (data.get("categories_present") or [])],
        metadata=dict(data.get("metadata") or {}),
    )


def evidence_packet_to_json(packet: EvidencePacket, *, indent: int | None = None) -> str:
    return json.dumps(evidence_packet_to_dict(packet), ensure_ascii=False, indent=indent)


def evidence_packet_from_json(raw: str) -> EvidencePacket:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid evidence packet JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Evidence packet JSON must be an object")
    return evidence_packet_from_dict(data)
