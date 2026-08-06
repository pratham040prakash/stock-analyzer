"""Investment Review hero — APS-002 presentation layer (UI only)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from typing import Any

import streamlit as st

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from ui.broker.state import BrokerSnapshot
from ui.components.canvas_utils import VerdictCanvasState, _esc
from ui.components.decision_card import DecisionCardViewModel, hero_review_setup_symbol
from ui.components.morning_brief_ui import (
    RecommendationContract,
    answer_key_from_brief,
    human_review_freshness_label,
    recommendation_contract_from_brief,
)
from ui.components.partner_shell import set_partner_dock
from ui.components.proof_runtime import proof_canvas_active
from ui.components.proof_state import open_proof_overlay
from ui.navigation import request_nav_tab

# Shared Today Brief presentation helpers — projection only.
# TODO: Consider moving to a shared presentation module if reused by additional experiences.
from ui.components.today_brief_experience import (
    _confidence_label,
    _product_recommendation,
    _product_today_action,
    _render_contract_popover,
    _review_time_minutes,
)
from ui.components.today_intelligence import build_today_command_center


def investment_display_name(
    *,
    card: DecisionCardViewModel,
    plan_symbol: str | None,
    os_report: InvestmentOS,
) -> str:
    sym = hero_review_setup_symbol(card)
    if sym:
        return sym
    if plan_symbol:
        return plan_symbol
    star = (os_report.starred_symbol or "").upper().replace(".NS", "").replace(".BO", "")
    if star:
        return star
    opp = card.best_opportunity
    if opp and opp.visible and opp.symbol:
        return opp.symbol
    return "Investment review"


def investment_review_why_line(
    *,
    card: DecisionCardViewModel,
    contract: RecommendationContract,
    brief: MorningBriefViewModel,
) -> str:
    if contract.why:
        return contract.why[0]
    reason = (card.reason or "").strip()
    if reason:
        return reason
    if brief.trust.why_this_is_recommended:
        return brief.trust.why_this_is_recommended
    return ""


def investment_review_time_label(card: DecisionCardViewModel) -> str:
    label = (_review_time_minutes(card) or "").strip()
    return label or "Quick Review"


def _dispatch_primary_action(card: DecisionCardViewModel) -> None:
    """Route existing card CTA actions — navigation only, no decision logic."""
    action = (card.cta_action or "done").strip().lower()
    if action == "plan":
        return
    if action == "connect":
        request_nav_tab("My Portfolio")
        return
    if action == "week":
        set_partner_dock("you")
        return
    if action == "done":
        st.toast("Nothing urgent today — you're clear.")
        set_partner_dock("today")
        return
    set_partner_dock("today")


def _render_investment_hero_html(
    *,
    investment_name: str,
    badge_key: str,
    badge_label: str,
    today_status: str,
    recommendation: str,
    why_line: str,
    confidence: str,
    review_time: str,
    freshness: str,
) -> None:
    why_block = ""
    if why_line:
        why_block = (
            f'<p class="apex-inv-row apex-inv-why">'
            f'<span class="apex-inv-k">Why this review</span>'
            f"{_esc(why_line)}</p>"
        )
    st.markdown(
        '<section class="apex-section apex-inv-hero" aria-label="Investment review hero">'
        '<p class="apex-section-label">Investment Review</p>'
        f'<h1 class="apex-inv-name">{_esc(investment_name)}</h1>'
        f'<p class="apex-inv-badge" data-badge="{_esc(badge_key)}">{_esc(badge_label)}</p>'
        f'<p class="apex-inv-row apex-inv-status">'
        f'<span class="apex-inv-k">Today\'s status</span>{_esc(today_status)}</p>'
        f'<p class="apex-inv-row apex-inv-rec">'
        f'<span class="apex-inv-k">Recommendation</span>{_esc(recommendation)}</p>'
        f"{why_block}"
        f'<p class="apex-inv-row apex-inv-confidence">'
        f'<span class="apex-inv-k">Decision confidence</span>{_esc(confidence)}</p>'
        f'<p class="apex-inv-row apex-inv-time">'
        f'<span class="apex-inv-k">Review time</span>{_esc(review_time)}</p>'
        f'<p class="apex-inv-fresh" role="status">{_esc(freshness)}</p>'
        "</section>",
        unsafe_allow_html=True,
    )


def render_investment_hero_experience(
    *,
    cached: dict[str, Any],
    brief: MorningBriefViewModel,
    card: DecisionCardViewModel,
    broker: BrokerSnapshot,
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    domain_decision: DecisionArtifact | None,
    pins: list,
    os_report: InvestmentOS,
    prefs,
    pulse,
    portfolio,
    journal_today_pnl,
    plan_symbol: str | None = None,
) -> None:
    """APS-002 Hero Recommendation — presentation only."""
    contract = recommendation_contract_from_brief(
        brief,
        decision=domain_decision,
        mis=mis,
        snapshot=snapshot,
        pins=pins,
    )
    state = VerdictCanvasState(card.verdict_key, card.verdict_word, card.cta_label, card.cta_action)
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

    badge_key, badge_label = answer_key_from_brief(brief)
    why_line = investment_review_why_line(card=card, contract=contract, brief=brief)
    freshness = human_review_freshness_label(
        built_at=str(cached.get("built_at", "")),
        last_updated=card.last_updated,
        stale=card.stale,
        stale_label=card.stale_label,
        refreshing=bool(cached.get("_refreshing")),
        offline=not broker.connected(),
    )

    _render_investment_hero_html(
        investment_name=investment_display_name(
            card=card,
            plan_symbol=plan_symbol,
            os_report=os_report,
        ),
        badge_key=badge_key,
        badge_label=badge_label,
        today_status=_product_today_action(card),
        recommendation=_product_recommendation(card, contract, center),
        why_line=why_line,
        confidence=_confidence_label(card),
        review_time=investment_review_time_label(card),
        freshness=freshness,
    )

    c1, c2 = st.columns(2)
    with c1:
        _render_contract_popover(
            contract=contract,
            confidence_pct=brief.decision.confidence_level,
        )
    with c2:
        if proof_canvas_active() and card.verdict_key in ("trade", "wait", "pause"):
            if st.button("See the proof", key="inv_hero_proof", use_container_width=True):
                open_proof_overlay(origin="trades", proof_mode=card.verdict_key)

    label = (card.cta_label or "Back to Today").strip()
    if st.button(label, key="inv_hero_primary", type="primary", use_container_width=True):
        _dispatch_primary_action(card)
