"""APS-003 Recommendation Explanation — presentation-only progressive disclosure."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from analyzer.decision_engine.models import DecisionArtifact
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from ui.components.canvas_utils import _esc, _strip_md
from ui.components.morning_brief_ui import (
    RecommendationContract,
    recommendation_action_from_brief,
)


@dataclass(frozen=True)
class RecommendationExplanationView:
    """Projection-only view model for recommendation explanation."""

    action_key: str
    action_label: str
    level1_simple: str
    level2_lines: tuple[str, ...]
    level3_lines: tuple[str, ...]
    why: tuple[str, ...]
    evidence: tuple[str, ...]
    risks: tuple[str, ...]
    what_could_change: tuple[str, ...]
    what_to_monitor: tuple[str, ...]


def _what_to_monitor_lines(
    contract: RecommendationContract,
    brief: MorningBriefViewModel,
    *,
    decision: DecisionArtifact | None = None,
) -> tuple[str, ...]:
    lines: list[str] = []
    for line in contract.suggested_next_step:
        text = _strip_md(line)
        if text and text not in lines:
            lines.append(text)
    if decision is not None:
        for raw in (decision.execution_recommendation, decision.capital_recommendation):
            text = _strip_md(str(raw or ""))
            if text and text not in lines:
                lines.append(text)
    for item in brief.evidence.supporting_signals[:2]:
        text = _strip_md(f"{item.label}: {item.value}")
        if text and text not in lines:
            lines.append(text)
    return tuple(lines[:5])


def build_recommendation_explanation_view(
    *,
    brief: MorningBriefViewModel,
    contract: RecommendationContract,
    decision: DecisionArtifact | None = None,
) -> RecommendationExplanationView:
    """Project RecommendationContract → APS-003 explanation sections."""
    action_key, action_label = recommendation_action_from_brief(brief, decision=decision)
    why = contract.why
    evidence = contract.evidence
    risks = contract.risks
    what_could_change = contract.what_could_change
    what_to_monitor = _what_to_monitor_lines(contract, brief, decision=decision)

    level1 = contract.help_simple[0] if contract.help_simple else (why[0] if why else "")
    level2 = tuple(dict.fromkeys(why + evidence))[:8] if (why or evidence) else tuple()
    level3 = contract.help_professional or (
        tuple(dict.fromkeys(why + evidence + contract.trade_offs + risks + what_could_change))[:12]
        if any((why, evidence, contract.trade_offs, risks, what_could_change))
        else tuple()
    )

    return RecommendationExplanationView(
        action_key=action_key,
        action_label=action_label,
        level1_simple=level1,
        level2_lines=level2,
        level3_lines=level3,
        why=why,
        evidence=evidence,
        risks=risks,
        what_could_change=what_could_change,
        what_to_monitor=what_to_monitor,
    )


def _render_section(title: str, lines: tuple[str, ...]) -> None:
    if not lines:
        return
    st.markdown(f"**{title}**")
    for line in lines:
        st.markdown(f"- {_esc(line)}")


def render_recommendation_explanation(
    view: RecommendationExplanationView,
    *,
    key_prefix: str = "apex_rex",
    title: str = "Why this recommendation",
    show_badge: bool = True,
) -> None:
    """Render progressive disclosure: simple → evidence → technical."""
    badge = (
        f'<span class="apex-rex-badge apex-rex-{view.action_key}">{_esc(view.action_label)}</span>'
        if show_badge
        else ""
    )
    level1_html = (
        f'<p class="apex-rex-l1">{_esc(view.level1_simple)}</p>' if view.level1_simple else ""
    )
    st.markdown(
        f'<section class="apex-section apex-rex" aria-label="Recommendation explanation">'
        f'<p class="apex-section-label">{_esc(title)}</p>'
        f"{badge}"
        f"{level1_html}"
        f"</section>",
        unsafe_allow_html=True,
    )

    evidence_sections = (
        view.why,
        view.evidence,
        view.risks,
        view.what_could_change,
        view.what_to_monitor,
    )
    if any(evidence_sections):
        with st.expander("See evidence", expanded=False, key=f"{key_prefix}_l2"):
            st.caption("Level 2 · Evidence")
            _render_section("Why", view.why)
            _render_section("Evidence", view.evidence)
            _render_section("Risks", view.risks)
            _render_section("What could change", view.what_could_change)
            _render_section("What to monitor", view.what_to_monitor)

    if view.level3_lines:
        with st.expander("Technical details", expanded=False, key=f"{key_prefix}_l3"):
            st.caption("Level 3 · Technical")
            for line in view.level3_lines:
                st.markdown(f"- {_esc(line)}")


def render_recommendation_explanation_popover(
    view: RecommendationExplanationView,
    *,
    key_prefix: str = "apex_rex_pop",
) -> None:
    """Compact popover entry point used from hero surfaces."""
    with st.popover("Why this recommendation"):
        render_recommendation_explanation(
            view,
            key_prefix=key_prefix,
            title="Recommendation explanation",
            show_badge=True,
        )
