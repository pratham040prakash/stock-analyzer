"""First-time onboarding tour (multi-step)."""

from __future__ import annotations

import streamlit as st

from analyzer.onboarding_state import (
    get_tour_step,
    is_onboarding_dismissed,
    is_tour_complete,
    set_tour_step,
)
from ui.navigation import request_nav_tab

TOUR_STEPS: list[dict[str, str]] = [
    {
        "title": "Welcome",
        "body": "This app suggests MIS trades with **Entry · Stop · Target**, then scores whether targets hit after close.",
        "action": "Next",
    },
    {
        "title": "Quick scan",
        "body": "After **3:30 PM IST**, open **Suggestions** and tap **Quick scan** — saves top 5 for tomorrow.",
        "action": "Show Suggestions",
        "tab": "Suggestions",
        "kwargs": {"intraday_focus_watchlist": True},
    },
    {
        "title": "Track results",
        "body": "**Track Record** shows **Hit target?** vs session high/low. Star your top 2 to compare vs full list.",
        "action": "Open Track Record",
        "tab": "Track Record",
    },
    {
        "title": "Alpha AI research",
        "body": "**Alpha AI** builds institutional-style reports — export Markdown/PDF, optional LLM narrative.",
        "action": "Open Alpha AI",
        "tab": "Alpha AI",
    },
    {
        "title": "Command palette",
        "body": "Use **⌘ Jump** at the top to search by symbol, name, ISIN, or jump to any tab (e.g. `alpha TCS`).",
        "action": "Finish tour",
    },
]


def render_onboarding_tour(*, force: bool = False) -> None:
    if not force and (is_onboarding_dismissed() or is_tour_complete()):
        return

    step_idx = get_tour_step()
    if step_idx >= len(TOUR_STEPS):
        return

    step = TOUR_STEPS[step_idx]
    with st.container(border=True):
        st.markdown(f"### 🧭 Tour · Step {step_idx + 1}/{len(TOUR_STEPS)} — {step['title']}")
        st.markdown(step["body"])
        c1, c2, c3 = st.columns(3)
        with c1:
            if step_idx > 0 and st.button("Back", key="tour_back"):
                set_tour_step(step_idx - 1)
                st.rerun()
        with c2:
            if st.button("Skip tour", key="tour_skip"):
                set_tour_step(len(TOUR_STEPS))
                st.rerun()
        with c3:
            if st.button(step["action"], key="tour_next", type="primary"):
                tab = step.get("tab")
                set_tour_step(step_idx + 1)
                if tab:
                    request_nav_tab(tab, **(step.get("kwargs") or {}))
                else:
                    st.rerun()
