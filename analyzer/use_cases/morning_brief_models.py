"""Morning Brief view models — authoritative DTO for Today (ETS-003b v0.2)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BriefMetaSection:
    built_at: str
    scenario: str
    market: str
    session_phase: str


@dataclass(frozen=True)
class DecisionSection:
    verdict: str | None
    verdict_display: str
    verdict_key: str
    reason: str
    confidence_level: int
    confidence_band: str
    last_updated: str
    valid_until: str
    cta_label: str
    cta_action: str
    decision_id: str
    decision_source: str


@dataclass(frozen=True)
class EvidenceLine:
    label: str
    value: str
    type: str
    source: str
    confidence: str


@dataclass(frozen=True)
class EvidenceSection:
    key_reasons: tuple[str, ...]
    supporting_signals: tuple[EvidenceLine, ...]
    conflicting_signals: tuple[EvidenceLine, ...]
    evidence_packet_id: str
    evidence_available: bool
    gap_note: str


@dataclass(frozen=True)
class DataFreshnessSection:
    context_fresh: bool
    context_age_sec: float | None
    decision_fresh: bool
    decision_age_min: float | None
    broker_sync_state: str
    broker_last_sync: str


@dataclass(frozen=True)
class PortfolioSyncSection:
    personalized: bool
    scope: str
    summary: str


@dataclass(frozen=True)
class TrustSection:
    why_this_is_recommended: str
    recommendation_confidence: str
    data_freshness: DataFreshnessSection
    portfolio_sync_status: PortfolioSyncSection
    stale: bool
    stale_label: str
    gaps: tuple[str, ...]


@dataclass(frozen=True)
class OpportunitySection:
    visible: bool
    symbol: str
    setup: str
    lane: str


@dataclass(frozen=True)
class PortfolioSection:
    ready: bool
    holdings_count: int
    cash_available_inr: float | None
    tactical_pool_inr: float | None
    sacred_core_excluded: bool
    summary: str


@dataclass(frozen=True)
class RiskSection:
    level: str
    warnings: tuple[str, ...]
    session_ribbon: tuple[str, ...]


@dataclass(frozen=True)
class MorningBriefViewModel:
    """Root DTO — Decision + Evidence + Trust + supporting sections."""

    meta: BriefMetaSection
    decision: DecisionSection
    evidence: EvidenceSection
    trust: TrustSection
    opportunity: OpportunitySection
    portfolio: PortfolioSection
    risk: RiskSection
    failure_message: str | None = None
