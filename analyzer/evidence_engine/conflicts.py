"""Detect conflicting evidence within a packet."""

from __future__ import annotations

import hashlib
from dataclasses import replace

from analyzer.evidence_engine.models import (
    EvidenceCategory,
    EvidenceConflict,
    EvidenceItem,
    EvidenceType,
)


def _conflict_id(category: EvidenceCategory, labels: list[str]) -> str:
    key = f"{category.value}:{'|'.join(sorted(labels))}"
    return f"conflict:{hashlib.sha256(key.encode()).hexdigest()[:10]}"


def _sentiment(item: EvidenceItem) -> float | None:
    meta = item.metadata or {}
    if "vote" in meta:
        try:
            return float(meta["vote"])
        except (TypeError, ValueError):
            pass
    if "score" in meta:
        try:
            return float(meta["score"])
        except (TypeError, ValueError):
            pass
    if "signal" in meta:
        sig = str(meta["signal"]).lower()
        if sig in ("bullish", "buy", "positive"):
            return 1.0
        if sig in ("bearish", "sell", "negative"):
            return -1.0
    if isinstance(item.value, (int, float)):
        return float(item.value)
    if isinstance(item.value, str):
        low = item.value.lower()
        if any(w in low for w in ("buy", "bullish", "strong buy", "accumulate")):
            return 1.0
        if any(w in low for w in ("sell", "bearish", "avoid", "reduce")):
            return -1.0
    return None


class EvidenceConflictDetector:
    """Find opposing claims in the same category."""

    CONFLICT_THRESHOLD = 0.35

    def detect(self, items: list[EvidenceItem]) -> list[EvidenceConflict]:
        conflicts: list[EvidenceConflict] = []
        by_category: dict[EvidenceCategory, list[EvidenceItem]] = {}
        for item in items:
            if item.type == EvidenceType.GAP:
                continue
            by_category.setdefault(item.category, []).append(item)

        seen: set[str] = set()
        for category, group in by_category.items():
            for conflict in self._pairwise_conflicts(category, group):
                if conflict.id not in seen:
                    seen.add(conflict.id)
                    conflicts.append(conflict)
            for conflict in self._recommendation_conflicts(category, group):
                if conflict.id not in seen:
                    seen.add(conflict.id)
                    conflicts.append(conflict)
        return conflicts

    def _pairwise_conflicts(
        self,
        category: EvidenceCategory,
        group: list[EvidenceItem],
    ) -> list[EvidenceConflict]:
        out: list[EvidenceConflict] = []
        scored = [(i, _sentiment(i)) for i in group]
        scored = [(i, s) for i, s in scored if s is not None]
        for idx, (a, sa) in enumerate(scored):
            for b, sb in scored[idx + 1 :]:
                if sa * sb >= 0:
                    continue
                if abs(sa) < self.CONFLICT_THRESHOLD or abs(sb) < self.CONFLICT_THRESHOLD:
                    continue
                severity = "high" if abs(sa) >= 1.0 and abs(sb) >= 1.0 else "medium"
                out.append(
                    EvidenceConflict(
                        id=_conflict_id(category, [a.label, b.label]),
                        category=category,
                        item_ids=[a.id, b.id],
                        description=(
                            f"{a.label} ({a.value}) conflicts with {b.label} ({b.value})"
                        ),
                        severity=severity,
                    )
                )
        return out

    def _recommendation_conflicts(
        self,
        category: EvidenceCategory,
        group: list[EvidenceItem],
    ) -> list[EvidenceConflict]:
        recs = [i for i in group if "recommendation" in i.label.lower() or "verdict" in i.label.lower()]
        if len(recs) < 2:
            return []
        bulls = [r for r in recs if (_sentiment(r) or 0) > 0.2]
        bears = [r for r in recs if (_sentiment(r) or 0) < -0.2]
        if not bulls or not bears:
            return []
        return [
            EvidenceConflict(
                id=_conflict_id(category, [r.label for r in recs]),
                category=category,
                item_ids=[r.id for r in recs],
                description="Multiple recommendation signals disagree",
                severity="high",
            )
        ]


def merge_duplicate_items(items: list[EvidenceItem]) -> list[EvidenceItem]:
    """Merge items with same category+label+type — keep higher confidence/weight."""
    merged: dict[tuple[str, str, str], EvidenceItem] = {}
    order: list[tuple[str, str, str]] = []

    conf_rank = {"high": 3, "medium": 2, "low": 1, "none": 0}

    for item in items:
        key = item.merge_key()
        if key not in merged:
            merged[key] = item
            order.append(key)
            continue
        existing = merged[key]
        ex_rank = conf_rank.get(
            existing.confidence.value if hasattr(existing.confidence, "value") else str(existing.confidence),
            0,
        )
        new_rank = conf_rank.get(
            item.confidence.value if hasattr(item.confidence, "value") else str(item.confidence),
            0,
        )
        winner = item if (new_rank, item.weight) >= (ex_rank, existing.weight) else existing
        loser = existing if winner is item else item
        combined_meta = {**loser.metadata, **winner.metadata}
        merged[key] = replace(winner, metadata=combined_meta)

    return [merged[k] for k in order]
