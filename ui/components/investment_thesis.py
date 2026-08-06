"""APS-004 Investment Thesis — presentation-only progressive disclosure."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from ui.components.canvas_utils import _esc
from ui.components.morning_brief_ui import (
    InvestmentThesisContract,
    RecommendationContract,
    investment_thesis_contract_from_brief,
)

InvestmentThesisView = InvestmentThesisContract


def build_investment_thesis_view(
    *,
    brief,
    contract: RecommendationContract,
    decision=None,
    mis=None,
) -> InvestmentThesisView:
    """Project via shared morning_brief_ui helper (decision unused — contract carries fields)."""
    _ = decision
    return investment_thesis_contract_from_brief(brief, contract, mis=mis)


def _render_section(title: str, lines: tuple[str, ...]) -> None:
    if not lines:
        return
    st.markdown(f"**{title}**")
    for line in lines:
        st.markdown(f"- {_esc(line)}")


def _view_has_content(view: InvestmentThesisView) -> bool:
    return bool(
        view.thesis_statement
        or view.status_label
        or view.strengths
        or view.concerns
        or view.watch_closely
        or view.sell_conditions
        or view.level3_evidence
    )


def render_investment_thesis(
    view: InvestmentThesisView,
    *,
    key_prefix: str = "apex_thesis",
    title: str = "Investment thesis",
) -> None:
    """Render progressive disclosure: summary → drivers → evidence."""
    if not _view_has_content(view):
        return

    badge = (
        f'<span class="apex-thesis-badge apex-thesis-{view.status_key}">'
        f"{_esc(view.status_label)}</span>"
        if view.status_label
        else ""
    )
    statement_html = (
        f'<p class="apex-thesis-l1">{_esc(view.thesis_statement)}</p>'
        if view.thesis_statement
        else ""
    )
    st.markdown(
        f'<section class="apex-section apex-thesis" aria-label="Investment thesis">'
        f'<p class="apex-section-label">{_esc(title)}</p>'
        f"{badge}"
        f"{statement_html}"
        f"</section>",
        unsafe_allow_html=True,
    )

    detail_sections = (
        view.strengths,
        view.concerns,
        view.watch_closely,
        view.sell_conditions,
    )
    if any(detail_sections):
        with st.expander("Thesis drivers", expanded=False, key=f"{key_prefix}_l2"):
            st.caption("Level 2 · Business view")
            _render_section("Business strengths", view.strengths)
            _render_section("Areas of concern", view.concerns)
            _render_section("Watch closely", view.watch_closely)
            _render_section("When would I sell?", view.sell_conditions)

    if view.level3_evidence:
        with st.expander("Supporting evidence", expanded=False, key=f"{key_prefix}_l3"):
            st.caption("Level 3 · Evidence")
            for line in view.level3_evidence:
                st.markdown(f"- {_esc(line)}")
