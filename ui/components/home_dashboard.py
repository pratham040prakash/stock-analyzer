"""AI Trading Partner — Today (Phase 1) + dock shell; Trades via plan_canvas."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief import domain_from_cache_bundle, pick_decision as _pick_decision, view_model_from_domain
from analyzer.use_cases.snapshot_cache import snapshot_from_cache, snapshot_to_cache
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot, load_broker_snapshot
from ui.components.dashboard_pipeline import decision_reason
from ui.components.decision_card import canvas_state_from_view_model, project_decision_card
from ui.components.partner_data import load_dashboard_data
from ui.components.partner_shell import get_partner_dock, render_ask_fab, render_partner_dock, set_partner_dock
from ui.theme import VERDICT_CANVAS_CSS, PARTNER_PAGE_ACTIVATE_JS

IST = ZoneInfo("Asia/Kolkata")
_MENTOR_MAX_WORDS = 18


@dataclass(frozen=True)
class VerdictCanvasState:
    key: str
    word: str
    cta_label: str
    cta_action: str  # done | plan | week | connect


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _strip_md(text: str) -> str:
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", str(text or ""))
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    return cleaned.strip()


def _trim_words(text: str, *, max_words: int = _MENTOR_MAX_WORDS) -> str:
    words = _strip_md(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    clipped = " ".join(words[:max_words]).rstrip(".,;:")
    return f"{clipped}…"


def _conf_numeric(decision: DecisionArtifact | None, snapshot: ContextSnapshot) -> int:
    if decision:
        raw = float(decision.confidence)
        return int(round(raw * 100)) if raw <= 1.0 else int(round(raw))
    raw = float(snapshot.confidence or 0.0)
    return int(round(raw * 100)) if raw <= 1.0 else int(round(raw))


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


def _broker_snapshot() -> BrokerSnapshot:
    raw = st.session_state.get("broker_snapshot")
    if raw:
        return BrokerSnapshot.from_dict(raw)
    return load_broker_snapshot()


def _sync_status(broker: BrokerSnapshot) -> tuple[str, str, str]:
    """Return (css_class, dot_class, label)."""
    if broker.connected():
        if broker.state == "limited":
            return "vc-sync-warn", "vc-sync-warn", "Stale"
        return "vc-sync-ok", "vc-sync-ok", "Synced"
    return "vc-sync-off", "vc-sync-off", "Offline"


def _session_phase(snapshot: ContextSnapshot) -> str:
    session = dict(snapshot.market_session or {})
    return str(session.get("phase", "") or snapshot.market_phase or "")


def _market_is_rest(snapshot: ContextSnapshot) -> bool:
    phase = _session_phase(snapshot)
    if snapshot.risk_mode == "CLOSED":
        return True
    return phase in ("weekend", "holiday", "after_hours", "closed")


def _resolve_verdict_state(
    broker: BrokerSnapshot,
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    decision: DecisionArtifact | None,
) -> VerdictCanvasState:
    if not broker.connected():
        return VerdictCanvasState("connect", "Connect", "Connect Zerodha", "connect")

    if _market_is_rest(snapshot):
        return VerdictCanvasState("rest", "Rest", "View your week", "week")

    if mis.loss_streak_days >= 2:
        return VerdictCanvasState("pause", "Pause", "You're done for today", "done")

    if decision and decision.verdict in (DecisionVerdict.PASS, DecisionVerdict.DEFENSIVE):
        return VerdictCanvasState("pause", "Pause", "You're done for today", "done")

    if snapshot.risk_mode in ("RISK-OFF", "CLOSED") and len(snapshot.trading_restrictions) >= 2:
        return VerdictCanvasState("pause", "Pause", "You're done for today", "done")

    if decision and decision.verdict == DecisionVerdict.ACT:
        if _conf_numeric(decision, snapshot) >= 40:
            return VerdictCanvasState("trade", "Trade", "See the plan", "plan")

    if decision and decision.verdict == DecisionVerdict.REDUCE:
        return VerdictCanvasState("wait", "Wait", "You're done for today", "done")

    return VerdictCanvasState("wait", "Wait", "You're done for today", "done")


def _mentor_one_liner(
    state: VerdictCanvasState,
    *,
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    snapshot: ContextSnapshot,
    pins: list[PinnedPlan],
) -> str:
    if state.key == "connect":
        return "Link Zerodha once — I'll sync positions and tailor today's call."

    if state.key == "rest":
        return "Markets are closed. Rest up; tomorrow's plan builds at open."

    if state.key == "pause":
        if mis.loss_streak_days >= 2:
            return _trim_words(
                f"{mis.loss_streak_days} rough days in a row — pause today and protect your capital."
            )
        reason = decision_reason(decision)
        if reason:
            return _trim_words(reason)
        if mis.summary:
            return _trim_words(mis.summary)
        if mis.flags:
            return _trim_words(mis.flags[0])
        return "Too much risk today — pause and protect your capital."

    if state.key == "trade":
        sym = (os_report.starred_symbol or "").upper().replace(".NS", "").replace(".BO", "")
        if not sym and pins:
            sym = pins[0].symbol.upper().replace(".NS", "").replace(".BO", "")
        if sym:
            return _trim_words(f"{sym} lines up — one clear plan, sized for your rules.")
        return "One setup is ready — stay within your daily risk limit."

    if state.key == "wait":
        reason = decision_reason(decision)
        if reason:
            return _trim_words(reason)
        if mis.summary:
            return _trim_words(mis.summary)
        if pins:
            sym = pins[0].symbol.upper().replace(".NS", "").replace(".BO", "")
            return _trim_words(f"Watch {sym} — wait for price to confirm before entering.")
        if snapshot.trading_restrictions:
            return _trim_words(snapshot.trading_restrictions[0])
        if os_report.next_step:
            return _trim_words(os_report.next_step)
        return "Not your moment yet — wait until price confirms the setup."

    reason = decision_reason(decision)
    if reason:
        return _trim_words(reason)
    if mis.summary:
        return _trim_words(mis.summary)
    if snapshot.trading_restrictions:
        return _trim_words(snapshot.trading_restrictions[0])
    if os_report.next_step:
        return _trim_words(os_report.next_step)
    return "Not your moment yet — wait until price confirms the setup."


def _pick_why_decision(
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
) -> DecisionArtifact | None:
    """Decision for Why popover — equity first, then any attached artifact."""
    decision, _source = _pick_decision(mis, os_report)
    if decision:
        return decision
    mis_art = getattr(mis, "decision_artifact", None)
    if mis_art:
        return mis_art
    return getattr(os_report, "decision_artifact", None)


def _why_primary(decision: DecisionArtifact | None) -> list[str]:
    bullets: list[str] = []
    if decision:
        why = decision_reason(decision)
        if why:
            bullets.append(_strip_md(why))
        if decision.capital_recommendation:
            text = _strip_md(decision.capital_recommendation)
            if text:
                bullets.append(f"Capital: {text}")
        if decision.execution_recommendation:
            text = _strip_md(decision.execution_recommendation)
            if text:
                bullets.append(f"Execution: {text}")
        for condition in (decision.invalidation_conditions or [])[:3]:
            text = _strip_md(str(condition))
            if text:
                bullets.append(f"If wrong: {text}")
    if not bullets:
        bullets.append("Conditions are mixed — patience beats forcing a trade.")
    return bullets[:6]


def _why_advanced(
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    *,
    pins: list[PinnedPlan],
) -> list[str]:
    bullets: list[str] = []
    for line in _evidence_summary(decision, limit=4):
        text = _strip_md(line)
        if text and text not in bullets:
            bullets.append(text)
    for pillar in (getattr(mis, "synthesis_pillars", None) or [])[:5]:
        text = _strip_md(str(pillar))
        if text and text not in bullets:
            bullets.append(text)
    for flag in (mis.flags or ())[:3]:
        text = _strip_md(flag)
        if text not in bullets:
            bullets.append(text)
    for restriction in snapshot.trading_restrictions[:2]:
        text = _strip_md(restriction)
        if text not in bullets:
            bullets.append(text)
    if pins:
        pin = pins[0]
        sym = pin.symbol.upper().replace(".NS", "")
        bullets.append(f"Watch {sym} near ₹{pin.entry:,.0f} with stop ₹{pin.stop_loss:,.0f}.")
    return bullets


def _why_bullets(
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    *,
    pins: list[PinnedPlan],
) -> list[str]:
    return _why_primary(decision) + _why_advanced(decision, mis, snapshot, pins=pins)


def _handle_primary_cta(action: str) -> None:
    if action == "done":
        st.toast("Nothing to do today — you're clear.")
        return
    if action == "plan":
        set_partner_dock("trades")
        return
    if action == "week":
        set_partner_dock("you")
        return
    if action == "connect":
        from ui.navigation import request_nav_tab

        request_nav_tab("My Portfolio")


def _render_verdict_header(
    *,
    state: VerdictCanvasState,
    mentor: str,
    built_at: str,
    broker: BrokerSnapshot,
    intel_html: str = "",
    stale_label: str = "",
) -> None:
    sync_cls, dot_cls, sync_label = _sync_status(broker)
    stale_html = ""
    if stale_label:
        stale_html = f'<p class="vc-stale">{_esc(stale_label)}</p>'
    st.markdown(
        f'<div class="verdict-canvas-root" data-verdict="{_esc(state.key)}">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f"{stale_html}"
        f'<div class="vc-verdict-zone"><p class="vc-verdict-word">{_esc(state.word)}</p></div>'
        f'<p class="vc-mentor">{_esc(mentor)}</p>'
        f"{intel_html}",
        unsafe_allow_html=True,
    )


def _render_verdict_ghost_and_cta(
    *,
    state: VerdictCanvasState,
    why_primary: list[str],
    why_advanced: list[str],
    confidence_pct: int | None = None,
) -> None:
    st.markdown('<div class="vc-ghost-row">', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        with st.popover("Why I'm saying this"):
            if confidence_pct is not None:
                st.caption(f"Confidence score: {confidence_pct}%")
            for line in why_primary:
                st.markdown(f"- {line}")
            if why_advanced:
                with st.expander("Advanced diagnostics"):
                    for line in why_advanced:
                        st.markdown(f"- {line}")
            if state.key in ("wait", "trade", "pause"):
                st.caption("I'm fairly sure about this call.")
    with g2:
        from ui.components.proof_runtime import proof_canvas_active

        if proof_canvas_active() and st.button("See the proof", key="vc_proof", use_container_width=True):
            from ui.components.proof_state import open_proof_overlay

            open_proof_overlay(origin="today", proof_mode=state.key)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-primary">', unsafe_allow_html=True)
    if st.button(state.cta_label, key="vc_primary_cta", type="primary", use_container_width=True):
        _handle_primary_cta(state.cta_action)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<p class="vc-foot">Zerodha Console is source of truth for P&amp;L.</p></div>',
        unsafe_allow_html=True,
    )


def _render_verdict_canvas(
    *,
    state: VerdictCanvasState,
    mentor: str,
    why_primary: list[str],
    why_advanced: list[str],
    built_at: str,
    broker: BrokerSnapshot,
    confidence_pct: int | None = None,
) -> None:
    _render_verdict_header(
        state=state,
        mentor=mentor,
        built_at=built_at,
        broker=broker,
    )
    _render_verdict_ghost_and_cta(
        state=state,
        why_primary=why_primary,
        why_advanced=why_advanced,
        confidence_pct=confidence_pct,
    )


def _render_today_canvas(
    *,
    market: str,
    period: str,
    cached: dict[str, Any],
) -> None:
    broker = _broker_snapshot()
    domain = domain_from_cache_bundle(cached, broker=broker)
    brief = view_model_from_domain(domain, broker=broker)
    card = project_decision_card(brief)
    vkey, vword, cta_label, cta_action = canvas_state_from_view_model(card)
    state = VerdictCanvasState(vkey, vword, cta_label, cta_action)

    snapshot = domain.context
    mis = domain.mis
    os_report = domain.os_report
    pins = domain.pins
    decision = domain.decision
    why_decision = _pick_why_decision(mis, os_report)
    mentor = card.reason
    why_primary = list(brief.evidence.key_reasons) or _why_primary(why_decision)
    why_advanced = [f"{line.label}: {line.value}" for line in brief.evidence.supporting_signals]
    if brief.evidence.conflicting_signals:
        why_advanced.extend(f"Conflict: {c.label} — {c.value}" for c in brief.evidence.conflicting_signals)
    if not why_advanced:
        why_advanced = _why_advanced(why_decision, mis, snapshot, pins=pins)

    from ui.components.today_intelligence import (
        build_today_command_center,
        intel_stack_html,
        render_today_command_center,
    )

    center = build_today_command_center(
        state=state,
        snapshot=snapshot,
        mis=mis,
        os_report=os_report,
        pins=pins,
        pulse=cached.get("pulse"),
        portfolio=cached.get("portfolio"),
        prefs=cached["prefs"],
        broker=broker,
        journal_today_pnl=cached.get("journal_today_pnl"),
        decision=decision,
    )
    hero_intel = intel_stack_html(
        center,
        state,
        sections=("opportunity", "do_next", "risk"),
    )

    _render_verdict_header(
        state=state,
        mentor=mentor,
        built_at=str(cached["built_at"]),
        broker=broker,
        intel_html=hero_intel,
        stale_label=card.stale_label if card.stale else "",
    )

    _render_verdict_ghost_and_cta(
        state=state,
        why_primary=why_primary,
        why_advanced=why_advanced,
        confidence_pct=brief.decision.confidence_level,
    )

    render_today_command_center(
        state=state,
        market=market,
        cached={**cached, "snapshot": snapshot},
        broker=broker,
        decision=decision,
        sections=("market", "portfolio", "next_watch"),
        include_actions=True,
        center=center,
    )


def render_home_dashboard(market: str, *, period: str = "1y", max_trades: int = 1) -> None:
    del max_trades
    st.markdown(VERDICT_CANVAS_CSS, unsafe_allow_html=True)
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)

    cached = load_dashboard_data(market, period, deep=False)

    from ui.components.answer_canvas import is_ask_overlay_open, render_answer_overlay
    from ui.components.proof_runtime import is_proof_ui_open, proof_canvas_active

    ask_open = is_ask_overlay_open()
    proof_open = proof_canvas_active() and is_proof_ui_open()
    if ask_open or proof_open:
        st.markdown('<div class="vc-main-dimmed">', unsafe_allow_html=True)

    dock = get_partner_dock()
    if dock == "trades":
        from ui.components.plan_canvas import render_plan_canvas

        render_plan_canvas(market=market, cached=cached)
    elif dock == "you":
        from ui.components.partner_shell import is_trust_depth

        if is_trust_depth():
            from ui.components.trust_canvas import render_trust_canvas

            render_trust_canvas(market=market, cached=cached)
        else:
            from ui.components.reflection_canvas import render_reflection_canvas

            render_reflection_canvas(market=market, cached=cached)
    else:
        _render_today_canvas(market=market, period=period, cached=cached)

    if ask_open or proof_open:
        st.markdown("</div>", unsafe_allow_html=True)
    if ask_open:
        render_answer_overlay(market=market, cached=cached)
    if proof_open:
        from ui.components.proof_canvas import render_proof_overlay

        render_proof_overlay(market=market, period=period, cached=cached)

    render_partner_dock(active=dock)
    render_ask_fab()
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)


def _snapshot_to_cache(snapshot: ContextSnapshot) -> dict[str, Any]:
    return snapshot_to_cache(snapshot)


def _snapshot_from_cache(data: dict[str, Any]) -> ContextSnapshot:
    return snapshot_from_cache(data)
