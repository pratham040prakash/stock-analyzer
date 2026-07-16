"""Home investing assistant — five questions, action before data."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from analyzer.broker_truth.learning import resolve_learning_outcomes
from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict
from analyzer.intraday_prefs import IntradayPrefs, load_intraday_prefs
from analyzer.markets import is_india_market
from analyzer.unified_search import unified_search
from analyzer.investment_os import InvestmentOS, build_investment_os
from analyzer.market_pulse_scan import MarketPulseReport
from analyzer.mis_trade_advisory import MisTradeAdvisory, build_mis_trade_advisory
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from analyzer.pulse_cache import load_pulse_cache_with_stale
from analyzer.trade_journal import load_journal_entries
from analyzer.watchlist_pins import PinnedPlan, load_pinned_plans
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.broker.state import BrokerSnapshot, load_broker_snapshot
from ui.navigation import request_nav_tab
from ui.theme import HOME_UI_CSS

IST = ZoneInfo("Asia/Kolkata")
PULSE_CACHE_TTL = 86_400

_VERDICT_CLASS = {
    DecisionVerdict.ACT: "dash-verdict-act",
    DecisionVerdict.WAIT: "dash-verdict-wait",
    DecisionVerdict.PASS: "dash-verdict-pass",
    DecisionVerdict.REDUCE: "dash-verdict-reduce",
    DecisionVerdict.DEFENSIVE: "dash-verdict-defensive",
}


@dataclass
class OpportunityRow:
    ticker: str
    confidence: int
    expected_reward: str
    risk: str
    entry: float
    stop: float
    target: float
    side: str


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _risk_reward(entry: float, stop: float, target: float) -> float | None:
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk <= 0:
        return None
    return round(reward / risk, 2)


def _fmt_inr(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    if signed:
        return f"{'+' if value >= 0 else ''}₹{value:,.0f}"
    return f"₹{value:,.0f}"


def _load_pulse(market: str, period: str) -> MarketPulseReport | None:
    key = f"pulse_{period}_{market}"
    report, _fresh = load_pulse_cache_with_stale(key, PULSE_CACHE_TTL)
    return report


def _pick_decision(
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
) -> tuple[DecisionArtifact | None, str]:
    """Prefer starred equity decision; fall back to session MIS decision."""
    os_art = getattr(os_report, "decision_artifact", None)
    mis_art = getattr(mis, "decision_artifact", None)
    if os_art and os_report.starred_symbol:
        return os_art, "equity"
    if mis_art:
        return mis_art, "session"
    if os_art:
        return os_art, "equity"
    return None, "none"


def _evidence_summary(decision: DecisionArtifact | None, *, limit: int = 6) -> list[str]:
    if not decision or not decision.evidence_packet_id:
        return []
    try:
        from analyzer.evidence_engine import fetch_evidence_packet

        packet = fetch_evidence_packet(decision.evidence_packet_id)
        if not packet:
            return []
        lines: list[str] = []
        for item in packet.items[:limit]:
            label = str(item.label or item.category.value)
            value = str(item.value or "")[:100]
            lines.append(f"{label}: {value}")
        if packet.conflicts:
            lines.append(f"{len(packet.conflicts)} conflicting signal(s) noted")
        if packet.gaps:
            lines.append(f"{len(packet.gaps)} data gap(s)")
        return lines
    except Exception:
        return []


def _build_opportunities(
    pins: list[PinnedPlan],
    pulse: MarketPulseReport | None,
) -> list[OpportunityRow]:
    stock_map = pulse.stock_map if pulse else {}
    rows: list[OpportunityRow] = []
    for p in pins[:5]:
        sym = p.symbol.upper().replace(".NS", "")
        pulse_row = stock_map.get(sym) or stock_map.get(p.symbol)
        conf = 55
        if pulse_row is not None:
            conf = int(max(0, min(100, round(pulse_row.combined_score))))
        rr = _risk_reward(p.entry, p.stop_loss, p.target)
        reward = abs(p.target - p.entry)
        risk_amt = abs(p.entry - p.stop_loss)
        rows.append(
            OpportunityRow(
                ticker=sym,
                confidence=conf,
                expected_reward=f"₹{reward:,.0f} ({rr or '—'}R)",
                risk=f"₹{risk_amt:,.0f} stop",
                entry=p.entry,
                stop=p.stop_loss,
                target=p.target,
                side=getattr(p, "side", "LONG"),
            )
        )
    return rows


def _portfolio_metrics(
    imp: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    *,
    journal_today_pnl: float | None,
) -> dict[str, Any]:
    holdings = imp.holdings if imp and imp.holdings else []
    invested = 0.0
    unrealized = 0.0
    allocation: list[tuple[str, float]] = []
    for h in holdings:
        ltp = h.last_price or h.average_price or 0.0
        value = float(h.quantity or 0) * float(ltp)
        invested += value
        if h.pnl is not None:
            unrealized += float(h.pnl)
        if value > 0:
            allocation.append((h.tradingsymbol or h.kite_symbol, value))
    allocation.sort(key=lambda x: x[1], reverse=True)
    capital = float(prefs.capital or 0)
    cash = max(0.0, capital - invested) if capital else 0.0
    exposure_pct = round(100.0 * invested / capital, 1) if capital > 0 else None
    max_risk = capital * float(prefs.max_risk_pct) / 100.0 if capital else 0.0
    alloc_lines = []
    total = invested or 1.0
    for sym, val in allocation[:4]:
        alloc_lines.append(f"{sym} {100.0 * val / total:.0f}%")
    return {
        "today_pnl": journal_today_pnl if journal_today_pnl is not None else unrealized,
        "today_pnl_source": "journal" if journal_today_pnl is not None else "holdings",
        "cash": cash,
        "exposure_pct": exposure_pct,
        "invested": invested,
        "risk_budget": max_risk,
        "allocation": alloc_lines,
        "holding_count": len(holdings),
    }


def _journal_pnl_for_date(trade_date: str) -> float | None:
    total = 0.0
    found = False
    for entry in load_journal_entries(limit=60):
        if entry.trade_date == trade_date and entry.pnl_inr is not None:
            total += float(entry.pnl_inr)
            found = True
    return total if found else None


def _conf_label(conf: float | int) -> tuple[str, str]:
    pct = int(round(float(conf)))
    if pct >= 70:
        return "High confidence", "assist-conf-high"
    if pct >= 40:
        return "Medium confidence", "assist-conf-medium"
    return "Low confidence", "assist-conf-low"


def _conf_numeric(decision: DecisionArtifact | None, snapshot: ContextSnapshot) -> int:
    if decision:
        raw = float(decision.confidence)
        return int(round(raw * 100)) if raw <= 1.0 else int(round(raw))
    raw = float(snapshot.confidence or 0.0)
    return int(round(raw * 100)) if raw <= 1.0 else int(round(raw))


def _verdict_conclusion(
    verdict: str,
    *,
    os_report: InvestmentOS,
    mis: MisTradeAdvisory,
) -> str:
    mapping = {
        "ACT": "Open today's trade plan and size the trade within your risk budget.",
        "WAIT": "Hold off on new trades until the setup clears.",
        "PASS": "Skip new trades today — protect your capital.",
        "REDUCE": "Trim exposure and avoid adding fresh risk.",
        "DEFENSIVE": "Stay defensive — no new entries until conditions improve.",
    }
    if os_report.next_step:
        return os_report.next_step
    return mapping.get(verdict, mis.summary or "Review your plan before acting.")


def _levels_for_symbol(symbol: str, pins: list[PinnedPlan]) -> tuple[float, float, float] | None:
    if not symbol:
        return None
    sym = symbol.upper().replace(".NS", "").replace(".BO", "")
    for pin in pins:
        pin_sym = pin.symbol.upper().replace(".NS", "").replace(".BO", "")
        if pin_sym == sym:
            return pin.entry, pin.stop_loss, pin.target
    return None


def _portfolio_health(
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
) -> tuple[str, str, str]:
    """Qualitative health from existing engine outputs — no synthetic score."""
    risk_mod = os_report.module("risk")
    flag_count = len(mis.flags or ())
    mode = snapshot.risk_mode or "NEUTRAL"

    if mode == "CLOSED" or (risk_mod and risk_mod.status in ("warn", "off")):
        label, css = "High Risk", "assist-conf-low"
    elif mode == "RISK-OFF" or flag_count >= 2 or (risk_mod and risk_mod.status == "wait"):
        label, css = "Needs Review", "assist-conf-medium"
    else:
        label, css = "Healthy", "assist-conf-high"

    detail = risk_mod.headline if risk_mod and risk_mod.headline else os_report.next_step
    if not detail and mis.flags:
        detail = mis.flags[0]
    if not detail:
        detail = f"Market is {mode.lower().replace('_', ' ')} — stay within your plan."
    return label, css, detail


def _holding_pnl_pct(h: ZerodhaHolding) -> float | None:
    if h.pnl is None or not h.average_price or not h.quantity:
        return None
    cost = float(h.average_price) * float(h.quantity)
    if cost <= 0:
        return None
    return 100.0 * float(h.pnl) / cost


def _holding_extremes(holdings: list[ZerodhaHolding]) -> tuple[str, str]:
    scored: list[tuple[str, float]] = []
    for h in holdings:
        pct = _holding_pnl_pct(h)
        if pct is None:
            continue
        scored.append((h.tradingsymbol or h.kite_symbol or "—", pct))
    if not scored:
        return "—", "—"
    scored.sort(key=lambda x: x[1])
    weakest = f"{scored[0][0]} ({scored[0][1]:+.1f}%)"
    strongest = f"{scored[-1][0]} ({scored[-1][1]:+.1f}%)"
    return weakest, strongest


def _best_opportunity(
    opportunities: list[OpportunityRow],
    os_report: InvestmentOS,
) -> OpportunityRow | None:
    if not opportunities:
        return None
    star = (os_report.starred_symbol or "").upper().replace(".NS", "")
    if star:
        for row in opportunities:
            if row.ticker.upper() == star:
                return row
    return opportunities[0]


def _watch_bullets(
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    opportunities: list[OpportunityRow],
    pins: list[PinnedPlan],
) -> list[str]:
    bullets: list[str] = []
    for flag in (mis.flags or ())[:2]:
        bullets.append(flag)
    for restriction in snapshot.trading_restrictions[:2]:
        if restriction not in bullets:
            bullets.append(restriction)
    for row in opportunities[:2]:
        line = f"{row.ticker} — watch entry near ₹{row.entry:,.0f}"
        if line not in bullets:
            bullets.append(line)
    if not bullets and pins:
        p = pins[0]
        sym = p.symbol.upper().replace(".NS", "")
        bullets.append(f"{sym} — plan entry ₹{p.entry:,.0f}, stop ₹{p.stop_loss:,.0f}")
    if not bullets:
        bullets.append("No urgent items — stick to your trade plan.")
    return bullets[:3]


def _broker_snapshot() -> BrokerSnapshot:
    raw = st.session_state.get("broker_snapshot")
    if raw:
        return BrokerSnapshot.from_dict(raw)
    return load_broker_snapshot()


def _go_symbol(symbol: str) -> None:
    sym = symbol.replace(".NS", "").replace(".BO", "").strip()
    request_nav_tab(
        "Single Stock",
        single_ticker=sym,
        bt_ticker=sym,
        intraday_ticker=sym,
        alpha_ai_ticker=sym,
    )


def _render_todays_decision(
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    snapshot: ContextSnapshot,
    pins: list[PinnedPlan],
) -> None:
    st.markdown('<div class="assist-card assist-hero">', unsafe_allow_html=True)
    st.markdown('<p class="assist-q">What should I do today?</p>', unsafe_allow_html=True)

    if decision:
        verdict = decision.verdict.value
        cls = _VERDICT_CLASS.get(decision.verdict, "dash-verdict-wait")
        reason = decision.reason
        if decision.explainability and decision.explainability.why:
            reason = decision.explainability.why
        conf_num = _conf_numeric(decision, snapshot)
    else:
        verdict = "WAIT" if snapshot.risk_mode != "CLOSED" else "DEFENSIVE"
        cls = "dash-verdict-defensive" if verdict == "DEFENSIVE" else "dash-verdict-wait"
        reason = os_report.next_step or mis.summary or "Wait for a clearer setup."
        conf_num = _conf_numeric(None, snapshot)

    conf_text, conf_cls = _conf_label(conf_num)
    conclusion = _verdict_conclusion(verdict, os_report=os_report, mis=mis)

    st.markdown(
        f'<div class="dash-verdict {cls}">'
        f'<p class="assist-verdict-xl">{_esc(verdict)}</p>'
        f'<p class="assist-conf {conf_cls}">{_esc(conf_text)}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<p class="assist-reason">{_esc(reason)}</p>', unsafe_allow_html=True)

    levels_sym = os_report.starred_symbol or (pins[0].symbol if pins else "")
    levels = _levels_for_symbol(levels_sym, pins) if levels_sym else None
    if levels:
        entry, stop, target = levels
        st.markdown(
            '<div class="assist-levels">'
            f'{_level_box("Entry", f"₹{entry:,.0f}")}'
            f'{_level_box("Stop", f"₹{stop:,.0f}")}'
            f'{_level_box("Target", f"₹{target:,.0f}")}'
            f'{_level_box("Symbol", levels_sym.upper().replace(".NS", ""))}'
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f'<p class="assist-conclusion">{_esc(conclusion)}</p>', unsafe_allow_html=True)

    if st.button("Open today's trade plan", key="assist_trade_plan", type="primary", use_container_width=True):
        request_nav_tab("Suggestions")

    with st.expander("Why this call?"):
        st.caption(f"Confidence score: {conf_num}%")
        evidence = _evidence_summary(decision)
        if not evidence and mis.synthesis_pillars:
            evidence = mis.synthesis_pillars[:5]
        if not evidence and mis.flags:
            evidence = [f"⚠ {f}" for f in mis.flags[:4]]
        if evidence:
            for line in evidence[:6]:
                st.markdown(f"- {line}")
        else:
            st.caption("More detail appears after live synthesis runs.")

    st.markdown("</div>", unsafe_allow_html=True)


def _level_box(label: str, value: str) -> str:
    return (
        f'<div class="assist-level-box">'
        f'<p class="assist-level-label">{_esc(label)}</p>'
        f'<p class="assist-level-value">{_esc(value)}</p>'
        f"</div>"
    )


def _render_best_opportunity(
    opportunities: list[OpportunityRow],
    os_report: InvestmentOS,
) -> None:
    st.markdown('<div class="assist-card">', unsafe_allow_html=True)
    st.markdown('<p class="assist-q">Which opportunity deserves my attention?</p>', unsafe_allow_html=True)

    row = _best_opportunity(opportunities, os_report)
    if not row:
        st.markdown(
            '<p class="assist-reason">No saved setups yet. Run a scan after market close to build your list.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="assist-conclusion">Head to Suggestions to scan and save picks for tomorrow.</p>',
            unsafe_allow_html=True,
        )
        if st.button("Go to suggestions", key="assist_go_suggestions", use_container_width=True):
            request_nav_tab("Suggestions")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    conf_text, conf_cls = _conf_label(row.confidence)
    rr = _risk_reward(row.entry, row.stop, row.target)
    rr_note = f"{rr}× reward vs risk" if rr else "check risk before sizing"
    st.markdown(
        f'<p class="assist-reason"><b>{_esc(row.ticker)}</b> — {_esc(row.side)} setup. '
        f'<span class="assist-conf {conf_cls}">{_esc(conf_text)}</span> · {_esc(rr_note)}.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="assist-reason">Entry ₹{row.entry:,.0f} · Stop ₹{row.stop:,.0f} · Target ₹{row.target:,.0f}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="assist-conclusion">Review the full setup for {_esc(row.ticker)} before you commit capital.</p>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Review Setup", key="assist_review_setup", type="primary", use_container_width=True):
            _go_symbol(row.ticker)
    with c2:
        if st.button("See all picks", key="assist_all_picks", use_container_width=True):
            request_nav_tab("Suggestions")

    with st.expander("Setup details"):
        st.caption(f"Confidence score: {row.confidence}%")
        st.markdown(f"- Expected move: {row.expected_reward}")
        st.markdown(f"- Risk: {row.risk}")

    st.markdown("</div>", unsafe_allow_html=True)


def _render_portfolio_assistant(
    metrics: dict[str, Any],
    portfolio: ZerodhaImportResult | None,
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
) -> None:
    st.markdown('<div class="assist-card">', unsafe_allow_html=True)
    st.markdown('<p class="assist-q">What should I do with my portfolio?</p>', unsafe_allow_html=True)

    health, health_cls, health_detail = _portfolio_health(snapshot, mis, os_report)
    holdings = portfolio.holdings if portfolio and portfolio.holdings else []
    weakest, strongest = _holding_extremes(holdings)

    pnl_label = "Today's P/L" if metrics["today_pnl_source"] == "journal" else "Unrealized P/L"
    pnl_val = _fmt_inr(metrics["today_pnl"], signed=True)
    exp = f"{metrics['exposure_pct']}%" if metrics["exposure_pct"] is not None else "not set"

    st.markdown(
        f'<p class="assist-reason">Portfolio is <span class="assist-conf {health_cls}">{_esc(health)}</span>. '
        f'{_esc(health_detail)}</p>',
        unsafe_allow_html=True,
    )

    if metrics["holding_count"]:
        st.markdown(
            f'<p class="assist-reason">{_esc(pnl_label)}: <b>{_esc(pnl_val)}</b> · '
            f'Exposure { _esc(exp)} · Weakest: {_esc(weakest)} · Strongest: {_esc(strongest)}</p>',
            unsafe_allow_html=True,
        )
        conclusion = (
            f"You hold {metrics['holding_count']} position(s). "
            "Review sizing on laggards before adding new trades."
        )
    else:
        st.markdown(
            '<p class="assist-reason">No holdings saved yet — connect your broker or import a CSV.</p>',
            unsafe_allow_html=True,
        )
        conclusion = "Connect Zerodha or import holdings so portfolio advice stays accurate."

    st.markdown(f'<p class="assist-conclusion">{_esc(conclusion)}</p>', unsafe_allow_html=True)

    if st.button("See full portfolio", key="assist_portfolio", use_container_width=True):
        request_nav_tab("My Portfolio")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_watch_today(
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    opportunities: list[OpportunityRow],
    pins: list[PinnedPlan],
) -> None:
    st.markdown('<div class="assist-card">', unsafe_allow_html=True)
    st.markdown('<p class="assist-q">What do I need to watch today?</p>', unsafe_allow_html=True)

    bullets = _watch_bullets(mis, snapshot, opportunities, pins)
    items = "".join(f"<li>{_esc(b)}</li>" for b in bullets)
    st.markdown(f'<ul class="dash-evidence-list">{items}</ul>', unsafe_allow_html=True)
    st.markdown(
        '<p class="assist-conclusion">Keep these on your radar — act only when your plan says go.</p>',
        unsafe_allow_html=True,
    )

    if st.button("View all picks", key="assist_watch_picks", use_container_width=True):
        request_nav_tab("Suggestions")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_broker_status() -> None:
    snap = _broker_snapshot()
    st.markdown('<div class="assist-card">', unsafe_allow_html=True)
    st.markdown('<p class="assist-q">Is my broker connected?</p>', unsafe_allow_html=True)

    if snap.connected():
        card_cls = "assist-broker-ok"
        status = f"Yes — {snap.broker_label} is connected"
        if snap.user_id:
            status += f" ({snap.user_id})"
        detail = snap.last_sync_at or "Recently synced"
        if snap.holdings_count:
            detail += f" · {snap.holdings_count} holding(s)"
        conclusion = "Your live holdings feed is active. Zerodha Console remains the P&L source of truth."
        action_label = "Open My Portfolio"
        action_tab = "My Portfolio"
    elif snap.needs_sign_in():
        card_cls = "assist-broker-off"
        status = "Not connected — sign in to sync holdings"
        detail = snap.error_message or "Connect Zerodha to pull live positions."
        conclusion = "Connect now so portfolio and risk advice use your real book."
        action_label = "Connect Zerodha"
        action_tab = "My Portfolio"
    else:
        card_cls = "assist-broker-warn"
        status = f"{snap.broker_label} — {snap.state.replace('_', ' ')}"
        detail = snap.error_message or snap.last_sync_status or "Limited sync — check connection."
        conclusion = "Refresh your broker session to keep advice aligned with your account."
        action_label = "Fix broker connection"
        action_tab = "My Portfolio"

    st.markdown(
        f'<div class="{card_cls}" style="padding-left:12px">'
        f'<p class="assist-reason"><b>{_esc(status)}</b></p>'
        f'<p class="assist-reason" style="opacity:0.8;font-size:0.95rem">{_esc(detail)}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<p class="assist-conclusion">{_esc(conclusion)}</p>', unsafe_allow_html=True)

    if st.button(action_label, key="assist_broker_action", use_container_width=True):
        request_nav_tab(action_tab)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_home_stock_search(*, market: str) -> None:
    st.markdown('<div class="assist-search-wrap">', unsafe_allow_html=True)
    query = st.text_input(
        "Search any stock",
        placeholder="Search any stock…",
        key="home_stock_search",
        label_visibility="collapsed",
    )
    if not query or len(query.strip()) < 2:
        st.caption("Type a symbol or company name to jump straight to analysis.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    q = query.strip()
    if is_india_market(market):
        hits = unified_search(q, max_results=5)
        if not hits:
            st.caption("No matches — try the NSE symbol or company name.")
        else:
            for i, h in enumerate(hits):
                label = f"{h.symbol} — {h.name[:40]}"
                if st.button(label, key=f"home_search_{i}_{h.symbol}", use_container_width=True):
                    _go_symbol(h.symbol)
    else:
        sym = q.upper()
        if st.button(f"Analyze {sym}", key="home_search_us", use_container_width=True):
            _go_symbol(sym)
    st.markdown("</div>", unsafe_allow_html=True)


def render_home_dashboard(market: str, *, period: str = "1y", max_trades: int = 1) -> None:
    del max_trades  # selection lives on Suggestions — home stays action-first
    st.markdown(HOME_UI_CSS, unsafe_allow_html=True)
    st.markdown('<div class="home-wrap dash-wrap assist-wrap">', unsafe_allow_html=True)

    with st.spinner("Getting your briefing…"):
        cached = load_dashboard_data(market, period, deep=False)

    snapshot: ContextSnapshot = _snapshot_from_cache(cached["snapshot"])
    mis: MisTradeAdvisory = cached["mis"]
    os_report: InvestmentOS = cached["os_report"]
    pins: list[PinnedPlan] = cached["pins"]
    prefs: IntradayPrefs = cached["prefs"]
    portfolio: ZerodhaImportResult | None = cached["portfolio"]
    data = {**cached, "snapshot": snapshot}

    decision, _source = _pick_decision(mis, os_report)
    opportunities = _build_opportunities(pins, data["pulse"])
    port_metrics = _portfolio_metrics(portfolio, prefs, journal_today_pnl=data["journal_today_pnl"])

    _render_todays_decision(decision, mis, os_report, snapshot, pins)
    _render_best_opportunity(opportunities, os_report)
    _render_portfolio_assistant(port_metrics, portfolio, snapshot, mis, os_report)
    _render_watch_today(mis, snapshot, opportunities, pins)
    _render_broker_status()
    _render_home_stock_search(market=market)

    st.caption(f"Updated {data['built_at']} · Zerodha Console is source of truth for P&L.")
    st.markdown("</div>", unsafe_allow_html=True)


def _snapshot_to_cache(snapshot: ContextSnapshot) -> dict[str, Any]:
    """Plain dict for st.cache_data — MappingProxyType is not pickle-serializable."""
    return snapshot.as_dict()


def _snapshot_from_cache(data: dict[str, Any]) -> ContextSnapshot:
    """Rebuild ContextSnapshot with plain dicts (no mappingproxy) for UI use."""
    return ContextSnapshot(
        timestamp=str(data["timestamp"]),
        market_regime=str(data["market_regime"]),
        market_phase=str(data["market_phase"]),
        market_breadth=str(data["market_breadth"]),
        volatility_state=str(data["volatility_state"]),
        liquidity_state=str(data["liquidity_state"]),
        market_session=dict(data.get("market_session") or {}),
        sector_strength=dict(data.get("sector_strength") or {}),
        industry_strength=dict(data.get("industry_strength") or {}),
        macro_state=dict(data.get("macro_state") or {}),
        global_market_state=dict(data.get("global_market_state") or {}),
        risk_mode=str(data["risk_mode"]),
        trading_restrictions=tuple(data.get("trading_restrictions") or ()),
        confidence=float(data.get("confidence") or 0.0),
        schema_version=str(data.get("schema_version") or "1.0"),
        snapshot_id=str(data.get("snapshot_id") or ""),
        context_hash=str(data.get("context_hash") or ""),
        metadata=dict(data.get("metadata") or {}),
    )


@st.cache_data(ttl=45, show_spinner=False)
def load_dashboard_data(market: str, period: str, deep: bool) -> dict[str, Any]:
    from analyzer.context_engine import build_context_snapshot

    prefs = load_intraday_prefs()
    snapshot = build_context_snapshot(market=market, use_cache=True)
    mis = build_mis_trade_advisory(market=market)
    os_report = build_investment_os(market, period=period, prefs=prefs, deep=deep)
    pins = load_pinned_plans()
    pulse = _load_pulse(market, period)
    prof = portfolio_profile_key()
    portfolio = load_saved_portfolio(profile=prof)
    session_date = str(dict(snapshot.market_session).get("date", ""))
    journal_today = _journal_pnl_for_date(session_date) if session_date else None
    learning = resolve_learning_outcomes(days=14)
    return {
        "snapshot": _snapshot_to_cache(snapshot),
        "mis": mis,
        "os_report": os_report,
        "pins": pins,
        "pulse": pulse,
        "portfolio": portfolio,
        "prefs": prefs,
        "journal_today_pnl": journal_today,
        "learning": learning,
        "built_at": datetime.now(IST).strftime("%H:%M IST"),
    }
