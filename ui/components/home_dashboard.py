"""AI Trading Partner — Today (Phase 1) + dock shell; Trades via plan_canvas."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from analyzer.use_cases.decision_context_bundle import DecisionContextBundle
from analyzer.use_cases.morning_brief import pick_decision as _pick_decision
from ui.components.canvas_utils import (
    VerdictCanvasState,
    _broker_snapshot,
    _esc,
    _snapshot_from_cache,
    _snapshot_to_cache,
    _strip_md,
    _sync_status,
    _trim_words,
)
from ui.components.decision_card import (
    below_fold_intel_sections,
    compose_hero_intel_html,
    hero_failure_html,
    hero_header_sync_html,
    hero_intel_sections,
    hero_l0_trust_html,
    hero_review_setup_symbol,
    hero_stale_html,
    project_decision_card,
    today_intel_actions_allowed,
)
from ui.components.morning_brief_ui import (
    why_advanced_from_brief,
    why_primary_from_brief,
)
from ui.components.partner_data import load_dashboard_data
from ui.components.partner_shell import get_partner_dock, render_ask_fab, render_partner_dock, set_partner_dock
from ui.theme import PARTNER_PAGE_ACTIVATE_JS, VERDICT_CANVAS_CSS

IST = ZoneInfo("Asia/Kolkata")
TODAY_BROKER_GATE = "today_broker_gate"

__all__ = [
    "VerdictCanvasState",
    "_broker_snapshot",
    "_esc",
    "_pick_decision",
    "_snapshot_from_cache",
    "_snapshot_to_cache",
    "_strip_md",
    "_sync_status",
    "_trim_words",
    "render_home_dashboard",
]


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
        st.session_state[TODAY_BROKER_GATE] = True
        st.rerun()


def _render_broker_gate_inline(broker) -> None:
    from ui.components.broker_connect import (
        render_broker_connect_gate,
        render_broker_error_gate,
        render_broker_reconnect_gate,
    )
    from ui.broker.state import BrokerSnapshot

    snap = broker if isinstance(broker, BrokerSnapshot) else BrokerSnapshot.from_dict(broker)
    if snap.state == "expired":
        render_broker_reconnect_gate(snap)
    elif snap.state in ("offline", "error"):
        render_broker_error_gate(snap)
    else:
        render_broker_connect_gate(snap)


def _render_thinking_canvas() -> None:
    built_at = datetime.now(IST).strftime("%H:%M IST")
    st.markdown(
        f'<div class="verdict-canvas-root" data-verdict="thinking">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync vc-sync-thinking">'
        f'<span class="vc-sync-dot vc-sync-thinking"></span>Reviewing</p>'
        f"</div>"
        f'<div class="vc-verdict-zone">'
        f'<p class="vc-verdict-word vc-thinking-word">Reviewing'
        f'<span class="vc-thinking-dots"><span></span><span></span><span></span></span></p>'
        f"</div>"
        f'<p class="vc-mentor vc-mentor-thinking">Checking market context and your portfolio…</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_verdict_header(
    *,
    card,
    built_at: str,
    intel_html: str = "",
) -> None:
    sync_cls, dot_cls, sync_label = hero_header_sync_html(card)
    stale_html = hero_stale_html(card)
    failure_html = hero_failure_html(card)
    trust_html = hero_l0_trust_html(card) if not card.failure_message else ""
    st.markdown(
        f'<div class="verdict-canvas-root" data-verdict="{_esc(card.verdict_key)}">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f"{stale_html}"
        f"{failure_html}"
        f'<div class="vc-verdict-zone"><p class="vc-verdict-word">{_esc(card.verdict_word)}</p></div>'
        f'<p class="vc-mentor">{_esc(card.reason)}</p>'
        f"{trust_html}"
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


def _render_today_canvas(
    *,
    market: str,
    period: str,
    cached: dict[str, Any],
) -> None:
    ctx = DecisionContextBundle.from_cache_dict(cached)
    brief = ctx.assemble_view_model(record_snapshot=False)
    domain = ctx.to_domain()
    card = project_decision_card(brief)
    state = VerdictCanvasState(card.verdict_key, card.verdict_word, card.cta_label, card.cta_action)

    snapshot = domain.context
    mis = domain.mis
    os_report = domain.os_report
    pins = domain.pins
    decision = domain.decision
    why_primary = why_primary_from_brief(brief)
    why_advanced = why_advanced_from_brief(brief, mis=mis, snapshot=snapshot, pins=pins)

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
    hero_sections = hero_intel_sections(card)
    legacy_sections = tuple(s for s in hero_sections if s != "opportunity")
    legacy_intel = (
        intel_stack_html(center, state, sections=legacy_sections)
        if legacy_sections
        else ""
    )
    hero_intel = compose_hero_intel_html(
        card=card,
        legacy_intel_html=legacy_intel,
        sections=hero_sections,
    )

    _render_verdict_header(
        card=card,
        built_at=str(cached["built_at"]),
        intel_html=hero_intel,
    )

    _render_verdict_ghost_and_cta(
        state=state,
        why_primary=why_primary,
        why_advanced=why_advanced,
        confidence_pct=brief.decision.confidence_level,
    )

    if st.session_state.get(TODAY_BROKER_GATE):
        _render_broker_gate_inline(broker)

    review_symbol = (
        hero_review_setup_symbol(card) if today_intel_actions_allowed(card) else None
    )
    render_today_command_center(
        state=state,
        market=market,
        cached={**cached, "snapshot": snapshot},
        broker=broker,
        decision=decision,
        sections=below_fold_intel_sections(card),
        include_actions=today_intel_actions_allowed(card),
        center=center,
        review_symbol=review_symbol,
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
    if cached is None:
        _render_thinking_canvas()
        render_partner_dock(active=dock)
        render_ask_fab()
        st.rerun()
        return

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
