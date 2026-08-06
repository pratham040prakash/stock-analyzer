"""APS-005 Business Health — presentation-only progressive disclosure."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from ui.components.canvas_utils import _esc
from ui.components.morning_brief_ui import (
    BusinessHealthContract,
    RecommendationContract,
    business_health_contract_from_brief,
    investment_thesis_contract_from_brief,
)

BusinessHealthView = BusinessHealthContract


def build_business_health_view(
    *,
    brief,
    contract: RecommendationContract,
    decision=None,
    mis=None,
) -> BusinessHealthView:
    """Project via shared morning_brief_ui helpers."""
    _ = decision
    thesis = investment_thesis_contract_from_brief(brief, contract, mis=mis)
    return business_health_contract_from_brief(brief, contract, thesis)


def _render_section(title: str, lines: tuple[str, ...]) -> None:
    if not lines:
        return
    st.markdown(f"**{title}**")
    for line in lines:
        st.markdown(f"- {_esc(line)}")


def _view_has_content(view: BusinessHealthView) -> bool:
    return bool(
        view.summary
        or view.strengths
        or view.weaknesses
        or view.health_indicators
        or view.monitor_next
        or view.level3_evidence
    )


def render_business_health(
    view: BusinessHealthView,
    *,
    key_prefix: str = "apex_health",
    title: str = "Business health",
) -> None:
    """Render progressive disclosure: summary → drivers → evidence."""
    if not _view_has_content(view):
        return

    summary_html = (
        f'<p class="apex-health-l1">{_esc(view.summary)}</p>' if view.summary else ""
    )
    chips_html = ""
    if view.health_indicators:
        chips = []
        for key, label in view.health_indicators:
            chips.append(
                f'<span class="apex-health-chip" data-indicator="{_esc(key)}">'
                f"{_esc(label)}</span>"
            )
        chips_html = f'<div class="apex-health-chips">{"".join(chips)}</div>'

    st.markdown(
        f'<section class="apex-section apex-health" aria-label="Business health">'
        f'<p class="apex-section-label">{_esc(title)}</p>'
        f"{summary_html}"
        f"{chips_html}"
        f"</section>",
        unsafe_allow_html=True,
    )

    detail_sections = (view.strengths, view.weaknesses, view.monitor_next)
    if any(detail_sections):
        with st.expander("Business drivers", expanded=False, key=f"{key_prefix}_l2"):
            st.caption("Level 2 · Business view")
            _render_section("Business strengths", view.strengths)
            _render_section("Business weaknesses", view.weaknesses)
            _render_section("Monitor next", view.monitor_next)

    if view.level3_evidence:
        with st.expander("Detailed evidence", expanded=False, key=f"{key_prefix}_l3"):
            st.caption("Level 3 · Evidence")
            for line in view.level3_evidence:
                st.markdown(f"- {_esc(line)}")
