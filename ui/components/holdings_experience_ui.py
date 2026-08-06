"""Holdings Experience — presentation contracts and projection only (V3-102)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from dataclasses import dataclass

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.use_cases.morning_brief_models import PortfolioSection
from analyzer.use_cases.portfolio_overview_assembly import assemble_portfolio_overview
from analyzer.use_cases.portfolio_overview_models import (
    PortfolioHoldingRowModel,
    PortfolioOverviewViewModel,
    PortfolioWatchlistRowModel,
)
from analyzer.zerodha import ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.portfolio_overview_ui import _fmt_compact_inr


@dataclass(frozen=True)
class HoldingsContextBarContract:
    summary_line: str
    disconnected: bool
    connect_message: str
    show_connect_cta: bool
    show_sync_cta: bool
    has_holdings: bool


@dataclass(frozen=True)
class HoldingsRowContract:
    symbol: str
    name: str
    quantity: float
    value_inr: float
    weight_pct: float
    quantity_label: str
    average_cost_label: str
    ltp_label: str
    value_label: str
    weight_label: str
    health_key: str
    health_label: str
    pnl_label: str
    stale: bool
    attention_reason: str
    understand_headline: str


@dataclass(frozen=True)
class WatchlistRowContract:
    symbol: str
    name: str
    ltp_label: str


@dataclass(frozen=True)
class HoldingsExperienceContract:
    context: HoldingsContextBarContract
    rows: tuple[HoldingsRowContract, ...]
    watchlist: tuple[WatchlistRowContract, ...]
    broker_footer: str
    filtered_empty_message: str


def _fmt_price(value: float | None) -> str:
    if value is None:
        return "—"
    return f"₹{float(value):,.0f}"


def _fmt_qty(value: float) -> str:
    if value <= 0:
        return "—"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def _fmt_pnl(value: float | None) -> str:
    if value is None:
        return "—"
    amount = float(value)
    sign = "+" if amount >= 0 else ""
    return f"{sign}₹{amount:,.0f}"


def _row_contract(row: PortfolioHoldingRowModel) -> HoldingsRowContract:
    qty_text = _fmt_qty(row.quantity)
    weight_text = f"{row.weight_pct:.1f}%" if row.weight_pct else "—"
    headline = f"You hold {qty_text} shares · {weight_text} of portfolio"
    return HoldingsRowContract(
        symbol=row.symbol,
        name=row.name,
        quantity=row.quantity,
        value_inr=row.value_inr,
        weight_pct=row.weight_pct,
        quantity_label=qty_text,
        average_cost_label=_fmt_price(row.average_price),
        ltp_label=_fmt_price(row.last_price),
        value_label=_fmt_compact_inr(row.value_inr if row.value_inr else None),
        weight_label=weight_text,
        health_key=row.health_key,
        health_label=row.health_label,
        pnl_label=_fmt_pnl(row.pnl_inr),
        stale=row.stale,
        attention_reason=row.attention_reason,
        understand_headline=headline,
    )


def _watchlist_contract(row: PortfolioWatchlistRowModel) -> WatchlistRowContract:
    return WatchlistRowContract(
        symbol=row.symbol,
        name=row.name,
        ltp_label=_fmt_price(row.last_price),
    )


def holdings_experience_from_view_model(
    vm: PortfolioOverviewViewModel,
) -> HoldingsExperienceContract:
    """Map assembled view model to holdings render contracts — formatting only."""
    ctx = vm.holdings_context
    return HoldingsExperienceContract(
        context=HoldingsContextBarContract(
            summary_line=ctx.summary_line,
            disconnected=ctx.disconnected,
            connect_message=ctx.connect_message,
            show_connect_cta=ctx.show_connect_cta,
            show_sync_cta=ctx.show_sync_cta,
            has_holdings=ctx.has_holdings,
        ),
        rows=tuple(_row_contract(row) for row in vm.holdings_rows),
        watchlist=tuple(_watchlist_contract(row) for row in vm.watchlist_rows),
        broker_footer=vm.holdings_broker_footer,
        filtered_empty_message="No holdings match these filters.",
    )


def holdings_experience_from_inputs(
    *,
    broker: BrokerSnapshot,
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    portfolio_section: PortfolioSection | None = None,
    journal_today_pnl: float | None = None,
) -> HoldingsExperienceContract:
    """Assemble upstream view model, then project to holdings contracts."""
    vm = assemble_portfolio_overview(
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    return holdings_experience_from_view_model(vm)


def holdings_row_understand_contract(row: HoldingsRowContract):
    from ui.components.understand_popover import UnderstandContract, UnderstandSection

    weight_lines = (
        row.understand_headline,
        f"Current value is {row.value_label}.",
        f"Portfolio weight is {row.weight_label}.",
    )
    cost_lines = (
        f"Average cost: {row.average_cost_label} per share.",
        f"Last traded price: {row.ltp_label}.",
        f"Unrealized P&L: {row.pnl_label}.",
    )
    if row.attention_reason:
        health_lines = (row.attention_reason,)
    elif row.health_key == "ok":
        health_lines = ("This holding is within guideline weights.",)
    else:
        health_lines = ("Health could not be assessed from current data.",)
    return UnderstandContract(
        sections=(
            UnderstandSection("Position", (row.understand_headline,)),
            UnderstandSection("Why this weight matters", weight_lines),
            UnderstandSection("Cost basis vs current value", cost_lines),
            UnderstandSection("Health indicator", health_lines),
        )
    )
