"""Evidence Engine — canonical investment evidence models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EvidenceCategory(str, Enum):
    MARKET = "Market"
    TECHNICAL = "Technical"
    FUNDAMENTAL = "Fundamental"
    VOLUME = "Volume"
    SENTIMENT = "Sentiment"
    MACRO = "Macro"
    OPTIONS = "Options"
    RISK = "Risk"
    PORTFOLIO = "Portfolio"
    EXECUTION = "Execution"


class EvidenceType(str, Enum):
    FACT = "FACT"
    ESTIMATE = "ESTIMATE"
    OPINION = "OPINION"
    ASSUMPTION = "ASSUMPTION"
    GAP = "GAP"


class EvidenceSource(str, Enum):
    YAHOO_FINANCE = "yahoo_finance"
    KITE = "kite"
    NSE = "nse"
    SCREENER = "screener"
    INTERNAL_MODEL = "internal_model"
    COACH = "coach"
    DATA_HEALTH = "data_health"
    NEWS_FEED = "news_feed"
    MACRO_FEED = "macro_feed"
    USER = "user"
    UNKNOWN = "unknown"


class EvidenceConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


ALL_CATEGORIES = tuple(EvidenceCategory)


@dataclass
class EvidenceItem:
    """Single labeled claim with provenance."""

    id: str
    category: EvidenceCategory
    source: EvidenceSource | str
    timestamp: str
    label: str
    type: EvidenceType
    value: str | float | bool | int | None
    confidence: EvidenceConfidence
    weight: float
    explanation: str
    metadata: dict = field(default_factory=dict)

    def merge_key(self) -> tuple[str, str, str]:
        return (self.category.value, self.label.strip().lower(), self.type.value)


@dataclass
class EvidenceConflict:
    """Detected disagreement between evidence items."""

    id: str
    category: EvidenceCategory
    item_ids: list[str]
    description: str
    severity: str  # low | medium | high


@dataclass
class EvidencePacket:
    """Bounded evidence bundle for a recommendation or report."""

    packet_id: str
    subject: str
    subject_type: str  # equity | options | portfolio | market
    created_at: str
    items: list[EvidenceItem] = field(default_factory=list)
    conflicts: list[EvidenceConflict] = field(default_factory=list)
    gaps: list[EvidenceItem] = field(default_factory=list)
    completeness_pct: float = 0.0
    categories_present: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def gap_count(self) -> int:
        return len(self.gaps)

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)

    def items_by_category(self, category: EvidenceCategory) -> list[EvidenceItem]:
        return [i for i in self.items if i.category == category]

    def fact_items(self) -> list[EvidenceItem]:
        return [i for i in self.items if i.type == EvidenceType.FACT]


@dataclass
class RecommendationFromEvidence:
    """Verdict derived solely from an EvidencePacket."""

    verdict: str
    headline: str
    confidence_pct: int
    net_score: float
    trade_allowed: bool
    positives: list[str]
    negatives: list[str]
