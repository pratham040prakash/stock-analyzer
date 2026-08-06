"""Shared progressive disclosure — Help me understand popover (V2 + V3)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import streamlit as st

from ui.components.morning_brief_ui import RecommendationContract


@dataclass(frozen=True)
class UnderstandSection:
    title: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class UnderstandDepthLevels:
    simple: tuple[str, ...]
    business: tuple[str, ...]
    professional: tuple[str, ...]


@dataclass(frozen=True)
class UnderstandContract:
    sections: tuple[UnderstandSection, ...]
    confidence_pct: int | None = None
    depth_levels: UnderstandDepthLevels | None = None


def understand_contract_from_recommendation(
    contract: RecommendationContract,
    *,
    confidence_pct: int | None = None,
) -> UnderstandContract:
    sections: list[UnderstandSection] = []
    for title, lines in (
        ("Why", contract.why),
        ("Evidence", contract.evidence),
        ("Trade-offs", contract.trade_offs),
        ("Risks", contract.risks),
        ("What could change", contract.what_could_change),
        ("Suggested next step", contract.suggested_next_step),
    ):
        if lines:
            sections.append(UnderstandSection(title=title, lines=lines))
    return UnderstandContract(
        sections=tuple(sections),
        confidence_pct=confidence_pct,
        depth_levels=UnderstandDepthLevels(
            simple=contract.help_simple,
            business=contract.help_business,
            professional=contract.help_professional,
        ),
    )


def render_understand_body(
    contract: UnderstandContract,
    *,
    depth_expander_key: str | None = None,
    depth_expanded: bool = True,
) -> None:
    if contract.confidence_pct is not None:
        st.caption(f"Confidence · {contract.confidence_pct}%")
    for section in contract.sections:
        if not section.lines:
            continue
        st.markdown(f"**{section.title}**")
        for line in section.lines:
            st.markdown(f"- {line}")
    if contract.depth_levels:
        with st.expander("Explanation depth", expanded=depth_expanded):
            radio_kwargs: dict[str, Any] = {
                "label": "Level",
                "options": ("Simple", "Business", "Professional"),
                "horizontal": True,
                "label_visibility": "collapsed",
            }
            if depth_expander_key:
                radio_kwargs["key"] = depth_expander_key
            level = st.radio(**radio_kwargs)
            if level == "Simple":
                lines = contract.depth_levels.simple
            elif level == "Business":
                lines = contract.depth_levels.business
            else:
                lines = contract.depth_levels.professional
            for line in lines:
                st.markdown(f"- {line}")


def render_understand_popover(
    contract: UnderstandContract,
    *,
    wrap_popover: bool = True,
    depth_expander_key: str | None = None,
    depth_expanded: bool = True,
    extra_body: Callable[[], None] | None = None,
) -> None:
    """Shared Help me understand gateway — one UX, surface-specific contracts."""

    def _body() -> None:
        render_understand_body(
            contract,
            depth_expander_key=depth_expander_key,
            depth_expanded=depth_expanded,
        )
        if extra_body:
            extra_body()

    if wrap_popover:
        with st.popover("Help me understand"):
            _body()
    else:
        _body()
