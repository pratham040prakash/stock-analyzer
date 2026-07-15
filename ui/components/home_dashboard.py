"""Investment OS Home Dashboard — answers market, decision, opportunities, risk in one screen."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from analyzer.broker_truth.learning import (
    LearningOutcomeRow,
    LearningOutcomeSource,
    learning_source_stats,
    resolve_learning_outcomes,
)
from analyzer.context_engine import build_context_snapshot
from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict
from analyzer.intraday_prefs import IntradayPrefs, load_intraday_prefs, save_intraday_prefs
from analyzer.investment_os import InvestmentOS, build_investment_os
from analyzer.market_pulse_scan import MarketPulseReport
from analyzer.mis_trade_advisory import MisTradeAdvisory, build_mis_trade_advisory
from analyzer.nightly_prep import run_nightly_prep
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from analyzer.pulse_cache import load_pulse_cache_with_stale
from analyzer.trade_journal import load_journal_entries
from analyzer.trade_selection import is_selected, toggle_selected
from analyzer.watchlist_history import outcome_label
from analyzer.watchlist_pins import PinnedPlan, load_pinned_plans
from analyzer.zerodha import ZerodhaImportResult
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


def _macro_headline(snapshot: ContextSnapshot) -> str:
    macro = dict(snapshot.macro_state)
    parts: list[str] = []
    vix = macro.get("vix_regime") or snapshot.volatility_state
    if vix:
        parts.append(f"VIX {vix}")
    fii = macro.get("fii_dii_summary")
    if fii:
        parts.append(str(fii)[:60])
    leader = dict(snapshot.sector_strength).get("leader")
    if leader:
        parts.append(f"Leader: {leader}")
    return " · ".join(parts) if parts else "Macro context loaded"


def _global_bias(snapshot: ContextSnapshot) -> str:
    state = dict(snapshot.global_market_state)
    bias = str(state.get("bias", "NEUTRAL"))
    action = str(state.get("india_action", "") or "")
    spill = state.get("spillover_score")
    tail = f" · spill {spill:+.0f}" if spill is not None else ""
    return f"{bias}{tail}" + (f" — {action[:50]}" if action else "")


def _session_label(snapshot: ContextSnapshot) -> str:
    session = dict(snapshot.market_session)
    status = str(session.get("status", "unknown"))
    phase = str(session.get("phase", ""))
    date = str(session.get("date", ""))
    open_flag = "open" if session.get("is_open") else "closed"
    return f"{status} · {phase} · {date} ({open_flag})"


def _market_decision_hint(os_report: InvestmentOS, snapshot: ContextSnapshot | None) -> str:
    if os_report.verdict in ("TRADE OK", "WAIT", "NO TRADE", "PREP", "CLOSED"):
        return os_report.verdict
    if snapshot:
        if snapshot.risk_mode == "CLOSED":
            return "CLOSED"
        if snapshot.trading_restrictions:
            return snapshot.trading_restrictions[0][:80]
        return snapshot.risk_mode
    return "—"


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


def _yesterday_learning_row(rows: list[LearningOutcomeRow]) -> LearningOutcomeRow | None:
    today = datetime.now(IST).date()
    for offset in range(1, 8):
        day = (today - timedelta(days=offset)).isoformat()
        for row in rows:
            if row.trade_date == day:
                return row
    return rows[0] if rows else None


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


def _section_title(title: str, subtitle: str = "") -> None:
    sub = f'<span class="dash-section-sub">{_esc(subtitle)}</span>' if subtitle else ""
    st.markdown(
        f'<div class="dash-section-head"><h3 class="dash-section-title">{_esc(title)}</h3>{sub}</div>',
        unsafe_allow_html=True,
    )


def _metric_tile(label: str, value: str, *, hint: str = "") -> str:
    hint_html = f'<p class="dash-tile-hint">{_esc(hint)}</p>' if hint else ""
    return (
        f'<div class="dash-tile">'
        f'<p class="dash-tile-label">{_esc(label)}</p>'
        f'<p class="dash-tile-value">{_esc(value)}</p>'
        f"{hint_html}"
        f"</div>"
    )


def _render_market_section(snapshot: ContextSnapshot, os_report: InvestmentOS) -> None:
    _section_title("Today's Market", "What is happening?")
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    row1 = "".join(
        [
            _metric_tile("Market Regime", snapshot.market_regime),
            _metric_tile("Risk Mode", snapshot.risk_mode),
            _metric_tile("Market Breadth", snapshot.market_breadth),
            _metric_tile("Global Bias", _global_bias(snapshot).split(" — ")[0]),
        ]
    )
    row2 = "".join(
        [
            _metric_tile("Macro State", _macro_headline(snapshot)[:72]),
            _metric_tile("Session", _session_label(snapshot)),
            _metric_tile("Decision", _market_decision_hint(os_report, snapshot)),
        ]
    )
    st.markdown(f'<div class="dash-tile-grid dash-tile-grid-4">{row1}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dash-tile-grid dash-tile-grid-3">{row2}</div>', unsafe_allow_html=True)
    global_detail = _global_bias(snapshot)
    if " — " in global_detail:
        st.caption(global_detail.split(" — ", 1)[1])
    st.markdown("</div>", unsafe_allow_html=True)


def _render_decision_section(
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    snapshot: ContextSnapshot,
) -> None:
    _section_title("Today's Decision", "Should I deploy capital today?")
    st.markdown('<div class="dash-card dash-decision-card">', unsafe_allow_html=True)

    if decision:
        verdict = decision.verdict.value
        cls = _VERDICT_CLASS.get(decision.verdict, "dash-verdict-wait")
        conf = int(round(decision.confidence))
        reason = decision.reason
        if decision.explainability and decision.explainability.why:
            reason = decision.explainability.why
    else:
        verdict = "WAIT" if snapshot.risk_mode != "CLOSED" else "DEFENSIVE"
        cls = "dash-verdict-defensive" if verdict == "DEFENSIVE" else "dash-verdict-wait"
        conf = int(snapshot.confidence * 100) if snapshot.confidence else 0
        reason = os_report.next_step or mis.summary

    st.markdown(
        f'<div class="dash-verdict {cls}">'
        f'<span class="dash-verdict-label">{_esc(verdict)}</span>'
        f'<span class="dash-verdict-conf">{conf}% confidence</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<p class="dash-reason">{_esc(reason)}</p>', unsafe_allow_html=True)

    evidence = _evidence_summary(decision)
    if not evidence and mis.synthesis_pillars:
        evidence = mis.synthesis_pillars[:5]
    if not evidence and mis.flags:
        evidence = [f"⚠ {f}" for f in mis.flags[:4]]
    if evidence:
        st.markdown('<p class="dash-evidence-title">Evidence summary</p>', unsafe_allow_html=True)
        items = "".join(f"<li>{_esc(line)}</li>" for line in evidence[:6])
        st.markdown(f'<ul class="dash-evidence-list">{items}</ul>', unsafe_allow_html=True)
    else:
        st.caption("Evidence packet not persisted yet — run live synthesis for detail.")

    if os_report.next_step:
        st.markdown(f'<p class="dash-next"><b>Next:</b> {_esc(os_report.next_step)}</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_opportunities_section(
    rows: list[OpportunityRow],
    *,
    max_trades: int,
    market: str,
    period: str,
) -> None:
    _section_title("Top Opportunities", "Best setups right now")
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    if not rows:
        st.caption("No picks saved — run tonight's scan after market close.")
        if st.button("Scan tonight's stocks", type="primary", key="dash_scan", use_container_width=True):
            with st.spinner("Scanning…"):
                result, _ = run_nightly_prep(market, period=period, send_telegram=False, use_cache=False)
            if result.equity_count:
                st.success(f"Saved {result.equity_count} picks.")
            load_dashboard_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(
        [
            {
                "Ticker": r.ticker,
                "Confidence": f"{r.confidence}%",
                "Expected reward": r.expected_reward,
                "Risk": r.risk,
                "Side": r.side,
            }
            for r in rows
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    for r in rows:
        picked = is_selected(r.ticker)
        label = f"⭐ {r.ticker} selected" if picked else f"Select {r.ticker}"
        btn_type = "primary" if picked else "secondary"
        if st.button(label, key=f"dash_pick_{r.ticker}", type=btn_type, use_container_width=True):
            toggle_selected(r.ticker, max_selected=max_trades)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_portfolio_section(metrics: dict[str, Any]) -> None:
    _section_title("Portfolio", "Exposure and P/L")
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    pnl_label = "Today's P/L" if metrics["today_pnl_source"] == "journal" else "Unrealized P/L"
    with c1:
        st.metric(pnl_label, _fmt_inr(metrics["today_pnl"], signed=True))
    with c2:
        st.metric("Cash", _fmt_inr(metrics["cash"]))
    with c3:
        exp = f"{metrics['exposure_pct']}%" if metrics["exposure_pct"] is not None else "—"
        st.metric("Exposure", exp)
    with c4:
        st.metric("Risk budget", _fmt_inr(metrics["risk_budget"]))

    if metrics["allocation"]:
        st.caption("Allocation: " + " · ".join(metrics["allocation"]))
    elif metrics["holding_count"] == 0:
        st.caption("No holdings saved — connect Kite or import CSV in My Portfolio.")
    else:
        st.caption(f"{metrics['holding_count']} holding(s) tracked.")

    if st.button("Open My Portfolio", key="dash_portfolio", use_container_width=True):
        request_nav_tab("My Portfolio")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_watchlist_section(
    opportunities: list[OpportunityRow],
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    pins: list[PinnedPlan],
) -> None:
    _section_title("Watchlist", "Opportunities and risks")
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="dash-card dash-half-card">', unsafe_allow_html=True)
        st.markdown("**Best opportunities**")
        if opportunities:
            for r in opportunities[:3]:
                star = "⭐ " if is_selected(r.ticker) else ""
                st.markdown(f"- {star}**{r.ticker}** · {r.confidence}% · {r.expected_reward}")
        elif pins:
            for p in pins[:3]:
                st.markdown(f"- **{p.symbol}** · E ₹{p.entry:,.0f} → T ₹{p.target:,.0f}")
        else:
            st.caption("Run scan to populate watchlist.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="dash-card dash-half-card">', unsafe_allow_html=True)
        st.markdown("**Worst risks**")
        risks: list[str] = []
        risks.extend(snapshot.trading_restrictions[:4])
        risks.extend(mis.flags[:4])
        for p in sorted(pins, key=lambda x: _risk_reward(x.entry, x.stop_loss, x.target) or 0)[:2]:
            rr = _risk_reward(p.entry, p.stop_loss, p.target)
            if rr is not None and rr < 1.5:
                risks.append(f"{p.symbol} tight R:R ({rr}×)")
        if not risks:
            risks.append("No elevated risk flags — stay sized to plan.")
        for line in risks[:5]:
            st.markdown(f"- {line}")
        if st.button("Open Watchlist", key="dash_watchlist", use_container_width=True):
            request_nav_tab("Watchlist")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_learning_section(learning: list[LearningOutcomeRow]) -> None:
    _section_title("Learning", "Yesterday vs reality")
    st.markdown('<div class="dash-card">', unsafe_allow_html=True)
    row = _yesterday_learning_row(learning)
    stats = learning_source_stats(days=14)
    if row:
        source = "Broker" if row.source == LearningOutcomeSource.BROKER else "Coach fallback"
        pnl_note = ""
        if row.realized_pnl is not None:
            pnl_note = f" · P&L {_fmt_inr(row.realized_pnl, signed=True)}"
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Yesterday** ({row.trade_date})")
            st.markdown(f"- **Decision context:** prep score {row.prep_score:.0f}")
            st.markdown(f"- **Reality:** {outcome_label(row.outcome)}")
        with c2:
            st.markdown("**Broker result**")
            st.markdown(f"- Source: {source}{pnl_note}")
            st.markdown(
                f"- **Calibration:** {stats['broker_pct']:.0f}% broker-backed "
                f"({stats['broker']}/{stats['total']} outcomes)"
            )
    else:
        st.caption("No scored outcomes yet — log trades and sync broker truth.")
    if st.button("Track Record & calibration", key="dash_learning", use_container_width=True):
        request_nav_tab("Track Record")
    st.markdown("</div>", unsafe_allow_html=True)


def render_home_dashboard(market: str, *, period: str = "1y", max_trades: int = 1) -> None:
    deep = st.session_state.get("os_deep_analysis", False)
    st.markdown(HOME_UI_CSS, unsafe_allow_html=True)
    st.markdown('<div class="home-wrap dash-wrap">', unsafe_allow_html=True)

    st.markdown(
        '<p class="dash-brand">Investment Operating System</p>'
        '<p class="dash-tagline">Market · Decision · Opportunities · Risk — one screen</p>',
        unsafe_allow_html=True,
    )

    with st.spinner("Loading dashboard…"):
        cached = load_dashboard_data(market, period, deep)

    snapshot: ContextSnapshot = _snapshot_from_cache(cached["snapshot"])
    mis: MisTradeAdvisory = cached["mis"]
    os_report: InvestmentOS = cached["os_report"]
    pins: list[PinnedPlan] = cached["pins"]
    prefs: IntradayPrefs = cached["prefs"]
    portfolio: ZerodhaImportResult | None = cached["portfolio"]
    learning: list[LearningOutcomeRow] = cached["learning"]
    data = {**cached, "snapshot": snapshot}

    decision, _source = _pick_decision(mis, os_report)
    opportunities = _build_opportunities(pins, data["pulse"])
    port_metrics = _portfolio_metrics(portfolio, prefs, journal_today_pnl=data["journal_today_pnl"])

    _render_market_section(snapshot, os_report)
    _render_decision_section(decision, mis, os_report, snapshot)

    col_left, col_right = st.columns(2)
    with col_left:
        _render_opportunities_section(
            opportunities,
            max_trades=max_trades,
            market=market,
            period=period,
        )
    with col_right:
        _render_portfolio_section(port_metrics)

    _render_watchlist_section(opportunities, mis, snapshot, pins)
    _render_learning_section(learning)

    st.markdown('<p class="dash-section-title" style="margin-top:24px">Quick actions</p>', unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        if st.button("Intraday", key="dash_go_intraday", use_container_width=True):
            request_nav_tab("Intraday")
    with a2:
        if st.button("Market Pulse", key="dash_go_pulse", use_container_width=True):
            request_nav_tab("Market Pulse")
    with a3:
        if st.button("Log P&L", key="dash_go_log", type="primary", use_container_width=True):
            request_nav_tab("Track Record")
    with a4:
        deep_label = "Live synthesis on" if deep else "Live synthesis"
        if st.button(deep_label, key="dash_deep", use_container_width=True):
            st.session_state["os_deep_analysis"] = not deep
            load_dashboard_data.clear()
            st.rerun()

    st.markdown('<p class="dash-section-title" style="margin-top:18px">Capital settings</p>', unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        cap = st.number_input("Capital (₹)", value=int(prefs.capital), step=500, key="dash_cap")
    with s2:
        pct = st.slider("Daily goal %", 1.0, 5.0, float(prefs.min_daily_profit_pct), 0.5, key="dash_pct")
    with s3:
        risk = st.slider("Max risk %", 0.5, 3.0, float(prefs.max_risk_pct), 0.25, key="dash_risk")
    with s4:
        st.write("")
        st.write("")
        if st.button("Save settings", key="dash_save", use_container_width=True):
            prefs.capital = float(cap)
            prefs.min_daily_profit_pct = float(pct)
            prefs.target_daily_profit_pct = pct * 2
            prefs.stretch_daily_profit_pct = pct * 3
            prefs.max_risk_pct = float(risk)
            save_intraday_prefs(prefs)
            load_dashboard_data.clear()
            st.rerun()

    snap_ref = f"{snapshot.snapshot_id[:8]}…" if snapshot.snapshot_id else "—"
    st.caption(
        f"Updated {data['built_at']} · snapshot {snap_ref} · "
        "Zerodha Console is source of truth for P&L."
    )
    st.markdown("</div>", unsafe_allow_html=True)
