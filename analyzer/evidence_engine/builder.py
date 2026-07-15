"""Build EvidenceItem instances with stable IDs and defaults."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.evidence_engine.models import (
    EvidenceCategory,
    EvidenceConfidence,
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
)

IST = ZoneInfo("Asia/Kolkata")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.strip().lower())
    return s.strip("_")[:48] or "item"


def evidence_item_id(category: EvidenceCategory, label: str, *, suffix: str = "") -> str:
    base = f"{category.value}:{_slug(label)}"
    if suffix:
        return f"{base}:{suffix}"
    digest = hashlib.sha256(base.encode()).hexdigest()[:8]
    return f"{base}:{digest}"


class EvidenceBuilder:
    """Factory for validated EvidenceItem construction."""

    def __init__(self, *, default_source: EvidenceSource = EvidenceSource.INTERNAL_MODEL):
        self._default_source = default_source
        self._seq = 0

    def build(
        self,
        *,
        category: EvidenceCategory,
        label: str,
        type: EvidenceType,
        value: str | float | bool | int | None,
        explanation: str,
        source: EvidenceSource | str | None = None,
        confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM,
        weight: float = 1.0,
        timestamp: str | None = None,
        item_id: str | None = None,
        metadata: dict | None = None,
    ) -> EvidenceItem:
        self._seq += 1
        ts = timestamp or datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        src = source or self._default_source
        return EvidenceItem(
            id=item_id or evidence_item_id(category, label, suffix=str(self._seq)),
            category=category,
            source=src,
            timestamp=ts,
            label=label,
            type=type,
            value=value,
            confidence=confidence,
            weight=max(0.0, min(weight, 10.0)),
            explanation=explanation.strip(),
            metadata=dict(metadata or {}),
        )

    def gap(
        self,
        *,
        category: EvidenceCategory,
        label: str,
        explanation: str,
        source: EvidenceSource | str = EvidenceSource.UNKNOWN,
        weight: float = 0.5,
        metadata: dict | None = None,
    ) -> EvidenceItem:
        return self.build(
            category=category,
            label=label,
            type=EvidenceType.GAP,
            value=None,
            explanation=explanation,
            source=source,
            confidence=EvidenceConfidence.NONE,
            weight=weight,
            metadata=metadata,
        )

    def fact(
        self,
        *,
        category: EvidenceCategory,
        label: str,
        value: str | float | bool | int,
        explanation: str,
        source: EvidenceSource | str,
        confidence: EvidenceConfidence = EvidenceConfidence.HIGH,
        weight: float = 1.0,
        metadata: dict | None = None,
    ) -> EvidenceItem:
        return self.build(
            category=category,
            label=label,
            type=EvidenceType.FACT,
            value=value,
            explanation=explanation,
            source=source,
            confidence=confidence,
            weight=weight,
            metadata=metadata,
        )

    def estimate(
        self,
        *,
        category: EvidenceCategory,
        label: str,
        value: str | float | bool | int | None,
        explanation: str,
        source: EvidenceSource | str = EvidenceSource.INTERNAL_MODEL,
        confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM,
        weight: float = 1.0,
        metadata: dict | None = None,
    ) -> EvidenceItem:
        return self.build(
            category=category,
            label=label,
            type=EvidenceType.ESTIMATE,
            value=value,
            explanation=explanation,
            source=source,
            confidence=confidence,
            weight=weight,
            metadata=metadata,
        )

    def opinion(
        self,
        *,
        category: EvidenceCategory,
        label: str,
        value: str,
        explanation: str,
        source: EvidenceSource | str = EvidenceSource.INTERNAL_MODEL,
        confidence: EvidenceConfidence = EvidenceConfidence.LOW,
        weight: float = 0.8,
        metadata: dict | None = None,
    ) -> EvidenceItem:
        return self.build(
            category=category,
            label=label,
            type=EvidenceType.OPINION,
            value=value,
            explanation=explanation,
            source=source,
            confidence=confidence,
            weight=weight,
            metadata=metadata,
        )
