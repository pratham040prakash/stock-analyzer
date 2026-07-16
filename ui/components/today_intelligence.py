"""P0 Today Command Center — prose supporting intelligence below verdict."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any, Protocol

import streamlit as st

from analyzer.context_engine.models import ContextSnapshot
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.market_pulse_scan import MarketPulseReport
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.watchlist_pins import PinnedPlan
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.navigation import request_nav_tab

_EXPOSURE_WARN_PCT = 75.0


class _TodayStance(Protocol):
    key: str
    word: str
    cta_action: str


@dataclass(frozen=True)
class OpportunityView:
    ticker: str
    side: str
    confidence: int
    entry: float
    stop: float
    target: float
    rr: float | None


@dataclass(frozen=True)
class TodayCommandCenter:
    """Conclusions surfaced automatically below the verdict."""

    opportunity_name: str
    entry_direction: str
    selection_reason: str
    price_status: str
    market_gate: str
    market_support: str
    portfolio_lines: tuple[str, ...]
    risk_warnings: tuple[str, ...]
    next_watch: str
    ai_recommendation: str
    best_ticker: str


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _strip_md(text: str) -> str:
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", str(text or ""))
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    return cleaned.strip()


def _risk_reward(entry: float, stop: float, target: float) -> float | None:
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk <= 0:
        return None
    return round(reward / risk, 1)


def _normalize_symbol(symbol: str) -> str:
    return symbol.upper().replace(".NS", "").replace(".BO", "")


def _build_opportunity_views(
    pins: list[PinnedPlan],
    pulse: MarketPulseReport | None,
) -> list[OpportunityView]:
    stock_map = pulse.stock_map if pulse else {}
    rows: list[OpportunityView] = []
    for pin in pins[:6]:
        sym = _normalize_symbol(pin.symbol)
        pulse_row = stock_map.get(sym) or stock_map.get(pin.symbol)
        conf = 55
        if pulse_row is not None:
            conf = int(max(0, min(100, round(pulse_row.combined_score))))
        side = getattr(pin, "side", "LONG")
        rows.append(
            OpportunityView(
                ticker=sym,
                side=side,
                confidence=conf,
                entry=pin.entry,
                stop=pin.stop_loss,
                target=pin.target,
                rr=_risk_reward(pin.entry, pin.stop_loss, pin.target),
            )
        )
    return rows


def _pick_best(
    opportunities: list[OpportunityView],
    os_report: InvestmentOS,
) -> OpportunityView | None:
    if not opportunities:
        return None
    star = _normalize_symbol(os_report.starred_symbol or "")
    if star:
        for row in opportunities:
            if row.ticker == star:
                return row
    return opportunities[0]


def _pick_next_watch(
    opportunities: list[OpportunityView],
    best: OpportunityView | None,
) -> str:
    if not best or len(opportunities) < 2:
        return ""
    for row in opportunities:
        if row.ticker != best.ticker:
            verb = "buy above" if row.side.upper() == "LONG" else "sell below"
            return f"{row.ticker} — {verb} ₹{row.entry:,.0f} if {best.ticker} doesn't trigger"
    return ""


def _market_gate(snapshot: ContextSnapshot) -> str:
    regime = snapshot.market_regime.strip()
    mode = (snapshot.risk_mode or "NEUTRAL").replace("_", " ").lower()
    phase = snapshot.market_phase.strip()
    vol = snapshot.volatility_state.strip()

    parts: list[str] = []
    if regime:
        parts.append(regime)
    parts.append(f"{mode} session")
    if phase:
        parts.append(f"phase {phase}")
    if vol:
        parts.append(f"volatility {vol}")

    gate = " · ".join(parts)
    return gate


def _market_support_line(snapshot: ContextSnapshot, os_report: InvestmentOS) -> str:
    """Plain risk-on/off judgment from context + Market AI."""
    meta = dict(snapshot.metadata or {})
    if not meta.get("allow_new_entries", False):
        if snapshot.trading_restrictions:
            return _strip_md(snapshot.trading_restrictions[0])
        return "New entries not allowed yet — wait for the session gate."

    mode = snapshot.risk_mode
    if mode == "RISK-ON":
        return "Environment supports taking risk — stay inside your daily loss cap."
    if mode in ("RISK-OFF", "CLOSED"):
        return "Environment does not support new risk — protect capital."

    market = os_report.module("market")
    if market and market.detail:
        favor = _strip_md(market.detail.split("·")[0])
        if favor:
            return f"Tape is tradeable with caution — {favor[:72]}."
    return "Mixed tape — one setup only, size down."


def _selection_reason(best: OpportunityView | None, os_report: InvestmentOS) -> str:
    if not best:
        return ""
    star = _normalize_symbol(os_report.starred_symbol or "")
    stock = os_report.module("stock")
    strategy = os_report.module("strategy")
    if star and best.ticker == star:
        if strategy and strategy.headline:
            return f"Chosen because you starred it — {_strip_md(strategy.headline)[:72]}."
        if stock and stock.detail:
            return _strip_md(stock.detail)
        return "Chosen because you starred it on tonight's scan."
    if stock and stock.detail and "star" not in stock.detail.lower():
        return _strip_md(stock.detail)
    return f"Chosen as top setup on tonight's scan ({best.confidence}% pulse score)."


def _price_vs_entry(best: OpportunityView | None, pulse: MarketPulseReport | None) -> str:
    if not best or not pulse:
        return ""
    row = pulse.stock_map.get(best.ticker) or pulse.stock_map.get(f"{best.ticker}.NS")
    if not row or not row.price:
        return ""
    price = float(row.price)
    entry = best.entry
    src = row.ltp_source or "live"
    if best.side.upper() == "LONG":
        if price >= entry:
            return f"Now ₹{price:,.0f} ({src}) — at or above entry, trigger is live."
        gap = 100.0 * (entry - price) / price if price > 0 else 0.0
        return f"Now ₹{price:,.0f} ({src}) — {gap:.1f}% below entry, not triggered yet."
    if price <= entry:
        return f"Now ₹{price:,.0f} ({src}) — at or below entry, trigger is live."
    gap = 100.0 * (price - entry) / price if price > 0 else 0.0
    return f"Now ₹{price:,.0f} ({src}) — {gap:.1f}% above entry, not triggered yet."


def _holding_conflict(portfolio: ZerodhaImportResult | None, ticker: str) -> str:
    if not portfolio or not ticker:
        return ""
    target = ticker.upper()
    for holding in portfolio.holdings or []:
        sym = (holding.tradingsymbol or holding.kite_symbol or "").upper()
        if sym == target:
            qty = int(holding.quantity or 0)
            if qty > 0:
                return f"You already hold {qty} {ticker} — a new trade adds to book risk."
    return ""


def _size_blocked_line(os_report: InvestmentOS) -> str:
    risk = os_report.module("risk")
    if not risk or not risk.headline:
        return ""
    head = risk.headline.lower()
    if "blocked" not in head and "size blocked" not in head:
        return ""
    return _strip_md(risk.detail or risk.headline)


def _daily_risk_budget_inr(prefs: IntradayPrefs) -> float:
    capital = float(prefs.capital or 0)
    pct = float(prefs.max_risk_pct or 0)
    return capital * pct / 100.0 if capital > 0 and pct > 0 else 0.0


def _portfolio_lines(
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    *,
    snapshot: ContextSnapshot,
    os_report: InvestmentOS,
    best_ticker: str = "",
) -> tuple[str, ...]:
    """Constraint + exposure capacity — one block, no duplicate deployment %. """
    holdings = portfolio.holdings if portfolio and portfolio.holdings else []
    if not holdings:
        return ("Portfolio not linked — connect Zerodha before sizing new risk.",)

    lines: list[str] = []
    if best_ticker:
        conflict = _holding_conflict(portfolio, best_ticker)
        if conflict:
            lines.append(conflict)
    blocked = _size_blocked_line(os_report)
    if blocked:
        lines.append(blocked)

    risk_mod = os_report.module("risk")
    constraint = ""
    if risk_mod and risk_mod.headline and not blocked:
        constraint = risk_mod.headline
    else:
        exposure_pct, _invested = _portfolio_exposure(portfolio, prefs)
        if exposure_pct is not None and exposure_pct >= _EXPOSURE_WARN_PCT:
            constraint = (
                f"Book is {exposure_pct:.0f}% deployed — add only if this setup clears your rules."
            )
        elif snapshot.risk_mode in ("RISK-OFF", "CLOSED"):
            constraint = "Risk-off session — protect capital before chasing new entries."
        else:
            weakest = _weakest_holding(holdings)
            if weakest:
                constraint = f"Review {weakest} before adding fresh exposure."
            else:
                constraint = (
                    f"{len(holdings)} holding(s) on book — stay within your daily risk cap."
                )

    lines.append(constraint)
    exposure_pct, invested = _portfolio_exposure(portfolio, prefs)
    capital = float(prefs.capital or 0)
    if capital <= 0 or exposure_pct is None:
        return tuple(lines)

    constraint_lower = constraint.lower()
    if exposure_pct < _EXPOSURE_WARN_PCT:
        cash = max(0.0, capital - invested)
        capacity = f"Room to deploy — about ₹{cash:,.0f} within your stated capital."
        if "cash" not in constraint_lower and "deploy" not in constraint_lower:
            lines.append(capacity)
    elif "deployed" not in constraint_lower and "%" not in constraint_lower:
        if exposure_pct >= 95:
            lines.append(f"Exposure at {exposure_pct:.0f}% — effectively fully invested.")
        else:
            lines.append(
                f"Exposure at {exposure_pct:.0f}% — limited room for another full-sized trade."
            )
    return tuple(lines[:3])


def _portfolio_exposure(
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
) -> tuple[float | None, float]:
    holdings = portfolio.holdings if portfolio and portfolio.holdings else []
    invested = 0.0
    for holding in holdings:
        ltp = holding.last_price or holding.average_price or 0.0
        invested += float(holding.quantity or 0) * float(ltp)
    capital = float(prefs.capital or 0)
    exposure_pct = round(100.0 * invested / capital, 1) if capital > 0 else None
    return exposure_pct, invested


def _weakest_holding(holdings: list[ZerodhaHolding]) -> str:
    scored: list[tuple[str, float]] = []
    for holding in holdings:
        if holding.pnl is None or not holding.average_price or not holding.quantity:
            continue
        cost = float(holding.average_price) * float(holding.quantity)
        if cost <= 0:
            continue
        pct = 100.0 * float(holding.pnl) / cost
        scored.append((holding.tradingsymbol or holding.kite_symbol or "", pct))
    if not scored:
        return ""
    scored.sort(key=lambda item: item[1])
    sym, pct = scored[0]
    return f"{sym} ({pct:+.1f}%)" if sym else ""


def _risk_warning_lines(
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    *,
    broker_connected: bool,
) -> tuple[str, ...]:
    lines: list[str] = []
    if not broker_connected:
        lines.append("Broker offline — today's call can't use live holdings.")
    if mis.loss_streak_days >= 2:
        lines.append(f"{mis.loss_streak_days} losing days in a row — pause protects capital.")
    elif mis.loss_streak_days == 1:
        lines.append("One losing day — keep today's size smaller than usual.")
    for flag in (mis.flags or ())[:2]:
        text = str(flag).strip()
        if text and text not in lines:
            lines.append(text)
    for restriction in snapshot.trading_restrictions[:2]:
        text = str(restriction).strip()
        if text and text not in lines:
            lines.append(text)
    return tuple(lines[:3])


def _opportunity_lines(best: OpportunityView | None) -> tuple[str, str]:
    if not best:
        return (
            "No staged setup",
            "Run tonight's scan on Suggestions, or wait for a clearer tape.",
        )
    side = best.side.upper()
    verb = "Long" if side == "LONG" else "Short"
    rr_note = f"{best.rr}R" if best.rr else "check reward vs risk"
    name = f"{best.ticker} — {verb} setup ({best.confidence}% confidence)"
    if side == "LONG":
        direction = (
            f"Buy above ₹{best.entry:,.0f} · stop ₹{best.stop:,.0f} · "
            f"target ₹{best.target:,.0f} · {rr_note}"
        )
    else:
        direction = (
            f"Sell below ₹{best.entry:,.0f} · stop ₹{best.stop:,.0f} · "
            f"target ₹{best.target:,.0f} · {rr_note}"
        )
    return name, direction


def _ai_recommendation(
    state: _TodayStance,
    *,
    os_report: InvestmentOS,
    best: OpportunityView | None,
    risk_warnings: tuple[str, ...],
    prefs: IntradayPrefs,
) -> str:
    step = _strip_md(os_report.next_step or "")
    if step and state.key in ("trade", "wait", "pause"):
        if state.key == "trade" and best:
            budget = _daily_risk_budget_inr(prefs)
            if budget > 0 and "max loss" not in step.lower():
                return f"{step} Size within ₹{budget:,.0f} max loss."
            return step
        return step

    if state.key == "connect":
        return "One Zerodha link unlocks portfolio-aware sizing and today's call."
    if state.key == "rest":
        return "Rest today — review your week and stage tomorrow's setups after close."
    if state.key == "pause":
        if risk_warnings:
            return f"Protect capital today — {risk_warnings[0]}"
        return "Protect capital today — conditions don't justify new risk."
    if state.key == "trade" and best:
        budget = _daily_risk_budget_inr(prefs)
        if budget > 0:
            return (
                f"Size {best.ticker} within ₹{budget:,.0f} max loss — "
                f"the plan shows entry, stop, and timing."
            )
        return f"Size {best.ticker} within your risk rules — the plan shows exact levels."
    if state.key == "trade":
        return "Use the plan for exact entry, stop, and timing before placing the order."
    if state.key == "wait" and best:
        return (
            f"Let {best.ticker} confirm near ₹{best.entry:,.0f} — "
            f"don't chase if it runs without you."
        )
    if state.key == "wait" and risk_warnings:
        return f"Stay patient — {risk_warnings[0]}"
    return "Stay patient — wait for price to confirm before committing capital."


def build_today_command_center(
    *,
    state: _TodayStance,
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    pins: list[PinnedPlan],
    pulse: MarketPulseReport | None,
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    broker_connected: bool,
) -> TodayCommandCenter:
    opportunities = _build_opportunity_views(pins, pulse)
    best = _pick_best(opportunities, os_report)
    opportunity_name, entry_direction = _opportunity_lines(best)
    risk_warnings = _risk_warning_lines(
        mis,
        snapshot,
        broker_connected=broker_connected,
    )
    if state.key == "connect" and risk_warnings:
        risk_warnings = tuple(
            line for line in risk_warnings if "broker offline" not in line.lower()
        )
    return TodayCommandCenter(
        opportunity_name=opportunity_name,
        entry_direction=entry_direction,
        selection_reason=_selection_reason(best, os_report),
        price_status=_price_vs_entry(best, pulse),
        market_gate=_market_gate(snapshot),
        market_support=_market_support_line(snapshot, os_report),
        portfolio_lines=_portfolio_lines(
            portfolio,
            prefs,
            snapshot=snapshot,
            os_report=os_report,
            best_ticker=best.ticker if best else "",
        ),
        risk_warnings=risk_warnings,
        next_watch=_pick_next_watch(opportunities, best),
        ai_recommendation=_ai_recommendation(
            state,
            os_report=os_report,
            best=best,
            risk_warnings=risk_warnings,
            prefs=prefs,
        ),
        best_ticker=best.ticker if best else "",
    )


def _intel_block(*, label: str, lines: list[str], tone: str = "") -> str:
    filtered = [line for line in lines if line.strip()]
    if not filtered:
        return ""
    tone_cls = f" vc-intel-{tone}" if tone else ""
    body = "".join(f'<p class="vc-intel-line{tone_cls}">{_esc(line)}</p>' for line in filtered)
    return (
        f'<section class="vc-intel-block">'
        f'<p class="vc-intel-label">{_esc(label)}</p>'
        f"{body}"
        f"</section>"
    )


def _go_symbol(symbol: str) -> None:
    sym = symbol.replace(".NS", "").replace(".BO", "").strip()
    request_nav_tab(
        "Single Stock",
        single_ticker=sym,
        bt_ticker=sym,
        intraday_ticker=sym,
        alpha_ai_ticker=sym,
    )


def render_today_command_center(
    *,
    state: _TodayStance,
    market: str,
    cached: dict[str, Any],
    broker_connected: bool,
) -> None:
    del market
    snapshot: ContextSnapshot = cached["snapshot"]
    if not isinstance(snapshot, ContextSnapshot):
        from ui.components.home_dashboard import _snapshot_from_cache

        snapshot = _snapshot_from_cache(cached["snapshot"])

    center = build_today_command_center(
        state=state,
        snapshot=snapshot,
        mis=cached["mis"],
        os_report=cached["os_report"],
        pins=cached["pins"],
        pulse=cached.get("pulse"),
        portfolio=cached.get("portfolio"),
        prefs=cached["prefs"],
        broker_connected=broker_connected,
    )

    blocks = [
        _intel_block(
            label="Opportunity",
            lines=[
                line
                for line in (
                    center.opportunity_name,
                    center.entry_direction,
                    center.selection_reason,
                    center.price_status,
                )
                if line
            ],
            tone="high" if state.key == "trade" else "",
        ),
        _intel_block(
            label="Market",
            lines=[line for line in (center.market_gate, center.market_support) if line],
        ),
        _intel_block(
            label="Portfolio",
            lines=list(center.portfolio_lines),
            tone="warn" if center.portfolio_lines and "not linked" in center.portfolio_lines[0].lower() else "",
        ),
        _intel_block(
            label="Risk",
            lines=list(center.risk_warnings),
            tone="warn" if center.risk_warnings else "",
        ),
        _intel_block(
            label="Next watch",
            lines=[center.next_watch] if center.next_watch else [],
        ),
        _intel_block(
            label="Do next",
            lines=[center.ai_recommendation],
            tone="high" if state.key == "trade" else "",
        ),
    ]

    html_body = "".join(block for block in blocks if block)
    st.markdown(f'<div class="vc-intel-stack">{html_body}</div>', unsafe_allow_html=True)

    st.markdown('<div class="vc-intel-actions">', unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    with a1:
        if center.best_ticker and st.button("Review setup", key="vc_intel_review", use_container_width=True):
            _go_symbol(center.best_ticker)
    with a2:
        if st.button("All picks", key="vc_intel_picks", use_container_width=True):
            request_nav_tab("Suggestions")
    with a3:
        if st.button("Portfolio", key="vc_intel_portfolio", use_container_width=True):
            request_nav_tab("My Portfolio")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<p class="vc-intel-foot">Command center</p>', unsafe_allow_html=True)


# Backward-compatible alias for imports/tests in transition.
render_today_intelligence = render_today_command_center
