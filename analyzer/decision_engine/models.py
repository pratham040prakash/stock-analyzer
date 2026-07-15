"""Decision Engine — canonical investment verdict models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

DECISION_VERSION = "1.0"


class DecisionVerdict(str, Enum):
    ACT = "ACT"
    WAIT = "WAIT"
    PASS = "PASS"
    REDUCE = "REDUCE"
    DEFENSIVE = "DEFENSIVE"


@dataclass
class UncertaintyVector:
    """Multi-axis uncertainty — higher means more uncertain."""

    evidence_completeness: float = 0.0
    conflict_level: float = 0.0
    data_quality: float = 0.0
    regime_risk: float = 0.0
    capital_headroom: float = 0.0
    overall: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "evidence_completeness": round(self.evidence_completeness, 1),
            "conflict_level": round(self.conflict_level, 1),
            "data_quality": round(self.data_quality, 1),
            "regime_risk": round(self.regime_risk, 1),
            "capital_headroom": round(self.capital_headroom, 1),
            "overall": round(self.overall, 1),
        }


@dataclass
class MarketContext:
    regime: str | None = None
    market_bias: str = ""
    session_open: bool = True
    allow_new_entries: bool = True
    allow_aggressive: bool = True
    timing_headline: str = ""


@dataclass
class CapitalConstraints:
    capital_inr: float = 50_000.0
    max_risk_pct: float = 2.0
    max_trades: int = 3
    allocation_pct: float = 100.0
    daily_loss_cap_inr: float | None = None


@dataclass
class PortfolioState:
    open_positions: int = 0
    sector_concentration_pct: float = 0.0
    cash_available_inr: float | None = None
    known: bool = True


@dataclass
class UserPreferences:
    beginner_mode: bool = False
    equity_only: bool = False
    profit_mode: str = "aggressive"
    horizon: str = "medium"


@dataclass
class RiskSettings:
    max_risk_pct: float = 2.0
    min_risk_reward: float = 1.5
    loss_streak_days: int = 0
    max_loss_streak_before_pause: int = 2
    require_gate_green: bool = True
    gate_allowed: bool = True


@dataclass
class DecisionContext:
    """Full decision input context."""

    market: MarketContext = field(default_factory=MarketContext)
    capital: CapitalConstraints = field(default_factory=CapitalConstraints)
    portfolio: PortfolioState = field(default_factory=PortfolioState)
    preferences: UserPreferences = field(default_factory=UserPreferences)
    risk: RiskSettings = field(default_factory=RiskSettings)


@dataclass
class DecisionRequest:
    subject: str
    subject_type: str
    evidence_packet_id: str
    context: DecisionContext = field(default_factory=DecisionContext)

    @property
    def market(self) -> MarketContext:
        return self.context.market

    @property
    def capital(self) -> CapitalConstraints:
        return self.context.capital

    @property
    def portfolio(self) -> PortfolioState:
        return self.context.portfolio

    @property
    def preferences(self) -> UserPreferences:
        return self.context.preferences

    @property
    def risk(self) -> RiskSettings:
        return self.context.risk


@dataclass
class DecisionExplainability:
    why: str
    why_now: str
    why_not: str


@dataclass
class DecisionArtifact:
    """Canonical investment verdict — only Decision Engine may produce this."""

    decision_id: str
    timestamp: str
    verdict: DecisionVerdict
    reason: str
    evidence_packet_id: str
    confidence: float
    uncertainty: UncertaintyVector
    capital_recommendation: str
    execution_recommendation: str
    supporting_evidence_ids: list[str] = field(default_factory=list)
    conflicting_evidence_ids: list[str] = field(default_factory=list)
    alternative_actions: list[str] = field(default_factory=list)
    invalidation_conditions: list[str] = field(default_factory=list)
    explainability: DecisionExplainability | None = None
    decision_version: str = DECISION_VERSION
    subject: str = ""
    subject_type: str = "equity"
    trade_allowed: bool = False
    net_score: float = 0.0
    metadata: dict = field(default_factory=dict)
