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
from ui.components.decision_card import project_decision_card
from ui.components.partner_data import load_dashboard_data
from ui.components.partner_shell import get_partner_dock, render_ask_fab, render_partner_dock
from ui.components.today_brief_experience import render_today_brief_experience
from ui.theme import (
    APEX_BRIEF_EXPERIENCE_CSS,
    APEX_BUSINESS_HEALTH_CSS,
    APEX_INVESTMENT_THESIS_CSS,
    APEX_RECOMMENDATION_EXPLANATION_CSS,
    APEX_RISK_MONITOR_CSS,
    APEX_V2_VISUAL_POLISH_CSS,
    PARTNER_PAGE_ACTIVATE_JS,
    VERDICT_CANVAS_CSS,
)

IST = ZoneInfo("Asia/Kolkata")

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


def _render_thinking_canvas(*, prepare: bool = False) -> None:
    built_at = datetime.now(IST).strftime("%H:%M IST")
    if prepare:
        st.markdown(
            f'<div class="apex-brief-page apex-loading">'
            f'<section class="apex-section apex-greeting">'
            f'<h1 class="apex-greeting-title">Welcome</h1>'
            f'<p class="apex-greeting-sub">We\'re preparing your first brief.</p>'
            f'<p class="apex-greeting-meta">{_esc(built_at)} · Getting ready</p>'
            f"</section></div>",
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        f'<div class="apex-brief-page apex-loading">'
        f'<section class="apex-section apex-greeting">'
        f'<h1 class="apex-greeting-title">Reviewing your day</h1>'
        f'<p class="apex-greeting-sub">Checking market context and what deserves attention.</p>'
        f'<p class="apex-greeting-meta">{_esc(built_at)} · One moment</p>'
        f"</section></div>",
        unsafe_allow_html=True,
    )


def _render_today_canvas(
    *,
    market: str,
    period: str,
    cached: dict[str, Any],
) -> None:
    del period
    ctx = DecisionContextBundle.from_cache_dict(cached)
    broker = ctx.broker
    brief = ctx.assemble_view_model(record_snapshot=False)
    domain = ctx.to_domain()
    card = project_decision_card(brief)

    render_today_brief_experience(
        cached=cached,
        brief=brief,
        card=card,
        broker=broker,
        snapshot=domain.context,
        mis=domain.mis,
        domain_decision=domain.decision,
        pins=domain.pins,
        os_report=domain.os_report,
        prefs=cached["prefs"],
        pulse=cached.get("pulse"),
        portfolio=cached.get("portfolio"),
        journal_today_pnl=cached.get("journal_today_pnl"),
    )


def render_home_dashboard(market: str, *, period: str = "1y", max_trades: int = 1) -> None:
    del max_trades
    st.markdown(
        APEX_V2_VISUAL_POLISH_CSS
        + APEX_BRIEF_EXPERIENCE_CSS
        + APEX_RECOMMENDATION_EXPLANATION_CSS
        + APEX_INVESTMENT_THESIS_CSS
        + APEX_BUSINESS_HEALTH_CSS
        + APEX_RISK_MONITOR_CSS
        + VERDICT_CANVAS_CSS,
        unsafe_allow_html=True,
    )
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)

    cached = load_dashboard_data(market, period, deep=False)

    from ui.components.partner_data import PARTNER_TODAY_LAST_BUNDLE

    from ui.components.answer_canvas import is_ask_overlay_open, render_answer_overlay
    from ui.components.proof_runtime import is_proof_ui_open, proof_canvas_active

    ask_open = is_ask_overlay_open()
    proof_open = proof_canvas_active() and is_proof_ui_open()
    if ask_open or proof_open:
        st.markdown('<div class="vc-main-dimmed">', unsafe_allow_html=True)

    dock = get_partner_dock()
    if cached is None:
        prepare = not st.session_state.get(PARTNER_TODAY_LAST_BUNDLE)
        _render_thinking_canvas(prepare=prepare)
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
