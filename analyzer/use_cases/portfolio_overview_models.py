"""Portfolio Overview view model — authoritative DTO for Portfolio Command Center (V3-101)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioAttentionItemModel:
    symbol: str
    flag_type: str
    reason: str


@dataclass(frozen=True)
class PortfolioHealthSection:
    badge_key: str
    badge_label: str
    headline: str
    supporting_reason: str
    stale_qualified: bool
    stale_label: str


@dataclass(frozen=True)
class PortfolioActionSection:
    primary_label: str
    primary_action: str
    show_secondary: bool = True


@dataclass(frozen=True)
class PortfolioMetricsSection:
    invested_inr: float
    cash_inr: float
    day_pnl_inr: float | None
    holdings_count: int


@dataclass(frozen=True)
class PortfolioAllocationSection:
    core_pct: float
    tactical_pct: float
    cash_pct: float
    policy_line: str


@dataclass(frozen=True)
class PortfolioStandoutsSection:
    strongest_symbol: str
    strongest_pct: str
    weakest_symbol: str
    weakest_pct: str


@dataclass(frozen=True)
class PortfolioPreviewRowModel:
    symbol: str
    weight_pct: float
    health_label: str
    health_key: str


@dataclass(frozen=True)
class PortfolioDepthSection:
    title: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioOverviewViewModel:
    health: PortfolioHealthSection
    action: PortfolioActionSection
    metrics: PortfolioMetricsSection
    attention_items: tuple[PortfolioAttentionItemModel, ...]
    attention_empty_message: str
    allocation: PortfolioAllocationSection
    standouts: PortfolioStandoutsSection
    preview_rows: tuple[PortfolioPreviewRowModel, ...]
    preview_more_count: int
    depth_sections: tuple[PortfolioDepthSection, ...]
    broker_footer: str
