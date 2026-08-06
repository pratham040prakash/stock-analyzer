"""Assemble PortfolioOverviewViewModel — health evaluation lives here, not in UI (V3-101)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.use_cases.morning_brief_models import PortfolioSection
from analyzer.use_cases.portfolio_overview_models import (
    PortfolioActionSection,
    PortfolioAllocationSection,
    PortfolioAttentionItemModel,
    PortfolioDepthSection,
    PortfolioHealthSection,
    PortfolioMetricsSection,
    PortfolioOverviewViewModel,
    PortfolioPreviewRowModel,
    PortfolioStandoutsSection,
)
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.broker.state import BrokerSnapshot

_CONCENTRATION_WARN_PCT = 25.0
_MAX_ATTENTION = 3
_BROKER_FOOTER = "Zerodha Console is source of truth for holdings and P&L."


def _holding_rows(portfolio: ZerodhaImportResult | None) -> list[ZerodhaHolding]:
    if not portfolio or not portfolio.holdings:
        return []
    return [h for h in portfolio.holdings if (h.quantity or 0) > 0]


def _weights(holdings: list[ZerodhaHolding]) -> list[tuple[str, float, float]]:
    rows: list[tuple[str, float, float]] = []
    for holding in holdings:
        ltp = holding.last_price or holding.average_price or 0.0
        value = float(holding.quantity or 0) * float(ltp)
        if value <= 0:
            continue
        sym = (holding.tradingsymbol or holding.kite_symbol or "—").upper()
        rows.append((sym, value, 0.0))
    total = sum(item[1] for item in rows) or 1.0
    return [(sym, value, 100.0 * value / total) for sym, value, _ in rows]


def _journal_unrealized(portfolio: ZerodhaImportResult | None) -> float | None:
    if not portfolio or not portfolio.holdings:
        return None
    total = 0.0
    found = False
    for holding in portfolio.holdings:
        if holding.pnl is not None:
            total += float(holding.pnl)
            found = True
    return total if found else None


def _holding_extremes(holdings: list[ZerodhaHolding]) -> tuple[str, str]:
    scored: list[tuple[str, float]] = []
    for holding in holdings:
        if holding.pnl is None or not holding.average_price or not holding.quantity:
            continue
        cost = float(holding.average_price) * float(holding.quantity)
        if cost <= 0:
            continue
        pct = 100.0 * float(holding.pnl) / cost
        sym = holding.tradingsymbol or holding.kite_symbol or "—"
        scored.append((sym, pct))
    if not scored:
        return "—", "—"
    scored.sort(key=lambda item: item[1])
    weakest = f"{scored[0][0]} ({scored[0][1]:+.1f}%)"
    strongest = f"{scored[-1][0]} ({scored[-1][1]:+.1f}%)"
    return weakest, strongest


def _split_standout(raw: str) -> tuple[str, str]:
    text = str(raw or "—").strip()
    if text == "—":
        return "—", "—"
    if "(" in text and text.endswith(")"):
        sym, _, rest = text.partition("(")
        return sym.strip(), rest.rstrip(")").strip()
    return text, "—"


def _attention_items(
    *,
    weights: list[tuple[str, float, float]],
    broker: BrokerSnapshot,
    portfolio_section: PortfolioSection | None,
) -> tuple[PortfolioAttentionItemModel, ...]:
    items: list[PortfolioAttentionItemModel] = []
    for sym, _, pct in sorted(weights, key=lambda row: -row[2]):
        if pct > _CONCENTRATION_WARN_PCT:
            items.append(
                PortfolioAttentionItemModel(
                    symbol=sym,
                    flag_type="Concentration",
                    reason=(
                        f"{sym} is {pct:.0f}% of portfolio — "
                        f"above {_CONCENTRATION_WARN_PCT:.0f}% guideline"
                    ),
                )
            )
    if portfolio_section and not portfolio_section.ready and broker.connected():
        summary = portfolio_section.summary.strip()
        if summary:
            items.append(
                PortfolioAttentionItemModel(
                    symbol="—",
                    flag_type="Health",
                    reason=summary,
                )
            )
    return tuple(items[:_MAX_ATTENTION])


def _allocation_section(
    *,
    invested: float,
    cash: float,
    prefs: IntradayPrefs,
    weights: list[tuple[str, float, float]],
) -> PortfolioAllocationSection:
    total = invested + cash
    if total <= 0:
        return PortfolioAllocationSection(
            core_pct=0.0,
            tactical_pct=0.0,
            cash_pct=0.0,
            policy_line="Connect broker or import holdings to see allocation",
        )
    cash_pct = round(100.0 * cash / total, 1)
    invested_pct = round(100.0 * invested / total, 1)
    tactical_cap = float(prefs.capital or 0) * float(prefs.allocation_pct or 0) / 100.0
    tactical_value = min(invested, tactical_cap) if tactical_cap > 0 else invested * 0.32
    core_value = max(0.0, invested - tactical_value)
    core_pct = round(100.0 * core_value / total, 1)
    tactical_pct = round(100.0 * tactical_value / total, 1)
    largest = max((pct for _, _, pct in weights), default=0.0)
    if largest > _CONCENTRATION_WARN_PCT:
        policy_line = f"vs policy: concentration review — largest holding {largest:.0f}%"
    elif cash_pct < 5.0 and invested > 0:
        policy_line = "vs policy: low cash buffer"
    else:
        policy_line = "vs policy: on track"
    if invested <= 0 and cash > 0:
        policy_line = "vs policy: cash only — no deployed holdings"
        core_pct = 0.0
        tactical_pct = 0.0
        cash_pct = 100.0
    elif invested > 0 and abs(core_pct + tactical_pct + cash_pct - 100.0) > 0.5:
        core_pct = round(invested_pct - tactical_pct, 1)
    return PortfolioAllocationSection(
        core_pct=core_pct,
        tactical_pct=tactical_pct,
        cash_pct=cash_pct,
        policy_line=policy_line,
    )


def _health_and_action(
    *,
    broker: BrokerSnapshot,
    count: int,
    has_saved: bool,
    attention: tuple[PortfolioAttentionItemModel, ...],
    stale: bool,
    stale_label: str,
    has_weights: bool,
) -> tuple[PortfolioHealthSection, PortfolioActionSection]:
    connected = broker.connected()
    if not connected and not has_saved:
        health = PortfolioHealthSection(
            badge_key="connect",
            badge_label="Connect broker",
            headline="Link Zerodha to see live holdings, health, and allocation.",
            supporting_reason="",
            stale_qualified=False,
            stale_label="",
        )
        action = PortfolioActionSection(
            primary_label="Connect Zerodha",
            primary_action="connect",
        )
    elif not connected and has_saved:
        health = PortfolioHealthSection(
            badge_key="connect",
            badge_label="Connect broker",
            headline=f"Saved portfolio with {count} holdings — connect for live sync.",
            supporting_reason="Broker offline — numbers reflect last saved snapshot.",
            stale_qualified=True,
            stale_label=stale_label or "Saved snapshot",
        )
        action = PortfolioActionSection(
            primary_label="Connect Zerodha",
            primary_action="connect",
            show_secondary=has_weights,
        )
    elif attention:
        lead = attention[0]
        headline = lead.reason if lead.symbol == "—" else (
            f"{len(attention)} item{'s' if len(attention) != 1 else ''} need your review."
        )
        supporting = (
            lead.reason
            if lead.symbol != "—" and len(attention) == 1
            else "Review concentration and sync flags below."
        )
        health = PortfolioHealthSection(
            badge_key="attention",
            badge_label="Needs attention",
            headline=headline,
            supporting_reason=supporting,
            stale_qualified=stale,
            stale_label=stale_label if stale else "",
        )
        action = PortfolioActionSection(
            primary_label=f"Review {len(attention)} item{'s' if len(attention) != 1 else ''}",
            primary_action="review",
        )
    else:
        health = PortfolioHealthSection(
            badge_key="healthy",
            badge_label="Healthy",
            headline=(
                f"Your portfolio is well diversified across {count} holding{'s' if count != 1 else ''}."
                if count
                else "Portfolio connected — no holdings deployed yet."
            ),
            supporting_reason=(
                "No concentration or sync issues today."
                if count
                else "Cash is available — deploy only when your plan confirms."
            ),
            stale_qualified=stale,
            stale_label=stale_label if stale else "",
        )
        action = PortfolioActionSection(
            primary_label="View all holdings",
            primary_action="holdings",
        )

    if stale and connected and not attention:
        action = PortfolioActionSection(
            primary_label="Sync now",
            primary_action="sync",
        )
    return health, action


def _depth_sections(
    *,
    allocation: PortfolioAllocationSection,
    attention: tuple[PortfolioAttentionItemModel, ...],
    weights: list[tuple[str, float, float]],
    portfolio_section: PortfolioSection | None,
    prefs: IntradayPrefs,
) -> tuple[PortfolioDepthSection, ...]:
    allocation_lines = (
        f"Core allocation is projected at {allocation.core_pct:.1f}% of total capital.",
        f"Tactical allocation is projected at {allocation.tactical_pct:.1f}% of total capital.",
        f"Cash buffer is {allocation.cash_pct:.1f}% of total capital.",
        allocation.policy_line,
    )
    if weights:
        top = sorted(weights, key=lambda row: -row[2])[:3]
        concentration_lines = tuple(
            f"{sym} represents {pct:.1f}% of deployed capital." for sym, _, pct in top
        )
    else:
        concentration_lines = ("No holdings to assess concentration.",)
    if attention:
        holding_health_lines = tuple(
            f"{item.flag_type}: {item.reason}" for item in attention
        )
    elif portfolio_section and portfolio_section.summary:
        holding_health_lines = (portfolio_section.summary,)
    else:
        holding_health_lines = ("All preview holdings are within guideline weights.",)
    policy_lines = (
        f"Capital policy tactical pool reference: ₹{prefs.capital:,.0f} at {prefs.allocation_pct:.0f}% allocation.",
        allocation.policy_line,
        "Sacred core holdings are excluded from tactical signals where configured.",
    )
    return (
        PortfolioDepthSection("Allocation", allocation_lines),
        PortfolioDepthSection("Concentration", concentration_lines),
        PortfolioDepthSection("Holding health", holding_health_lines),
        PortfolioDepthSection("Policy vs actual", policy_lines),
    )


def assemble_portfolio_overview(
    *,
    broker: BrokerSnapshot,
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    portfolio_section: PortfolioSection | None = None,
    journal_today_pnl: float | None = None,
) -> PortfolioOverviewViewModel:
    """Evaluate portfolio health and assemble the authoritative overview view model."""
    holdings = _holding_rows(portfolio)
    weights = _weights(holdings)
    invested = sum(value for _, value, _ in weights)
    cash = float(broker.available_cash_inr or 0.0) if broker.connected() else 0.0
    if broker.connected() and broker.portfolio_value_inr > 0:
        invested = float(broker.portfolio_value_inr)
    count = broker.holdings_count or len(holdings)
    attention = _attention_items(
        weights=weights,
        broker=broker,
        portfolio_section=portfolio_section,
    )
    attention_symbols = frozenset(
        item.symbol for item in attention if item.symbol not in ("—", "")
    )
    allocation = _allocation_section(
        invested=invested,
        cash=cash,
        prefs=prefs,
        weights=weights,
    )
    weakest_raw, strongest_raw = _holding_extremes(holdings)
    weakest_sym, weakest_pct = _split_standout(weakest_raw)
    strongest_sym, strongest_pct = _split_standout(strongest_raw)
    sorted_rows = sorted(weights, key=lambda row: -row[2])
    preview_rows = tuple(
        PortfolioPreviewRowModel(
            symbol=sym,
            weight_pct=round(pct, 1),
            health_label="Review" if sym in attention_symbols else "Healthy",
            health_key="review" if sym in attention_symbols else "healthy",
        )
        for sym, _, pct in sorted_rows[:5]
    )
    stale = broker.connected() and broker.state == "limited"
    stale_label = (
        portfolio_section.summary if stale and portfolio_section else "Data may be outdated"
    )
    has_saved = bool(holdings)
    connected = broker.connected()
    health, action = _health_and_action(
        broker=broker,
        count=count,
        has_saved=has_saved,
        attention=attention,
        stale=stale,
        stale_label=stale_label,
        has_weights=bool(weights),
    )
    day_pnl = (
        broker.today_unrealized_pnl_inr
        if broker.connected()
        else journal_today_pnl if journal_today_pnl is not None else _journal_unrealized(portfolio)
    )
    empty_attention = (
        "Nothing needs attention today."
        if connected or has_saved
        else "Connect broker to assess portfolio health."
    )
    return PortfolioOverviewViewModel(
        health=health,
        action=action,
        metrics=PortfolioMetricsSection(
            invested_inr=invested,
            cash_inr=cash,
            day_pnl_inr=day_pnl,
            holdings_count=count,
        ),
        attention_items=attention,
        attention_empty_message=empty_attention,
        allocation=allocation,
        standouts=PortfolioStandoutsSection(
            strongest_symbol=strongest_sym,
            strongest_pct=strongest_pct,
            weakest_symbol=weakest_sym,
            weakest_pct=weakest_pct,
        ),
        preview_rows=preview_rows,
        preview_more_count=max(0, len(sorted_rows) - len(preview_rows)),
        depth_sections=_depth_sections(
            allocation=allocation,
            attention=attention,
            weights=weights,
            portfolio_section=portfolio_section,
            prefs=prefs,
        ),
        broker_footer=_BROKER_FOOTER,
    )
