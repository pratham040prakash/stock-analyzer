"""Validate evidence items — unknown must never become FACT."""

from __future__ import annotations

import logging
from dataclasses import replace

from analyzer.evidence_engine.models import (
    EvidenceConfidence,
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
)

logger = logging.getLogger(__name__)

TRUSTED_FACT_SOURCES = {
    EvidenceSource.YAHOO_FINANCE,
    EvidenceSource.KITE,
    EvidenceSource.NSE,
    EvidenceSource.SCREENER,
    EvidenceSource.DATA_HEALTH,
    EvidenceSource.NEWS_FEED,
    EvidenceSource.MACRO_FEED,
}

_UNTRUSTED_SOURCES = {EvidenceSource.UNKNOWN, EvidenceSource.COACH, EvidenceSource.USER}


class EvidenceValidator:
    """Enforce labeling rules before items enter a packet."""

    def validate(self, item: EvidenceItem) -> EvidenceItem:
        item = self._normalize_source(item)
        item = self._enforce_fact_rules(item)
        item = self._enforce_gap_rules(item)
        item = self._ensure_explanation(item)
        return item

    def validate_many(self, items: list[EvidenceItem]) -> list[EvidenceItem]:
        return [self.validate(i) for i in items]

    def _normalize_source(self, item: EvidenceItem) -> EvidenceItem:
        src = item.source
        if isinstance(src, str):
            try:
                return replace(item, source=EvidenceSource(src))
            except ValueError:
                return item
        return item

    def _enforce_fact_rules(self, item: EvidenceItem) -> EvidenceItem:
        if item.type != EvidenceType.FACT:
            return item

        src = item.source
        if isinstance(src, str):
            try:
                src = EvidenceSource(src)
            except ValueError:
                logger.info("evidence: downgrade FACT — unrecognized source %s", src)
                return replace(item, type=EvidenceType.ESTIMATE, confidence=EvidenceConfidence.LOW)

        if src in _UNTRUSTED_SOURCES:
            logger.info("evidence: downgrade FACT — untrusted source %s", src.value)
            return replace(
                item,
                type=EvidenceType.ASSUMPTION,
                confidence=EvidenceConfidence.LOW,
                explanation=f"{item.explanation} (downgraded from FACT — source not verified)",
            )

        if src not in TRUSTED_FACT_SOURCES:
            logger.info("evidence: downgrade FACT — non-feed source %s", src.value)
            return replace(
                item,
                type=EvidenceType.ESTIMATE,
                confidence=EvidenceConfidence.MEDIUM,
                explanation=f"{item.explanation} (downgraded from FACT — model-derived)",
            )

        if item.confidence in (EvidenceConfidence.NONE, EvidenceConfidence.LOW):
            logger.info("evidence: downgrade FACT — low confidence on %s", item.label)
            return replace(
                item,
                type=EvidenceType.ESTIMATE,
                explanation=f"{item.explanation} (downgraded from FACT — confidence {item.confidence.value})",
            )

        if item.value is None or (isinstance(item.value, str) and not item.value.strip()):
            logger.info("evidence: FACT without value → GAP for %s", item.label)
            return replace(
                item,
                type=EvidenceType.GAP,
                value=None,
                confidence=EvidenceConfidence.NONE,
                explanation=item.explanation or f"No verified value for {item.label}",
            )

        return item

    def _enforce_gap_rules(self, item: EvidenceItem) -> EvidenceItem:
        if item.type == EvidenceType.GAP:
            return replace(
                item,
                value=None,
                confidence=EvidenceConfidence.NONE,
                explanation=item.explanation or f"Missing evidence: {item.label}",
            )
        if item.value is None and item.type != EvidenceType.GAP:
            return replace(
                item,
                type=EvidenceType.GAP,
                confidence=EvidenceConfidence.NONE,
                explanation=item.explanation or f"Missing value for {item.label}",
            )
        return item

    def _ensure_explanation(self, item: EvidenceItem) -> EvidenceItem:
        if item.explanation.strip():
            return item
        fallback = f"{item.label}: {item.value}" if item.value is not None else f"Missing: {item.label}"
        return replace(item, explanation=fallback)
