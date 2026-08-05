"""P0 Today Command Center — prose supporting intelligence below verdict."""
# APEX-012-LIFECYCLE: QUARANTINED

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any, Protocol

import streamlit as st

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.market_pulse_scan import MarketPulseReport
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.watchlist_pins import PinnedPlan
from analyzer.zerodha import ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.dashboard_pipeline import (
    decision_reason,
    fmt_inr,
    holding_extremes,
    portfolio_health_label,
    portfolio_metrics,
    watch_bullets,
)
from ui.navigation import request_nav_tab


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
    breadth = snapshot.market_breadth.strip()
    liquidity = snapshot.liquidity_state.strip()

    parts: list[str] = []
    if regime:
        parts.append(regime)
    parts.append(f"{mode} session")
    if phase:
        parts.append(f"phase {phase}")
    if vol:
        parts.append(f"volatility {vol}")
    if breadth:
        parts.append(f"breadth {breadth}")
    if liquidity:
        parts.append(f"liquidity {liquidity}")
    industries = dict(snapshot.industry_strength or {})
    industry_note = str(industries.get("note", "") or "").strip()
    industry_leader = str(industries.get("leader", "") or "").strip()
    if industry_note:
        parts.append(f"industry {industry_note}")
    elif industry_leader and industry_leader.lower() != "unknown":
        parts.append(f"industry leader {industry_leader}")
    sectors = dict(snapshot.sector_strength or {})
    sector_leader = str(sectors.get("leader", "") or "").strip()
    if sector_leader and sector_leader.lower() != "unknown":
        parts.append(f"sector leader {sector_leader}")

    return " · ".join(parts)


def _market_support_line(snapshot: ContextSnapshot, os_report: InvestmentOS) -> str:
    """Plain risk-on/off judgment from context + Market AI + Sector module."""
    parts: list[str] = []
    meta = dict(snapshot.metadata or {})
    if not meta.get("allow_new_entries", False):
        if snapshot.trading_restrictions:
            parts.append(_strip_md(snapshot.trading_restrictions[0]))
        else:
            parts.append("New entries not allowed yet — wait for the session gate.")
    elif snapshot.risk_mode == "RISK-ON":
        parts.append("Environment supports taking risk — stay inside your daily loss cap.")
    elif snapshot.risk_mode in ("RISK-OFF", "CLOSED"):
        parts.append("Environment does not support new risk — protect capital.")
    else:
        market = os_report.module("market")
        if market and market.detail:
            favor = _strip_md(market.detail.split("·")[0])
            if favor:
                parts.append(f"Tape is tradeable with caution — {favor[:72]}.")
            else:
                parts.append("Mixed tape — one setup only, size down.")
        else:
            parts.append("Mixed tape — one setup only, size down.")

    sector = os_report.module("sector")
    if sector and sector.headline and sector.headline != "No sector data yet":
        sector_line = _strip_md(sector.headline)
        if sector.detail:
            sector_line = f"{sector_line} — {_strip_md(sector.detail)[:96]}"
        parts.append(f"Sectors: {sector_line}")

    return " · ".join(parts)


def _selection_reason(best: OpportunityView | None, os_report: InvestmentOS) -> str:
    if not best:
        return ""
    star = _normalize_symbol(os_report.starred_symbol or "")
    stock = os_report.module("stock")
    strategy = os_report.module("strategy")
    execution = os_report.module("execution")
    if star and best.ticker == star:
        if strategy and strategy.detail:
            return f"Chosen because you starred it — {_strip_md(strategy.detail)[:96]}."
        if strategy and strategy.headline:
            return f"Chosen because you starred it — {_strip_md(strategy.headline)[:96]}."
        if stock and stock.detail:
            return _strip_md(stock.detail)
        return "Chosen because you starred it on tonight's scan."
    if strategy and strategy.detail:
        return _strip_md(strategy.detail)
    if stock and stock.detail and "star" not in stock.detail.lower():
        return _strip_md(stock.detail)
    if execution and execution.headline:
        return f"Execution plan — {_strip_md(execution.headline)[:96]}."
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
    what = _strip_md(getattr(row, "what_to_do", "") or "")
    if best.side.upper() == "LONG":
        if price >= entry:
            status = f"Now ₹{price:,.0f} ({src}) — at or above entry, trigger is live."
        else:
            gap = 100.0 * (entry - price) / price if price > 0 else 0.0
            status = f"Now ₹{price:,.0f} ({src}) — {gap:.1f}% below entry, not triggered yet."
    elif price <= entry:
        status = f"Now ₹{price:,.0f} ({src}) — at or below entry, trigger is live."
    else:
        gap = 100.0 * (price - entry) / price if price > 0 else 0.0
        status = f"Now ₹{price:,.0f} ({src}) — {gap:.1f}% above entry, not triggered yet."
    if what:
        return f"{status} Pulse: {what[:96]}."
    return status


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
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    best_ticker: str = "",
    journal_today_pnl: float | None = None,
) -> tuple[str, ...]:
    """Constraint + exposure capacity — one block, no duplicate deployment %."""
    holdings = portfolio.holdings if portfolio and portfolio.holdings else []
    if not holdings:
        return ("Portfolio not linked — connect Zerodha before sizing new risk.",)

    metrics = portfolio_metrics(portfolio, prefs, journal_today_pnl=journal_today_pnl)
    health_label, health_detail = portfolio_health_label(snapshot, mis, os_report)
    weakest, strongest = holding_extremes(holdings)

    lines: list[str] = []
    lines.append(f"Portfolio is {health_label}. {_strip_md(health_detail)}")
    if journal_today_pnl is not None:
        lines.append(
            f"Today's Journal P/L: {fmt_inr(journal_today_pnl, signed=True)} · "
            f"Exposure {metrics['exposure_pct']}% · "
            f"Weakest: {weakest} · Strongest: {strongest}"
        )
    else:
        lines.append(
            f"Exposure {metrics['exposure_pct']}% · "
            f"Weakest: {weakest} · Strongest: {strongest}"
        )
    if metrics["allocation"]:
        lines.append("Allocation: " + ", ".join(metrics["allocation"]))

    if best_ticker:
        conflict = _holding_conflict(portfolio, best_ticker)
        if conflict:
            lines.append(conflict)
    blocked = _size_blocked_line(os_report)
    if blocked:
        lines.append(blocked)

    risk_mod = os_report.module("risk")
    risk_head = _strip_md(risk_mod.headline) if risk_mod and risk_mod.headline else ""
    if risk_head and risk_head not in _strip_md(health_detail) and not blocked:
        lines.append(risk_head)
    elif snapshot.risk_mode in ("RISK-OFF", "CLOSED") and "Risk-off" not in " ".join(lines):
        lines.append("Risk-off session — protect capital before chasing new entries.")

    return tuple(lines[:5])


def _risk_warning_lines(
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    *,
    broker: BrokerSnapshot,
) -> tuple[str, ...]:
    lines: list[str] = []
    if not broker.connected():
        detail = broker.error_message or "Connect Zerodha to pull live positions."
        lines.append(f"Broker offline — {detail}")
    elif broker.last_sync_at or broker.holdings_count:
        sync = broker.last_sync_at or "Recently synced"
        holdings_note = f" · {broker.holdings_count} holding(s)" if broker.holdings_count else ""
        lines.append(f"Broker synced — {sync}{holdings_note}")
    if mis.loss_streak_days >= 2:
        lines.append(f"{mis.loss_streak_days} losing days in a row — pause protects capital.")
    elif mis.loss_streak_days == 1:
        lines.append("One losing day — keep today's size smaller than usual.")
    if mis.mtf_summary:
        lines.append(f"MTF: {_strip_md(mis.mtf_summary)}")
    if mis.flow_summary:
        lines.append(f"Flow: {_strip_md(mis.flow_summary)}")
    if mis.synthesis_summary:
        text = _strip_md(mis.synthesis_summary)
        if text and text not in lines:
            lines.append(text)
    for flag in (mis.flags or ())[:2]:
        text = str(flag).strip()
        if text and text not in lines:
            lines.append(text)
    for restriction in snapshot.trading_restrictions[:2]:
        text = str(restriction).strip()
        if text and text not in lines:
            lines.append(text)
    return tuple(lines[:5])


def _opportunity_lines(
    best: OpportunityView | None,
    *,
    os_report: InvestmentOS,
) -> tuple[str, str]:
    if not best:
        return (
            "No staged setup",
            "Run tonight's scan on Suggestions, or wait for a clearer tape.",
        )
    side = best.side.upper()
    verb = "Long" if side == "LONG" else "Short"
    rr_note = f"{best.rr}R" if best.rr else "check reward vs risk"
    reward_amt = abs(best.target - best.entry)
    risk_amt = abs(best.entry - best.stop)
    reward_risk = f"₹{reward_amt:,.0f} ({rr_note}) · ₹{risk_amt:,.0f} stop"
    name = f"{best.ticker} — {verb} setup ({best.confidence}% confidence)"
    execution = os_report.module("execution")
    if execution and execution.headline:
        direction = f"{_strip_md(execution.headline)} · {reward_risk}"
    elif side == "LONG":
        direction = (
            f"Buy above ₹{best.entry:,.0f} · stop ₹{best.stop:,.0f} · "
            f"target ₹{best.target:,.0f} · {reward_risk}"
        )
    else:
        direction = (
            f"Sell below ₹{best.entry:,.0f} · stop ₹{best.stop:,.0f} · "
            f"target ₹{best.target:,.0f} · {reward_risk}"
        )
    return name, direction


def _ai_recommendation(
    state: _TodayStance,
    *,
    os_report: InvestmentOS,
    mis: MisTradeAdvisory,
    decision: DecisionArtifact | None,
    best: OpportunityView | None,
    risk_warnings: tuple[str, ...],
    prefs: IntradayPrefs,
) -> str:
    step = _strip_md(os_report.next_step or "")
    if step:
        if state.key == "trade" and best:
            budget = float(os_report.max_loss_inr or 0) or _daily_risk_budget_inr(prefs)
            if budget > 0 and "max loss" not in step.lower():
                return f"{step} Size within ₹{budget:,.0f} max loss."
        return step

    if state.key == "rest":
        review = os_report.module("review")
        if review and review.detail:
            return _strip_md(review.detail)
        if review and review.headline:
            return _strip_md(review.headline)
        return "Rest today — review your week and stage tomorrow's setups after close."
    if state.key == "connect":
        return "One Zerodha link unlocks portfolio-aware sizing and today's call."
    if state.key == "pause":
        reason = decision_reason(decision)
        if reason:
            return _strip_md(reason)[:160]
        if mis.summary:
            return _strip_md(mis.summary)
        if risk_warnings:
            return f"Protect capital today — {risk_warnings[0]}"
        return "Protect capital today — conditions don't justify new risk."
    if state.key == "trade" and best:
        budget = float(os_report.max_loss_inr or 0) or _daily_risk_budget_inr(prefs)
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


def _next_watch_lines(
    opportunities: list[OpportunityView],
    best: OpportunityView | None,
    *,
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    pins: list[PinnedPlan],
) -> tuple[str, ...]:
    alt = _pick_next_watch(opportunities, best)
    tickers = [(row.ticker, row.entry) for row in opportunities]
    bullets = watch_bullets(mis, snapshot, opportunity_tickers=tickers, pins=pins)
    lines: list[str] = []
    if alt:
        lines.append(alt)
    for bullet in bullets:
        if bullet not in lines:
            lines.append(bullet)
    return tuple(lines[:3])


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
    broker: BrokerSnapshot,
    journal_today_pnl: float | None = None,
    decision: DecisionArtifact | None = None,
) -> TodayCommandCenter:
    opportunities = _build_opportunity_views(pins, pulse)
    best = _pick_best(opportunities, os_report)
    opportunity_name, entry_direction = _opportunity_lines(best, os_report=os_report)
    risk_warnings = _risk_warning_lines(mis, snapshot, broker=broker)
    if state.key == "connect":
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
            mis=mis,
            os_report=os_report,
            best_ticker=best.ticker if best else "",
            journal_today_pnl=journal_today_pnl,
        ),
        risk_warnings=risk_warnings,
        next_watch=" · ".join(
            _next_watch_lines(opportunities, best, mis=mis, snapshot=snapshot, pins=pins)
        ),
        ai_recommendation=_ai_recommendation(
            state,
            os_report=os_report,
            mis=mis,
            decision=decision,
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


def _intel_blocks_for_center(
    center: TodayCommandCenter,
    state: _TodayStance,
) -> dict[str, str]:
    return {
        "opportunity": _intel_block(
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
        "market": _intel_block(
            label="Market",
            lines=[line for line in (center.market_gate, center.market_support) if line],
        ),
        "portfolio": _intel_block(
            label="Portfolio",
            lines=list(center.portfolio_lines),
            tone="warn" if center.portfolio_lines and "not linked" in center.portfolio_lines[0].lower() else "",
        ),
        "risk": _intel_block(
            label="Risk",
            lines=list(center.risk_warnings),
            tone="warn" if center.risk_warnings else "",
        ),
        "next_watch": _intel_block(
            label="Next watch",
            lines=[line for line in center.next_watch.split(" · ") if line.strip()],
        ),
        "do_next": _intel_block(
            label="Do next",
            lines=[center.ai_recommendation],
            tone="high" if state.key == "trade" else "",
        ),
    }


def intel_stack_html(
    center: TodayCommandCenter,
    state: _TodayStance,
    *,
    sections: tuple[str, ...],
) -> str:
    block_map = _intel_blocks_for_center(center, state)
    blocks = [block_map[key] for key in sections if key in block_map]
    body = "".join(block for block in blocks if block)
    if not body:
        return ""
    return f'<div class="vc-intel-stack vc-intel-stack-hero">{body}</div>'


def render_today_command_center(
    *,
    state: _TodayStance,
    market: str,
    cached: dict[str, Any],
    broker: BrokerSnapshot,
    decision: DecisionArtifact | None = None,
    sections: tuple[str, ...] | None = None,
    include_actions: bool = False,
    center: TodayCommandCenter | None = None,
    review_symbol: str | None = None,
) -> None:
    del market
    snapshot: ContextSnapshot = cached["snapshot"]
    if not isinstance(snapshot, ContextSnapshot):
        from ui.components.home_dashboard import _snapshot_from_cache

        snapshot = _snapshot_from_cache(cached["snapshot"])

    if center is None:
        center = build_today_command_center(
            state=state,
            snapshot=snapshot,
            mis=cached["mis"],
            os_report=cached["os_report"],
            pins=cached["pins"],
            pulse=cached.get("pulse"),
            portfolio=cached.get("portfolio"),
            prefs=cached["prefs"],
            broker=broker,
            journal_today_pnl=cached.get("journal_today_pnl"),
            decision=decision,
        )

    block_map = _intel_blocks_for_center(center, state)
    order = sections or ("opportunity", "do_next", "risk", "market", "portfolio", "next_watch")
    blocks = [block_map[key] for key in order if key in block_map]

    html_body = "".join(block for block in blocks if block)
    if html_body:
        st.markdown(f'<div class="vc-intel-stack">{html_body}</div>', unsafe_allow_html=True)

    if not include_actions:
        return

    st.markdown('<div class="vc-intel-actions">', unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    from ui.components.decision_card import resolve_hero_review_nav_symbol

    nav_symbol = resolve_hero_review_nav_symbol(
        review_symbol=review_symbol,
        legacy_best_ticker=center.best_ticker,
    )
    with a1:
        if nav_symbol and st.button("Review setup", key="vc_intel_review", use_container_width=True):
            _go_symbol(nav_symbol)
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
