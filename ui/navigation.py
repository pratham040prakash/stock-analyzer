"""Safe cross-tab navigation (Streamlit blocks nav_tab writes after the radio exists)."""

from __future__ import annotations

import streamlit as st

from ui.theme import DEFAULT_NAV_GROUP, DEFAULT_NAV_TAB, nav_group_for_tab

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
        st.session_state["nav_group"] = nav_group_for_tab(pending)


def init_nav_state() -> None:
    """Ensure group + tab session keys exist and stay consistent."""
    if "nav_tab" not in st.session_state:
        st.session_state["nav_tab"] = DEFAULT_NAV_TAB
    if "nav_group" not in st.session_state:
        st.session_state["nav_group"] = nav_group_for_tab(st.session_state["nav_tab"])
    else:
        st.session_state["nav_group"] = nav_group_for_tab(st.session_state["nav_tab"])


def on_nav_group_change() -> None:
    """Keep nav_tab valid when user switches category."""
    from ui.theme import NAV_GROUPS, ensure_tab_in_group

    group = st.session_state.get("nav_group", DEFAULT_NAV_GROUP)
    tabs = NAV_GROUPS.get(group, [])
    if tabs and st.session_state.get("nav_tab") not in tabs:
        st.session_state["nav_tab"] = tabs[0]

