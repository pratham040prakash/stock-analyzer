"""Review Depth panel — composes APS-003 through APS-006 renderers (presentation only, V2-002)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from analyzer.decision_engine.models import DecisionArtifact
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from ui.components.business_health import (
    build_business_health_view,
    render_business_health,
)
from ui.components.investment_thesis import (
    build_investment_thesis_view,
    render_investment_thesis,
)
from ui.components.morning_brief_ui import RecommendationContract
from ui.components.recommendation_explanation import (
    build_recommendation_explanation_view,
    render_recommendation_explanation,
)
from ui.components.risk_monitor import (
    build_risk_monitor_view,
    render_risk_monitor,
)

import streamlit as st


def render_decision_depth_panel(
    *,
    brief: MorningBriefViewModel,
    contract: RecommendationContract,
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
    key_prefix: str = "apex_review_depth",
) -> None:
    """Unified Review Depth container — reuses existing APS renderers only."""
    st.markdown(
        '<section class="apex-section apex-review-depth" aria-label="Review depth">'
        '<p class="apex-section-label">Review Depth</p>'
        "</section>",
        unsafe_allow_html=True,
    )

    explanation = build_recommendation_explanation_view(
        brief=brief,
        contract=contract,
        decision=decision,
    )
    with st.expander("Recommendation explanation", expanded=False):
        render_recommendation_explanation(
            explanation,
            key_prefix=f"{key_prefix}_rex",
            title="Recommendation explanation",
        )

    thesis = build_investment_thesis_view(
        brief=brief,
        contract=contract,
        decision=decision,
        mis=mis,
    )
    with st.expander("Investment thesis", expanded=False):
        render_investment_thesis(thesis, key_prefix=f"{key_prefix}_thesis")

    health = build_business_health_view(
        brief=brief,
        contract=contract,
        decision=decision,
        mis=mis,
    )
    with st.expander("Business health", expanded=False):
        render_business_health(health, key_prefix=f"{key_prefix}_health")

    risk = build_risk_monitor_view(
        brief=brief,
        contract=contract,
        decision=decision,
        mis=mis,
    )
    with st.expander("Risk monitor", expanded=False):
        render_risk_monitor(risk, key_prefix=f"{key_prefix}_risk")
