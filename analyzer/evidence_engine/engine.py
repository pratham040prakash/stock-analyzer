"""Evidence Engine — combine, merge, validate, and build packets."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.evidence_engine.builder import EvidenceBuilder
from analyzer.evidence_engine.conflicts import EvidenceConflictDetector, merge_duplicate_items
from analyzer.evidence_engine.models import (
    EvidenceCategory,
    EvidenceItem,
    EvidencePacket,
    EvidenceType,
    RecommendationFromEvidence,
)
from analyzer.evidence_engine.validator import EvidenceValidator
from analyzer.structured_log import log_event

IST = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)

SCOPE_REQUIRED_CATEGORIES: dict[str, tuple[EvidenceCategory, ...]] = {
    "equity": (
        EvidenceCategory.MARKET,
        EvidenceCategory.TECHNICAL,
        EvidenceCategory.FUNDAMENTAL,
        EvidenceCategory.RISK,
    ),
    "options": (
        EvidenceCategory.MARKET,
        EvidenceCategory.TECHNICAL,
        EvidenceCategory.OPTIONS,
        EvidenceCategory.RISK,
        EvidenceCategory.EXECUTION,
    ),
    "portfolio": (
        EvidenceCategory.PORTFOLIO,
        EvidenceCategory.RISK,
        EvidenceCategory.FUNDAMENTAL,
    ),
    "market": (
        EvidenceCategory.MARKET,
        EvidenceCategory.MACRO,
    ),
    "research": (
        EvidenceCategory.FUNDAMENTAL,
        EvidenceCategory.TECHNICAL,
        EvidenceCategory.RISK,
    ),
}


class EvidenceEngine:
    """Canonical combiner — the only path to EvidencePacket."""

    def __init__(
        self,
        *,
        validator: EvidenceValidator | None = None,
        conflict_detector: EvidenceConflictDetector | None = None,
    ):
        self._validator = validator or EvidenceValidator()
        self._conflicts = conflict_detector or EvidenceConflictDetector()
        self._builder = EvidenceBuilder()

    def build_packet(
        self,
        *,
        subject: str,
        subject_type: str,
        items: list[EvidenceItem],
        required_categories: tuple[EvidenceCategory, ...] | None = None,
        metadata: dict | None = None,
        packet_id: str | None = None,
    ) -> EvidencePacket:
        required = required_categories or SCOPE_REQUIRED_CATEGORIES.get(
            subject_type, SCOPE_REQUIRED_CATEGORIES["equity"]
        )
        validated = self._validator.validate_many(items)
        merged = merge_duplicate_items(validated)
        gaps = self._inject_category_gaps(merged, required)
        merged_ids = {i.id for i in merged}
        all_items = merged + [g for g in gaps if g.id not in merged_ids]
        conflicts = self._conflicts.detect(all_items)
        present = sorted({i.category.value for i in all_items if i.type != EvidenceType.GAP})
        gap_items = [i for i in all_items if i.type == EvidenceType.GAP]
        non_gap_cats = {i.category for i in all_items if i.type != EvidenceType.GAP}
        covered = sum(1 for c in required if c in non_gap_cats)
        completeness = round(100.0 * covered / max(len(required), 1), 1)

        packet = EvidencePacket(
            packet_id=packet_id or f"evp_{uuid.uuid4().hex[:12]}",
            subject=subject,
            subject_type=subject_type,
            created_at=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
            items=all_items,
            conflicts=conflicts,
            gaps=gap_items,
            completeness_pct=completeness,
            categories_present=present,
            metadata=dict(metadata or {}),
        )
        log_event(
            "evidence_packet_built",
            subject=subject,
            subject_type=subject_type,
            packet_id=packet.packet_id,
            item_count=len(packet.items),
            gap_count=packet.gap_count,
            conflict_count=packet.conflict_count,
            completeness_pct=packet.completeness_pct,
        )
        return packet

    def _inject_category_gaps(
        self,
        items: list[EvidenceItem],
        required: tuple[EvidenceCategory, ...],
    ) -> list[EvidenceItem]:
        present = {i.category for i in items if i.type != EvidenceType.GAP}
        gap_categories = {i.category for i in items if i.type == EvidenceType.GAP}
        gaps: list[EvidenceItem] = []
        for cat in required:
            if cat in present or cat in gap_categories:
                continue
            gaps.append(
                self._builder.gap(
                    category=cat,
                    label=f"{cat.value} coverage",
                    explanation=f"No {cat.value} evidence collected for this subject",
                )
            )
        return gaps

    def recommend_from_packet(self, packet: EvidencePacket) -> RecommendationFromEvidence:
        """Derive verdict solely from packet evidence — for Recommendation Engine."""
        scored: list[tuple[EvidenceItem, float]] = []
        for item in packet.items:
            if item.type == EvidenceType.GAP:
                continue
            vote = item.metadata.get("vote")
            if vote is not None:
                try:
                    scored.append((item, float(vote) * item.weight))
                    continue
                except (TypeError, ValueError):
                    pass
            score = item.metadata.get("score")
            if score is not None:
                try:
                    scored.append((item, float(score) * item.weight * 0.01))
                    continue
                except (TypeError, ValueError):
                    pass
            sig = str(item.metadata.get("signal", "")).lower()
            if sig == "bullish":
                scored.append((item, 0.5 * item.weight))
            elif sig == "bearish":
                scored.append((item, -0.5 * item.weight))

        if not scored:
            return RecommendationFromEvidence(
                verdict="WAIT",
                headline="Insufficient evidence — default WAIT",
                confidence_pct=max(0, int(packet.completeness_pct * 0.5)),
                net_score=0.0,
                trade_allowed=False,
                positives=[],
                negatives=[g.explanation for g in packet.gaps[:3]],
            )

        total_w = sum(i.weight for i, _ in scored) or 1.0
        net = round(sum(v for _, v in scored) / total_w, 3)
        conflict_penalty = min(len(packet.conflicts) * 8, 30)
        agree_pos = sum(1 for _, v in scored if v > 0.2)
        agree_neg = sum(1 for _, v in scored if v < -0.2)
        conf = 50 + int(net * 22) + min(agree_pos * 4, 20) - min(agree_neg * 6, 30) - conflict_penalty
        conf = max(0, min(100, conf))

        hard_block = any(
            c.severity == "high" and c.category == EvidenceCategory.EXECUTION
            for c in packet.conflicts
        )
        if hard_block or net < -0.35:
            verdict, headline, allowed = "NO_TRADE", "No trade — conflicts or negative net", False
        elif net >= 1.2:
            verdict, headline, allowed = "STRONG_BUY", "Strong alignment — trade with plan", True
        elif net >= 0.55:
            verdict, headline, allowed = "BUY", "Lean buy — follow gate & stop", True
        elif net >= 0.15:
            verdict, headline, allowed = "CAUTION", "Mixed — reduce size", False
        else:
            verdict, headline, allowed = "WAIT", "Wait — signals not aligned", False

        if packet.gap_count > 2 and conf < 55:
            allowed = False
            if verdict in ("STRONG_BUY", "BUY"):
                verdict = "CAUTION"

        positives = [
            f"{i.label}: {i.explanation[:80]}"
            for i, v in scored
            if v > 0.3
        ][:6]
        negatives = [
            f"{i.label}: {i.explanation[:80]}"
            for i, v in scored
            if v < -0.3
        ][:6]
        for c in packet.conflicts:
            negatives.append(c.description[:80])

        return RecommendationFromEvidence(
            verdict=verdict,
            headline=headline,
            confidence_pct=conf,
            net_score=net,
            trade_allowed=allowed and conf >= 55,
            positives=positives,
            negatives=negatives,
        )


def default_engine() -> EvidenceEngine:
    return EvidenceEngine()
