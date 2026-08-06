"""Portfolio Command Center — presentation contracts and projection only (V3-101)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from dataclasses import dataclass

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.use_cases.morning_brief_models import PortfolioSection
from analyzer.use_cases.portfolio_overview_assembly import assemble_portfolio_overview
from analyzer.use_cases.portfolio_overview_models import PortfolioOverviewViewModel
from analyzer.zerodha import ZerodhaImportResult
from ui.broker.state import BrokerSnapshot


@dataclass(frozen=True)
class PortfolioHealthHeroContract:
    badge_key: str
    badge_label: str
    headline: str
    supporting_reason: str
    stale_qualified: bool
    stale_label: str


@dataclass(frozen=True)
class PortfolioActionRowContract:
    primary_label: str
    primary_action: str
    show_secondary: bool = True


@dataclass(frozen=True)
class PortfolioStatusStripContract:
    total_value_label: str
    day_change_label: str
    holdings_count_label: str
    cash_label: str
    sync_label: str


@dataclass(frozen=True)
class PortfolioAttentionItem:
    symbol: str
    flag_type: str
    reason: str


@dataclass(frozen=True)
class PortfolioAttentionContract:
    items: tuple[PortfolioAttentionItem, ...]
    empty_message: str


@dataclass(frozen=True)
class PortfolioAllocationContract:
    core_pct: float
    tactical_pct: float
    cash_pct: float
    policy_line: str


@dataclass(frozen=True)
class PortfolioStandoutsContract:
    strongest_symbol: str
    strongest_pct: str
    weakest_symbol: str
    weakest_pct: str


@dataclass(frozen=True)
class PortfolioHoldingPreviewRow:
    symbol: str
    weight_pct: float
    health_label: str
    health_key: str


@dataclass(frozen=True)
class PortfolioHoldingPreviewContract:
    rows: tuple[PortfolioHoldingPreviewRow, ...]
    more_count: int


@dataclass(frozen=True)
class PortfolioDepthContract:
    allocation_lines: tuple[str, ...]
    concentration_lines: tuple[str, ...]
    holding_health_lines: tuple[str, ...]
    policy_lines: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioOverviewContract:
    hero: PortfolioHealthHeroContract
    action: PortfolioActionRowContract
    status: PortfolioStatusStripContract
    attention: PortfolioAttentionContract
    allocation: PortfolioAllocationContract
    standouts: PortfolioStandoutsContract
    preview: PortfolioHoldingPreviewContract
    broker_footer: str
    depth: PortfolioDepthContract


def _fmt_compact_inr(value: float | None) -> str:
    if value is None:
        return "—"
    amount = float(value)
    if abs(amount) >= 100000:
        return f"₹{amount / 100000:.1f}L"
    return f"₹{amount:,.0f}"


def _fmt_day_pct(value: float | None, *, invested: float) -> str:
    if value is None or invested <= 0:
        return "—"
    pct = 100.0 * float(value) / invested
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"


def _sync_label(broker: BrokerSnapshot) -> str:
    if broker.connected():
        if broker.state == "limited":
            return "Stale"
        if broker.last_sync_at:
            return f"Synced · {broker.last_sync_at}"
        return "Synced"
    if broker.last_sync_at:
        return f"Saved · {broker.last_sync_at}"
    return "Not synced"


def portfolio_overview_from_view_model(
    vm: PortfolioOverviewViewModel,
    *,
    broker: BrokerSnapshot,
) -> PortfolioOverviewContract:
    """Map assembled view model to render contracts — formatting only."""
    metrics = vm.metrics
    total = metrics.invested_inr + metrics.cash_inr
    depth_by_title = {section.title: section.lines for section in vm.depth_sections}
    return PortfolioOverviewContract(
        hero=PortfolioHealthHeroContract(
            badge_key=vm.health.badge_key,
            badge_label=vm.health.badge_label,
            headline=vm.health.headline,
            supporting_reason=vm.health.supporting_reason,
            stale_qualified=vm.health.stale_qualified,
            stale_label=vm.health.stale_label,
        ),
        action=PortfolioActionRowContract(
            primary_label=vm.action.primary_label,
            primary_action=vm.action.primary_action,
            show_secondary=vm.action.show_secondary,
        ),
        status=PortfolioStatusStripContract(
            total_value_label=_fmt_compact_inr(total if total else None),
            day_change_label=_fmt_day_pct(
                metrics.day_pnl_inr,
                invested=metrics.invested_inr or 1.0,
            ),
            holdings_count_label=str(metrics.holdings_count),
            cash_label=_fmt_compact_inr(metrics.cash_inr if metrics.cash_inr else None),
            sync_label=_sync_label(broker),
        ),
        attention=PortfolioAttentionContract(
            items=tuple(
                PortfolioAttentionItem(
                    symbol=item.symbol,
                    flag_type=item.flag_type,
                    reason=item.reason,
                )
                for item in vm.attention_items
            ),
            empty_message=vm.attention_empty_message,
        ),
        allocation=PortfolioAllocationContract(
            core_pct=vm.allocation.core_pct,
            tactical_pct=vm.allocation.tactical_pct,
            cash_pct=vm.allocation.cash_pct,
            policy_line=vm.allocation.policy_line,
        ),
        standouts=PortfolioStandoutsContract(
            strongest_symbol=vm.standouts.strongest_symbol,
            strongest_pct=vm.standouts.strongest_pct,
            weakest_symbol=vm.standouts.weakest_symbol,
            weakest_pct=vm.standouts.weakest_pct,
        ),
        preview=PortfolioHoldingPreviewContract(
            rows=tuple(
                PortfolioHoldingPreviewRow(
                    symbol=row.symbol,
                    weight_pct=row.weight_pct,
                    health_label=row.health_label,
                    health_key=row.health_key,
                )
                for row in vm.preview_rows
            ),
            more_count=vm.preview_more_count,
        ),
        broker_footer=vm.broker_footer,
        depth=PortfolioDepthContract(
            allocation_lines=depth_by_title.get("Allocation", ()),
            concentration_lines=depth_by_title.get("Concentration", ()),
            holding_health_lines=depth_by_title.get("Holding health", ()),
            policy_lines=depth_by_title.get("Policy vs actual", ()),
        ),
    )


def portfolio_overview_from_inputs(
    *,
    broker: BrokerSnapshot,
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    portfolio_section: PortfolioSection | None = None,
    journal_today_pnl: float | None = None,
) -> PortfolioOverviewContract:
    """Assemble upstream view model, then project to presentation contracts."""
    vm = assemble_portfolio_overview(
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    return portfolio_overview_from_view_model(vm, broker=broker)


def portfolio_understand_contract(contract: PortfolioOverviewContract):
    from ui.components.understand_popover import UnderstandContract, UnderstandSection

    depth = contract.depth
    return UnderstandContract(
        sections=(
            UnderstandSection("Allocation", depth.allocation_lines),
            UnderstandSection("Concentration", depth.concentration_lines),
            UnderstandSection("Holding health", depth.holding_health_lines),
            UnderstandSection("Policy vs actual", depth.policy_lines),
        )
    )
