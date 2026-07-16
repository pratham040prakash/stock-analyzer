"""Phase 2 — Trades tab · Plan Canvas (execution companion, presentation only)."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any

import streamlit as st

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.home_dashboard import (
    VerdictCanvasState,
    _broker_snapshot,
    _esc,
    _pick_decision,
    _resolve_verdict_state,
    _strip_md,
    _sync_status,
    _trim_words,
)
from ui.components.partner_shell import set_partner_dock

_MENTOR_OPEN_MAX_WORDS = 22
_REASON_MAX_WORDS = 20


@dataclass(frozen=True)
class TradePlanView:
    has_plan: bool
    symbol: str
    side: str
    mentor_opening: str
    reason: str
    entry_line: str
    stop_line: str
    max_loss_line: str
    target_line: str
    lifecycle_line: str
    kite_url: str


def _fmt_inr(value: float) -> str:
    return f"₹{value:,.0f}"


def _pick_plan_pin(
    os_report: InvestmentOS,
    pins: list[PinnedPlan],
) -> PinnedPlan | None:
    if not pins:
        return None
    star = (os_report.starred_symbol or "").upper().replace(".NS", "").replace(".BO", "")
    if star:
        for pin in pins:
            sym = pin.symbol.upper().replace(".NS", "").replace(".BO", "")
            if sym == star:
                return pin
    return pins[0]


def _trigger_line(pin: PinnedPlan) -> str:
    side = (pin.side or "LONG").upper()
    entry = _fmt_inr(pin.entry)
    if side == "SHORT":
        return f"Sell below {entry}"
    return f"Buy above {entry}"


def _max_loss_inr(pin: PinnedPlan, prefs: IntradayPrefs) -> float:
    capital = float(prefs.capital or 0)
    if capital > 0 and prefs.max_risk_pct:
        return round(capital * float(prefs.max_risk_pct) / 100.0)
    risk_per_share = abs(pin.entry - pin.stop_loss)
    if risk_per_share > 0:
        return round(risk_per_share * 1)
    return 0.0


def _plan_reason(
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
) -> str:
    if decision:
        if decision.explainability and decision.explainability.why:
            return _trim_words(decision.explainability.why, max_words=_REASON_MAX_WORDS)
        if decision.reason:
            return _trim_words(decision.reason, max_words=_REASON_MAX_WORDS)
    if mis.flags:
        return _trim_words(mis.flags[0], max_words=_REASON_MAX_WORDS)
    if mis.summary:
        return _trim_words(mis.summary, max_words=_REASON_MAX_WORDS)
    return "Momentum and structure line up — protect the stop if you take it."


def _plan_mentor_opening(
    pin: PinnedPlan,
    *,
    reason: str,
    decision: DecisionArtifact | None,
) -> str:
    sym = pin.symbol.upper().replace(".NS", "").replace(".BO", "")
    side = (pin.side or "LONG").upper()
    verb = "buy" if side == "LONG" else "sell"
    base = (
        f"I'd {verb} {sym} only above {_fmt_inr(pin.entry)} "
        f"with a hard stop at {_fmt_inr(pin.stop_loss)}."
    )
    if decision and decision.reason and decision.reason not in reason:
        return _trim_words(base, max_words=_MENTOR_OPEN_MAX_WORDS)
    return _trim_words(base, max_words=_MENTOR_OPEN_MAX_WORDS)


def _lifecycle_line(snapshot: ContextSnapshot) -> str:
    phase = str(dict(snapshot.market_session or {}).get("phase", "") or snapshot.market_phase or "")
    restrictions = snapshot.trading_restrictions or ()

    for raw in restrictions:
        text = _strip_md(raw).lower()
        if "9:45" in text or "9.45" in text or "opening" in text:
            return "Earliest entry after 9:45."
        if "noon" in text or "12" in text:
            return "Review if not triggered by noon."

    if phase in ("pre_market", "opening", "regular", "live"):
        return "This plan expires at market close."

    if phase in ("after_hours", "closed"):
        return "This plan expires at market close."

    return "This plan expires at market close."


def _kite_market_url(symbol: str) -> str:
    sym = symbol.upper().replace(".NS", "").replace(".BO", "")
    return f"https://kite.zerodha.com/markets/equity/NSE/{sym}"


def build_trade_plan_view(
    *,
    state: VerdictCanvasState,
    pin: PinnedPlan | None,
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    prefs: IntradayPrefs,
) -> TradePlanView | None:
    if state.key != "trade" or pin is None:
        return None

    reason = _plan_reason(decision, mis)
    sym = pin.symbol.upper().replace(".NS", "").replace(".BO", "")
    max_loss = _max_loss_inr(pin, prefs)
    max_loss_text = _fmt_inr(max_loss) if max_loss > 0 else "—"

    return TradePlanView(
        has_plan=True,
        symbol=sym,
        side=(pin.side or "LONG").upper(),
        mentor_opening=_plan_mentor_opening(pin, reason=reason, decision=decision),
        reason=reason,
        entry_line=_trigger_line(pin),
        stop_line=f"Stop {_fmt_inr(pin.stop_loss)}",
        max_loss_line=f"Maximum loss {max_loss_text}",
        target_line=f"Target {_fmt_inr(pin.target)}",
        lifecycle_line=_lifecycle_line(snapshot),
        kite_url=_kite_market_url(sym),
    )


def _render_active_plan(plan: TradePlanView, *, built_at: str, broker: BrokerSnapshot) -> None:
    sync_cls, dot_cls, sync_label = _sync_status(broker)
    side_cls = "pc-side-long" if plan.side == "LONG" else "pc-side-short"
    st.markdown(
        f'<div class="verdict-canvas-root plan-canvas-root" data-plan="active">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f'<div class="pc-hero-zone pc-hero-trade">'
        f'<p class="pc-context">Trade</p>'
        f'<p class="pc-symbol">{_esc(plan.symbol)}</p>'
        f'<p class="pc-side {side_cls}">{_esc(plan.side.title())}</p>'
        f"</div>"
        f'<p class="vc-mentor pc-mentor-open">{_esc(plan.mentor_opening)}</p>'
        f'<p class="pc-reason">{_esc(plan.reason)}</p>'
        f'<p class="pc-line pc-line-protect">{_esc(plan.entry_line)}</p>'
        f'<p class="pc-line pc-line-protect">{_esc(plan.stop_line)}</p>'
        f'<p class="pc-line pc-line-loss">{_esc(plan.max_loss_line)}</p>'
        f'<p class="pc-line pc-line-target">{_esc(plan.target_line)}</p>'
        f'<p class="pc-lifecycle">{_esc(plan.lifecycle_line)}</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="vc-primary">', unsafe_allow_html=True)
    st.link_button("Open in Kite", plan.kite_url, type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-secondary">', unsafe_allow_html=True)
    if st.button("Not today", key="pc_not_today", use_container_width=True):
        st.toast("Sitting out is a valid decision.")
        set_partner_dock("today")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-ghost-row">', unsafe_allow_html=True)
    if st.button("See the structure", key="pc_proof", use_container_width=True):
        from ui.components.proof_canvas import open_proof_overlay

        open_proof_overlay(origin="trades", proof_mode="trade", symbol=plan.symbol)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<p class="vc-foot">Zerodha Console is source of truth for P&amp;L.</p></div>',
        unsafe_allow_html=True,
    )


def _render_empty_plan(*, built_at: str, broker: BrokerSnapshot) -> None:
    sync_cls, dot_cls, sync_label = _sync_status(broker)
    st.markdown(
        f'<div class="verdict-canvas-root plan-canvas-root" data-plan="empty">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f'<div class="pc-hero-zone">'
        f'<p class="pc-symbol pc-symbol-muted">No plan today</p>'
        f"</div>"
        f"<p class=\"vc-mentor\">Sitting out is the trade. Your capital is protected when you don't force one.</p>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="vc-primary">', unsafe_allow_html=True)
    if st.button("Back to Today", key="pc_back_today", type="primary", use_container_width=True):
        set_partner_dock("today")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<p class="vc-foot">Zerodha Console is source of truth for P&amp;L.</p></div>', unsafe_allow_html=True)


def _render_connect_plan(*, built_at: str, broker: BrokerSnapshot) -> None:
    sync_cls, dot_cls, sync_label = _sync_status(broker)
    st.markdown(
        f'<div class="verdict-canvas-root plan-canvas-root" data-plan="connect">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f'<div class="pc-hero-zone">'
        f'<p class="pc-symbol pc-symbol-muted">Link Zerodha first</p>'
        f"</div>"
        f"<p class=\"vc-mentor\">I'll size risk against your real book once holdings sync.</p>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="vc-primary">', unsafe_allow_html=True)
    if st.button("Connect Zerodha", key="pc_connect", type="primary", use_container_width=True):
        from ui.navigation import request_nav_tab

        request_nav_tab("My Portfolio")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="vc-secondary">', unsafe_allow_html=True)
    if st.button("Back to Today", key="pc_connect_back", use_container_width=True):
        set_partner_dock("today")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<p class="vc-foot">Zerodha Console is source of truth for P&amp;L.</p></div>', unsafe_allow_html=True)


def render_plan_canvas(
    *,
    market: str,
    cached: dict[str, Any],
) -> None:
    del market
    from ui.components.home_dashboard import _snapshot_from_cache

    snapshot_obj = _snapshot_from_cache(cached["snapshot"])

    mis: MisTradeAdvisory = cached["mis"]
    os_report: InvestmentOS = cached["os_report"]
    pins: list[PinnedPlan] = cached["pins"]
    prefs: IntradayPrefs = cached["prefs"]
    broker = _broker_snapshot()
    built_at = str(cached["built_at"])

    decision, _source = _pick_decision(mis, os_report)
    state = _resolve_verdict_state(broker, snapshot_obj, mis, decision)

    if not broker.connected():
        _render_connect_plan(built_at=built_at, broker=broker)
        return

    pin = _pick_plan_pin(os_report, pins)
    plan = build_trade_plan_view(
        state=state,
        pin=pin,
        decision=decision,
        mis=mis,
        snapshot=snapshot_obj,
        prefs=prefs,
    )

    if plan and plan.has_plan:
        _render_active_plan(plan, built_at=built_at, broker=broker)
    else:
        _render_empty_plan(built_at=built_at, broker=broker)
