"""Today's Brief — product-first presentation layer (UI only, APS-001)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from ui.broker.state import BrokerSnapshot
from ui.components.canvas_utils import VerdictCanvasState, _esc
from ui.components.decision_card import DecisionCardViewModel
from ui.components.morning_brief_ui import (
    RecommendationContract,
    recommendation_contract_from_brief,
)
from ui.components.recommendation_explanation import (
    build_recommendation_explanation_view,
    render_recommendation_explanation,
)
from ui.components.investment_thesis import (
    build_investment_thesis_view,
    render_investment_thesis,
)
from ui.components.business_health import (
    build_business_health_view,
    render_business_health,
)
from ui.components.risk_monitor import (
    build_risk_monitor_view,
    render_risk_monitor,
)
from ui.components.partner_shell import set_partner_dock
from ui.components.today_intelligence import TodayCommandCenter, build_today_command_center

IST = ZoneInfo("Asia/Kolkata")
TODAY_SKIP_PORTFOLIO = "today_skip_portfolio"


def _display_name(broker: BrokerSnapshot) -> str:
    raw = (broker.user_name or "").strip()
    if raw:
        return raw.split()[0]
    return "there"


def _time_greeting() -> str:
    hour = datetime.now(IST).hour
    if hour < 12:
        return "Good Morning"
    if hour < 17:
        return "Good Afternoon"
    return "Good Evening"


def _human_sync_label(card: DecisionCardViewModel) -> str:
    if card.broker_connected:
        if card.sync_state == "warn":
            return "Portfolio sync · updating"
        return "Portfolio connected"
    return "Portfolio not connected"


def _human_regime(snapshot: ContextSnapshot) -> str:
    regime = (snapshot.market_regime or "").strip().lower()
    mapping = {
        "range bound": "Markets are moving sideways today.",
        "range-bound": "Markets are moving sideways today.",
        "range": "Markets are moving sideways today.",
        "neutral": "Markets are balanced — no strong trend has developed.",
        "bullish": "Markets are showing positive momentum today.",
        "bearish": "Markets are under pressure today — caution is warranted.",
        "volatile": "Markets are volatile today — patience may beat aggression.",
    }
    for key, text in mapping.items():
        if key in regime:
            return text
    if regime:
        return f"Markets are in a {regime} phase today."
    return "Markets are balanced — no strong trend has developed."


def _human_market_body(snapshot: ContextSnapshot, center: TodayCommandCenter) -> tuple[str, str]:
    headline = _human_regime(snapshot)
    support = center.market_support.strip() if center else ""
    if support:
        body = support
    else:
        body = (
            "No strong trend has developed. "
            "Patience is likely better than aggressive trading."
        )
    body = body.replace("RISK-OFF", "defensive").replace("RISK-ON", "supportive")
    body = body.replace("broker offline", "portfolio not connected")
    return headline, body


def _product_current_view(card: DecisionCardViewModel) -> str:
    key = card.verdict_key
    if key == "trade":
        opp = card.best_opportunity
        if opp and opp.visible:
            return f"Review {opp.symbol} today"
        return "One investment deserves your attention"
    if key == "pause":
        return "Protect your capital today"
    if key == "rest":
        return "Markets are resting"
    if key in ("wait", "connect"):
        return "No immediate action required"
    return card.verdict_word or "No immediate action required"


def _product_today_action(card: DecisionCardViewModel) -> str:
    if card.verdict_key == "trade" and card.best_opportunity and card.best_opportunity.visible:
        return "1 investment requires review"
    if card.verdict_key == "pause":
        return "Take a breather today"
    if card.verdict_key == "rest":
        return "Review your week"
    return "No immediate action required"


def _review_time_minutes(card: DecisionCardViewModel) -> str:
    if card.verdict_key == "trade":
        return "3 minutes"
    if card.verdict_key == "pause":
        return "1 minute"
    return "2 minutes"


def _portfolio_status_label(brief: MorningBriefViewModel, card: DecisionCardViewModel) -> str:
    if not card.broker_connected:
        return "Not connected"
    if brief.portfolio.ready:
        return "Healthy"
    if brief.portfolio.holdings_count == 0:
        return "Connected · empty"
    return "Needs attention"


def _product_why_line(
    card: DecisionCardViewModel,
    brief: MorningBriefViewModel,
    center: TodayCommandCenter,
    snapshot: ContextSnapshot,
) -> str:
    reason = (card.reason or "").strip()
    lower = reason.lower()
    if card.verdict_key == "connect" or "zerodha" in lower or "broker" in lower or "connect" in lower:
        if center.ai_recommendation and "zerodha" not in center.ai_recommendation.lower():
            return center.ai_recommendation
        _, body = _human_market_body(snapshot, center)
        return body
    if reason:
        return reason
    if brief.trust.why_this_is_recommended:
        return brief.trust.why_this_is_recommended
    return "Conditions are mixed — patience beats forcing a trade."


def _product_recommendation(
    card: DecisionCardViewModel,
    contract: RecommendationContract,
    center: TodayCommandCenter,
) -> str:
    if contract.suggested_next_step:
        step = contract.suggested_next_step[0]
        lower = step.lower()
        if "zerodha" not in lower and lower != "connect":
            return step
    rec = center.ai_recommendation if center else ""
    if rec and "zerodha" not in rec.lower() and "broker" not in rec.lower():
        return rec
    if card.verdict_key == "trade":
        return "Review the plan before committing capital."
    return "Stay patient — let price confirm before you act."


def _confidence_label(card: DecisionCardViewModel) -> str:
    band = (card.confidence_band or "").strip().lower()
    if band == "high":
        return "High confidence"
    if band == "medium":
        return "Moderate confidence"
    if band == "low":
        return "Lower confidence — proceed carefully"
    if card.confidence_level:
        return f"{card.confidence_level}% confidence"
    return "Confidence updating"


def _render_contract_popover(
    *,
    contract: RecommendationContract,
    confidence_pct: int | None,
) -> None:
    with st.popover("Help me understand"):
        if confidence_pct is not None:
            st.caption(f"Confidence · {confidence_pct}%")
        for title, lines in (
            ("Why", contract.why),
            ("Evidence", contract.evidence),
            ("Trade-offs", contract.trade_offs),
            ("Risks", contract.risks),
            ("What could change", contract.what_could_change),
            ("Suggested next step", contract.suggested_next_step),
        ):
            if not lines:
                continue
            st.markdown(f"**{title}**")
            for line in lines:
                st.markdown(f"- {line}")
        with st.expander("Explanation depth"):
            level = st.radio(
                "Level",
                ("Simple", "Business", "Professional"),
                horizontal=True,
                label_visibility="collapsed",
            )
            if level == "Simple":
                lines = contract.help_simple
            elif level == "Business":
                lines = contract.help_business
            else:
                lines = contract.help_professional
            for line in lines:
                st.markdown(f"- {line}")


def _render_greeting(*, built_at: str, broker: BrokerSnapshot, refreshing: bool) -> None:
    name = _display_name(broker)
    now = datetime.now(IST).strftime("%I:%M %p IST").lstrip("0")
    refresh_note = "Updating today's brief…" if refreshing else f"Last refreshed · {built_at}"
    st.markdown(
        f'<section class="apex-section apex-greeting" aria-label="Greeting">'
        f'<h1 class="apex-greeting-title">{_esc(_time_greeting())}, {_esc(name)}</h1>'
        f'<p class="apex-greeting-sub">We\'ve reviewed everything while you were away.</p>'
        f'<p class="apex-greeting-meta">{_esc(now)} · {_esc(refresh_note)}</p>'
        f"</section>",
        unsafe_allow_html=True,
    )


def _render_executive_summary(
    *,
    portfolio_status: str,
    today_action: str,
    review_time: str,
) -> None:
    st.markdown(
        '<section class="apex-section apex-exec" aria-label="Executive summary">'
        '<p class="apex-section-label">Executive Summary</p>'
        '<div class="apex-exec-grid">'
        f'<div class="apex-exec-card"><span class="apex-exec-k">Portfolio</span>'
        f'<span class="apex-exec-v">{_esc(portfolio_status)}</span></div>'
        f'<div class="apex-exec-card"><span class="apex-exec-k">Today\'s Action</span>'
        f'<span class="apex-exec-v">{_esc(today_action)}</span></div>'
        f'<div class="apex-exec-card"><span class="apex-exec-k">Review Time</span>'
        f'<span class="apex-exec-v">{_esc(review_time)}</span></div>'
        "</div></section>",
        unsafe_allow_html=True,
    )


def _render_todays_brief_hero(
    *,
    current_view: str,
    why: str,
    confidence: str,
    recommendation: str,
    card: DecisionCardViewModel,
) -> None:
    st.markdown(
        '<section class="apex-section apex-brief-hero" aria-label="Today\'s Brief">'
        '<p class="apex-section-label">Today\'s Brief</p>'
        f'<p class="apex-brief-view">{_esc(current_view)}</p>'
        f'<p class="apex-brief-why">{_esc(why)}</p>'
        f'<p class="apex-brief-confidence">{_esc(confidence)}</p>'
        f'<p class="apex-brief-rec"><span class="apex-brief-rec-k">Recommendation</span> '
        f'{_esc(recommendation)}</p>'
        "</section>",
        unsafe_allow_html=True,
    )
    from ui.components.proof_runtime import proof_canvas_active

    if proof_canvas_active() and card.verdict_key in ("trade", "wait", "pause"):
        if st.button("See the proof", key="apex_brief_proof", use_container_width=True):
            from ui.components.proof_state import open_proof_overlay

            open_proof_overlay(origin="today", proof_mode=card.verdict_key)


def _render_priority_review(*, card: DecisionCardViewModel, center: TodayCommandCenter) -> None:
    if card.verdict_key != "trade" or not card.best_opportunity or not card.best_opportunity.visible:
        return
    opp = card.best_opportunity
    lines = [f"{opp.symbol} — {opp.setup}" if opp.setup else opp.symbol]
    if center.selection_reason:
        lines.append(center.selection_reason)
    st.markdown(
        '<section class="apex-section apex-priority" aria-label="Priority review">'
        '<p class="apex-section-label">Priority Review</p>'
        f'<p class="apex-priority-lead">{_esc(lines[0])}</p>'
        + (
            f'<p class="apex-priority-detail">{_esc(lines[1])}</p>'
            if len(lines) > 1
            else ""
        )
        + "</section>",
        unsafe_allow_html=True,
    )
    if st.button("Review investment", key="apex_priority_review", type="primary", use_container_width=True):
        set_partner_dock("trades")


def _render_market_today(*, headline: str, body: str, detail: str) -> None:
    st.markdown(
        '<section class="apex-section apex-market" aria-label="Market today">'
        '<p class="apex-section-label">Market Today</p>'
        f'<p class="apex-market-head">{_esc(headline)}</p>'
        f'<p class="apex-market-body">{_esc(body)}</p>'
        "</section>",
        unsafe_allow_html=True,
    )
    with st.expander("Read more"):
        st.markdown(detail or body)


def _render_portfolio_connection(*, broker: BrokerSnapshot) -> None:
    if broker.connected() or st.session_state.get(TODAY_SKIP_PORTFOLIO):
        return
    st.markdown(
        '<section class="apex-section apex-connect" aria-label="Portfolio connection">'
        '<p class="apex-section-label">Portfolio Connection</p>'
        '<p class="apex-connect-title">Personalize Your Brief</p>'
        '<p class="apex-connect-body">Connect your portfolio to receive personalized recommendations.</p>'
        "</section>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Connect Portfolio", key="apex_connect_portfolio", use_container_width=True):
            st.session_state["today_broker_gate"] = True
            st.rerun()
    with c2:
        if st.button(
            "Continue Without Connecting",
            key="apex_skip_portfolio",
            use_container_width=True,
        ):
            st.session_state[TODAY_SKIP_PORTFOLIO] = True
            st.rerun()
    if st.session_state.get("today_broker_gate"):
        from ui.components.broker_connect import render_broker_sign_in_button

        render_broker_sign_in_button(key="apex_brief_sign_in", label="Connect Portfolio")


def _render_learning() -> None:
    st.markdown(
        '<section class="apex-section apex-learning" aria-label="Learning">'
        '<p class="apex-section-label">Learning</p>'
        '<p class="apex-learning-title">Today\'s Investing Lesson</p>'
        '<p class="apex-learning-body">The best trade is often the one you do not take. '
        "Discipline compounds — inconsistency erodes edge.</p>"
        '<p class="apex-learning-meta">Reading time · 2 minutes</p>'
        "</section>",
        unsafe_allow_html=True,
    )


def _render_brief_primary_action(*, card: DecisionCardViewModel) -> None:
    if card.verdict_key == "connect":
        return
    if card.verdict_key == "trade":
        label = "Review investment"
        action = "plan"
    elif card.verdict_key == "rest":
        label = "View your week"
        action = "week"
    elif card.verdict_key == "pause":
        label = "You're clear for today"
        action = "done"
    else:
        label = "You're clear for today"
        action = "done"
    if st.button(label, key="apex_brief_primary", type="primary", use_container_width=True):
        if action == "plan":
            set_partner_dock("trades")
        elif action == "week":
            set_partner_dock("you")
        elif action == "done":
            st.toast("Nothing urgent today — you're clear.")


def render_today_brief_experience(
    *,
    cached: dict[str, Any],
    brief: MorningBriefViewModel,
    card: DecisionCardViewModel,
    broker: BrokerSnapshot,
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    domain_decision: DecisionArtifact | None,
    pins: list,
    os_report,
    prefs,
    pulse,
    portfolio,
    journal_today_pnl,
) -> None:
    """Product-first Today's page — presentation only."""
    state = VerdictCanvasState(card.verdict_key, card.verdict_word, card.cta_label, card.cta_action)
    contract = recommendation_contract_from_brief(
        brief,
        decision=domain_decision,
        mis=mis,
        snapshot=snapshot,
        pins=pins,
    )
    center = build_today_command_center(
        state=state,
        snapshot=snapshot,
        mis=mis,
        os_report=os_report,
        pins=pins,
        pulse=pulse,
        portfolio=portfolio,
        prefs=prefs,
        broker=broker,
        journal_today_pnl=journal_today_pnl,
        decision=domain_decision,
    )

    st.markdown('<div class="apex-brief-page">', unsafe_allow_html=True)

    if card.failure_message:
        st.markdown(
            f'<p class="apex-failure" role="alert">{_esc(card.failure_message)}</p>',
            unsafe_allow_html=True,
        )

    if card.stale and card.stale_label:
        st.markdown(
            f'<p class="apex-stale" role="status">{_esc(card.stale_label)}</p>',
            unsafe_allow_html=True,
        )

    _render_greeting(
        built_at=str(cached.get("built_at", "")),
        broker=broker,
        refreshing=bool(cached.get("_refreshing")),
    )

    _render_executive_summary(
        portfolio_status=_portfolio_status_label(brief, card),
        today_action=_product_today_action(card),
        review_time=_review_time_minutes(card),
    )

    why = _product_why_line(card, brief, center, snapshot)
    market_headline, market_body = _human_market_body(snapshot, center)
    market_detail = center.market_support or center.market_gate
    market_detail = market_detail.replace("broker offline", "portfolio not connected")

    _render_todays_brief_hero(
        current_view=_product_current_view(card),
        why=why,
        confidence=_confidence_label(card),
        recommendation=_product_recommendation(card, contract, center),
        card=card,
    )

    explanation = build_recommendation_explanation_view(
        brief=brief,
        contract=contract,
        decision=domain_decision,
    )
    render_recommendation_explanation(explanation, key_prefix="apex_today_rex")

    thesis = build_investment_thesis_view(
        brief=brief,
        contract=contract,
        decision=domain_decision,
        mis=mis,
    )
    render_investment_thesis(thesis, key_prefix="apex_today_thesis")

    health = build_business_health_view(
        brief=brief,
        contract=contract,
        decision=domain_decision,
        mis=mis,
    )
    render_business_health(health, key_prefix="apex_today_health")

    risk = build_risk_monitor_view(
        brief=brief,
        contract=contract,
        decision=domain_decision,
        mis=mis,
    )
    render_risk_monitor(risk, key_prefix="apex_today_risk")

    _render_priority_review(card=card, center=center)
    _render_market_today(headline=market_headline, body=market_body, detail=market_detail)
    _render_portfolio_connection(broker=broker)
    _render_learning()
    _render_brief_primary_action(card=card)

    st.markdown(
        f'<p class="apex-foot">Portfolio data syncs securely when connected. '
        f'You always own the final decision.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
