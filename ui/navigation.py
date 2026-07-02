"""Safe cross-tab navigation (Streamlit blocks nav_tab writes after the radio exists)."""

from __future__ import annotations

import streamlit as st

_NAV_REQUEST_KEY = "_nav_tab_request"


def request_nav_tab(tab: str, **extra_state) -> None:
    """Switch section on next run — call from buttons inside tab content."""
    st.session_state[_NAV_REQUEST_KEY] = tab
    for key, value in extra_state.items():
        st.session_state[key] = value
    st.rerun()


def apply_pending_nav_tab() -> None:
    """Call in app.py immediately before the nav radio widget."""
    pending = st.session_state.pop(_NAV_REQUEST_KEY, None)
    if pending:
        st.session_state["nav_tab"] = pending
