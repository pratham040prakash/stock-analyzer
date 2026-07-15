"""Decision rules — thresholds and critical gap policy."""

from __future__ import annotations

from analyzer.evidence_engine.models import EvidenceCategory, EvidenceType

DECISION_VERSION = "1.0"
MIN_COMPLETENESS_PCT = 20.0
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 100.0

CRITICAL_GAP_CATEGORIES = frozenset({
    EvidenceCategory.RISK,
    EvidenceCategory.EXECUTION,
    EvidenceCategory.MARKET,
})

ACT_NET_THRESHOLD = 0.45
STRONG_ACT_NET_THRESHOLD = 1.0
STRONG_ACT_CONFIDENCE = 65.0
ACT_CONFIDENCE = 55.0
REDUCE_NET_THRESHOLD = -0.15
PASS_NET_THRESHOLD = -0.35
CONFLICT_VOTE_THRESHOLD = 0.35


def is_critical_gap(item) -> bool:
    if item.type != EvidenceType.GAP:
        return False
    return item.category in CRITICAL_GAP_CATEGORIES
