"""APS-006 Risk Monitor — presentation-only progressive disclosure."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from ui.components.canvas_utils import _esc
from ui.components.morning_brief_ui import (
    RecommendationContract,
    RiskMonitorContract,
    business_health_contract_from_brief,
    investment_thesis_contract_from_brief,
    risk_monitor_contract_from_brief,
)

RiskMonitorView = RiskMonitorContract


def build_risk_monitor_view(
    *,
    brief,
    contract: RecommendationContract,
    decision=None,
    mis=None,
) -> RiskMonitorView:
    """Project via shared morning_brief_ui helpers."""
    _ = decision
    thesis = investment_thesis_contract_from_brief(brief, contract, mis=mis)
    health = business_health_contract_from_brief(brief, contract, thesis)
    return risk_monitor_contract_from_brief(brief, thesis, health)


def _render_section(title: str, lines: tuple[str, ...]) -> None:
    if not lines:
        return
    st.markdown(f"**{title}**")
    for line in lines:
        st.markdown(f"- {_esc(line)}")


def _view_has_content(view: RiskMonitorView) -> bool:
    return bool(
        view.summary
        or view.key_business_risks
        or view.watch_carefully
        or view.thesis_breakers
        or view.supporting_evidence
    )


def render_risk_monitor(
    view: RiskMonitorView,
    *,
    key_prefix: str = "apex_risk",
    title: str = "Risk monitor",
) -> None:
    """Render progressive disclosure: summary → risks → evidence."""
    if not _view_has_content(view):
        return

    summary_html = (
        f'<p class="apex-risk-l1">{_esc(view.summary)}</p>' if view.summary else ""
    )
    badges_html = ""
    if view.key_business_risks:
        badges = []
        for line in view.key_business_risks[:3]:
            badges.append(f'<span class="apex-risk-badge">{_esc(line)}</span>')
        badges_html = f'<div class="apex-risk-badges">{"".join(badges)}</div>'

    st.markdown(
        f'<section class="apex-section apex-risk" aria-label="Risk monitor">'
        f'<p class="apex-section-label">{_esc(title)}</p>'
        f"{summary_html}"
        f"{badges_html}"
        f"</section>",
        unsafe_allow_html=True,
    )

    detail_sections = (
        view.key_business_risks,
        view.watch_carefully,
        view.thesis_breakers,
    )
    if any(detail_sections):
        with st.expander("Risk drivers", expanded=False, key=f"{key_prefix}_l2"):
            st.caption("Level 2 · Risk view")
            _render_section("Key business risks", view.key_business_risks)
            _render_section("Watch carefully", view.watch_carefully)
            _render_section("Potential thesis breakers", view.thesis_breakers)

    if view.supporting_evidence:
        with st.expander("Supporting evidence", expanded=False, key=f"{key_prefix}_l3"):
            st.caption("Level 3 · Evidence")
            for line in view.supporting_evidence:
                st.markdown(f"- {_esc(line)}")
