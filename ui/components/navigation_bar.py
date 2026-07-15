"""Main navigation — standard radios or compact collapsible groups."""

from __future__ import annotations

import streamlit as st

from ui.navigation import on_nav_group_change
from ui.theme import DEFAULT_NAV_GROUP, DEFAULT_NAV_TAB, active_nav_groups, ensure_tab_in_group


def render_app_navigation() -> str:
    """
    Render category + page navigation.
    Returns selected tab name.
    """
    nav_groups = active_nav_groups()
    compact = st.session_state.get("compact_nav", False)

    if compact:
        st.caption("Navigation (compact)")
        selected_tab = st.session_state.get("nav_tab", DEFAULT_NAV_TAB)
        for group, tabs in nav_groups.items():
            expanded = st.session_state.get("nav_group") == group
            with st.expander(group, expanded=expanded):
                for tab in tabs:
                    if st.button(
                        tab,
                        key=f"nav_compact_{group}_{tab}",
                        use_container_width=True,
                        type="primary" if tab == selected_tab else "tertiary",
                    ):
                        st.session_state["nav_group"] = group
                        st.session_state["nav_tab"] = tab
                        selected_tab = tab
                        st.rerun()
        return st.session_state.get("nav_tab", selected_tab)

    st.caption("Choose a category, then a page:")
    st.radio(
        "Category",
        list(nav_groups.keys()),
        horizontal=True,
        label_visibility="collapsed",
        key="nav_group",
        on_change=on_nav_group_change,
    )

    tabs_in_group = nav_groups[st.session_state.get("nav_group", DEFAULT_NAV_GROUP)]
    if st.session_state.get("nav_tab") not in tabs_in_group:
        st.session_state["nav_tab"] = tabs_in_group[0]

    return st.radio(
        "Page",
        tabs_in_group,
        horizontal=True,
        label_visibility="collapsed",
        key="nav_tab",
    )
