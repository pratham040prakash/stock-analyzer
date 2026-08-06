"""Portfolio Review — presentation contracts and theme projection (V3-103)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from dataclasses import dataclass

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.use_cases.morning_brief_models import PortfolioSection
from analyzer.use_cases.portfolio_overview_assembly import assemble_portfolio_overview
from analyzer.use_cases.portfolio_overview_models import (
    PortfolioAttentionItemModel,
    PortfolioHoldingRowModel,
    PortfolioOverviewViewModel,
)
from analyzer.zerodha import ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.portfolio_overview_ui import portfolio_understand_contract, portfolio_overview_from_view_model

_THEME_SECTOR = "sector_concentration"
_THEME_SINGLE = "single_position_risk"
_THEME_POLICY = "policy_drift"
_THEME_CASH = "cash_allocation"

_CALM_QUALIFIER = (
    "This does not require immediate trading — review before your next decision window."
)
_GUIDANCE = {
    _THEME_SECTOR: "Confirm whether sector overweight is intentional; check your rebalance plan.",
    _THEME_SINGLE: "Confirm position size aligns with conviction and your capital plan.",
    _THEME_POLICY: "Compare actual allocation to your policy; adjust only if your plan changed.",
    _THEME_CASH: "Verify cash buffer matches your tactical deployment plan.",
}


@dataclass(frozen=True)
class AffectedHoldingContract:
    symbol: str
    weight_label: str
    weight_pct: float


@dataclass(frozen=True)
class ThemeReviewItemContract:
    theme_key: str
    theme_title: str
    explanation: str
    affected_holdings: tuple[AffectedHoldingContract, ...]
    investigation_guidance: str
    research_symbols: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioExplanationContract:
    headline: str
    qualifier: str
    show_connect_cta: bool
    connect_message: str


@dataclass(frozen=True)
class ReassuranceItemContract:
    label: str
    passed: bool


@dataclass(frozen=True)
class AllocationPolicyReviewContract:
    summary_line: str
    show_understand: bool


@dataclass(frozen=True)
class PortfolioReviewContract:
    explanation: PortfolioExplanationContract
    themes: tuple[ThemeReviewItemContract, ...]
    reassurance_items: tuple[ReassuranceItemContract, ...]
    allocation: AllocationPolicyReviewContract
    broker_footer: str
    primary_action: str
    primary_label: str
    show_progress: bool
    overview_understand: object


def _weight_label(pct: float) -> str:
    return f"{pct:.1f}%"


def _affected_holdings(
    holdings: tuple[PortfolioHoldingRowModel, ...],
    symbols: tuple[str, ...] | None = None,
) -> tuple[AffectedHoldingContract, ...]:
    rows = list(holdings)
    if symbols:
        wanted = {sym.upper() for sym in symbols}
        rows = [row for row in rows if row.symbol.upper() in wanted]
    rows.sort(key=lambda row: (-row.weight_pct, row.symbol))
    return tuple(
        AffectedHoldingContract(
            symbol=row.symbol,
            weight_label=_weight_label(row.weight_pct),
            weight_pct=row.weight_pct,
        )
        for row in rows[:5]
    )


def _affected_line(holdings: tuple[AffectedHoldingContract, ...]) -> str:
    if not holdings:
        return "—"
    return " · ".join(f"{item.symbol} ({item.weight_label})" for item in holdings)


def _concentration_items(
    attention: tuple[PortfolioAttentionItemModel, ...],
) -> tuple[PortfolioAttentionItemModel, ...]:
    return tuple(item for item in attention if item.flag_type == "Concentration")


def _sector_concentration_theme(
    items: tuple[PortfolioAttentionItemModel, ...],
    holdings: tuple[PortfolioHoldingRowModel, ...],
) -> ThemeReviewItemContract | None:
    if not items:
        return None
    symbols = tuple(item.symbol for item in items if item.symbol not in ("—", ""))
    affected = _affected_holdings(holdings, symbols or None)
    if not affected and holdings:
        top = sorted(holdings, key=lambda row: -row.weight_pct)[:3]
        affected = tuple(
            AffectedHoldingContract(row.symbol, _weight_label(row.weight_pct), row.weight_pct)
            for row in top
        )
        symbols = tuple(row.symbol for row in top)
    explanation = items[0].reason
    if len(items) > 1 and "sector" not in explanation.lower():
        explanation = (
            f"Multiple holdings exceed guideline weights. {items[0].reason}"
        )
    return ThemeReviewItemContract(
        theme_key=_THEME_SECTOR,
        theme_title="Sector Concentration",
        explanation=explanation,
        affected_holdings=affected,
        investigation_guidance=_GUIDANCE[_THEME_SECTOR],
        research_symbols=symbols or tuple(item.symbol for item in affected),
    )


def _single_position_theme(
    item: PortfolioAttentionItemModel,
    holdings: tuple[PortfolioHoldingRowModel, ...],
) -> ThemeReviewItemContract:
    symbols = (item.symbol,) if item.symbol not in ("—", "") else ()
    affected = _affected_holdings(holdings, symbols or None)
    if not affected and item.symbol not in ("—", ""):
        affected = (
            AffectedHoldingContract(item.symbol, "—", 0.0),
        )
    return ThemeReviewItemContract(
        theme_key=f"{_THEME_SINGLE}:{item.symbol}",
        theme_title="Single Position Risk",
        explanation=item.reason,
        affected_holdings=affected,
        investigation_guidance=_GUIDANCE[_THEME_SINGLE],
        research_symbols=symbols,
    )


def _health_attention_theme(
    item: PortfolioAttentionItemModel,
    holdings: tuple[PortfolioHoldingRowModel, ...],
) -> ThemeReviewItemContract:
    flagged_rows = [row for row in holdings if row.health_key == "attention"]
    flagged = tuple(
        AffectedHoldingContract(row.symbol, _weight_label(row.weight_pct), row.weight_pct)
        for row in sorted(flagged_rows, key=lambda row: (-row.weight_pct, row.symbol))[:5]
    )
    symbols = tuple(row.symbol for row in flagged)
    return ThemeReviewItemContract(
        theme_key=f"health:{item.symbol}",
        theme_title="Single Position Risk",
        explanation=item.reason,
        affected_holdings=flagged,
        investigation_guidance="Verify business health and thesis in Research before acting.",
        research_symbols=symbols,
    )


def _policy_drift_theme(vm: PortfolioOverviewViewModel) -> ThemeReviewItemContract | None:
    policy = vm.allocation.policy_line.strip()
    if not policy or "on track" in policy.lower():
        return None
    top = _affected_holdings(vm.holdings_rows, None)[:3]
    return ThemeReviewItemContract(
        theme_key=_THEME_POLICY,
        theme_title="Policy Drift",
        explanation=policy,
        affected_holdings=top,
        investigation_guidance=_GUIDANCE[_THEME_POLICY],
        research_symbols=tuple(row.symbol for row in top),
    )


def _cash_allocation_theme(vm: PortfolioOverviewViewModel) -> ThemeReviewItemContract | None:
    if vm.metrics.invested_inr <= 0 or vm.allocation.cash_pct >= 5.0:
        return None
    return ThemeReviewItemContract(
        theme_key=_THEME_CASH,
        theme_title="Cash Allocation",
        explanation=(
            f"Cash buffer is {vm.allocation.cash_pct:.1f}% of total capital — "
            "below your 5% minimum guideline."
        ),
        affected_holdings=(),
        investigation_guidance=_GUIDANCE[_THEME_CASH],
        research_symbols=(),
    )


def _build_themes(vm: PortfolioOverviewViewModel) -> tuple[ThemeReviewItemContract, ...]:
    themes: list[ThemeReviewItemContract] = []
    concentration = _concentration_items(vm.attention_items)
    sector_like = [item for item in concentration if "sector" in item.reason.lower()]
    use_sector = len(concentration) >= 2 or bool(sector_like)
    if use_sector and concentration:
        sector_theme = _sector_concentration_theme(concentration, vm.holdings_rows)
        if sector_theme:
            themes.append(sector_theme)
    else:
        for item in concentration:
            if item.symbol not in ("—", ""):
                themes.append(_single_position_theme(item, vm.holdings_rows))

    for item in vm.attention_items:
        if item.flag_type == "Health":
            themes.append(_health_attention_theme(item, vm.holdings_rows))

    policy = _policy_drift_theme(vm)
    if policy and not any(theme.theme_key == _THEME_POLICY for theme in themes):
        themes.append(policy)

    cash = _cash_allocation_theme(vm)
    if cash:
        themes.append(cash)

    priority = {
        _THEME_SECTOR: 0,
        _THEME_SINGLE: 1,
        _THEME_POLICY: 2,
        _THEME_CASH: 3,
    }

    def sort_key(theme: ThemeReviewItemContract) -> tuple[int, str]:
        base = theme.theme_key.split(":", 1)[0]
        return (priority.get(base, 9), theme.theme_title)

    themes.sort(key=sort_key)
    return tuple(themes[:3])


def _explanation_headline(vm: PortfolioOverviewViewModel) -> tuple[str, str]:
    health = vm.health
    qualifier = ""
    if health.stale_qualified and health.stale_label:
        qualifier = health.stale_label
    if health.badge_key == "connect":
        return (
            "Connect your broker to review portfolio health and allocation.",
            qualifier,
        )
    if vm.attention_items:
        lead = vm.attention_items[0].reason
        headline = f"Your portfolio needs review because {lead.rstrip('.')}."
        if len(vm.attention_items) > 1:
            headline = (
                "Your portfolio needs review because multiple themes exceed your guidelines."
            )
        return (f"{headline} {_CALM_QUALIFIER}", qualifier)
    supporting = health.supporting_reason or health.headline
    return (f"Your portfolio is healthy. {supporting}", qualifier)


def _reassurance_items(vm: PortfolioOverviewViewModel) -> tuple[ReassuranceItemContract, ...]:
    concentration_ok = not vm.attention_items or all(
        item.flag_type != "Concentration" for item in vm.attention_items
    )
    allocation_ok = "on track" in vm.allocation.policy_line.lower()
    sync_ok = not vm.health.stale_qualified
    return (
        ReassuranceItemContract("Concentration within limits", concentration_ok),
        ReassuranceItemContract(
            "Allocation on track (Core / Tactical / Cash)", allocation_ok
        ),
        ReassuranceItemContract("No sync or data freshness issues", sync_ok),
    )


def portfolio_review_from_view_model(
    vm: PortfolioOverviewViewModel,
    *,
    broker: BrokerSnapshot,
) -> PortfolioReviewContract:
    """Map assembled view model to review contracts — theme grouping is projection only."""
    headline, qualifier = _explanation_headline(vm)
    themes = _build_themes(vm)
    overview = portfolio_overview_from_view_model(vm, broker=broker)
    alloc = vm.allocation
    summary = (
        f"Core {alloc.core_pct:.0f}% · Tactical {alloc.tactical_pct:.0f}% · "
        f"Cash {alloc.cash_pct:.0f}% — {alloc.policy_line}"
    )
    connected = broker.connected()
    show_connect = vm.health.badge_key == "connect"
    if vm.attention_items:
        primary_action = "review_next"
        primary_label = "Review next theme"
    elif show_connect:
        primary_action = "connect"
        primary_label = "Connect Zerodha"
    else:
        primary_action = "holdings"
        primary_label = "View holdings"
    return PortfolioReviewContract(
        explanation=PortfolioExplanationContract(
            headline=headline,
            qualifier=qualifier,
            show_connect_cta=show_connect and not connected,
            connect_message=(
                "Link Zerodha to review live portfolio themes and allocation."
                if show_connect
                else ""
            ),
        ),
        themes=themes,
        reassurance_items=_reassurance_items(vm),
        allocation=AllocationPolicyReviewContract(
            summary_line=summary,
            show_understand=True,
        ),
        broker_footer=vm.broker_footer,
        primary_action=primary_action,
        primary_label=primary_label,
        show_progress=bool(themes),
        overview_understand=portfolio_understand_contract(overview),
    )


def portfolio_review_from_inputs(
    *,
    broker: BrokerSnapshot,
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    portfolio_section: PortfolioSection | None = None,
    journal_today_pnl: float | None = None,
) -> PortfolioReviewContract:
    vm = assemble_portfolio_overview(
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    return portfolio_review_from_view_model(vm, broker=broker)


def theme_understand_contract(theme: ThemeReviewItemContract):
    from ui.components.understand_popover import UnderstandContract, UnderstandSection

    holdings_line = _affected_line(theme.affected_holdings)
    return UnderstandContract(
        sections=(
            UnderstandSection("Why this theme was flagged", (theme.explanation,)),
            UnderstandSection("Affected holdings", (holdings_line,)),
            UnderstandSection(
                "Investigation guidance",
                (theme.investigation_guidance,),
            ),
            UnderstandSection(
                "What could change",
                ("New buys, sector rotation, or policy update.",),
            ),
        )
    )


def affected_holdings_display(theme: ThemeReviewItemContract) -> str:
    return _affected_line(theme.affected_holdings)
