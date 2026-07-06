"""Dark / light theme toggle (CSS overlay)."""

from __future__ import annotations

import streamlit as st

from analyzer.ui_preferences import get_theme, set_theme
from ui.theme import LIGHT_THEME_CSS


def init_theme_state() -> None:
    if "ui_theme" not in st.session_state:
        st.session_state["ui_theme"] = get_theme()


def apply_theme_css() -> None:
    init_theme_state()
    if st.session_state.get("ui_theme") == "light":
        st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


def render_theme_toggle_sidebar() -> None:
    init_theme_state()
    choice = st.radio(
        "Theme",
        ["dark", "light"],
        format_func=lambda x: "🌙 Dark" if x == "dark" else "☀️ Light",
        horizontal=True,
        key="ui_theme_radio",
        index=0 if st.session_state.get("ui_theme", "dark") == "dark" else 1,
    )
    if choice != st.session_state.get("ui_theme"):
        st.session_state["ui_theme"] = choice
        set_theme(choice)
        st.rerun()
