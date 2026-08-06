"""Shared dock + Ask chrome for AI Trading Partner (Phases 1–6)."""

from __future__ import annotations

import streamlit as st

PARTNER_DOCK_KEY = "partner_dock"
PARTNER_DEPTH_KEY = "partner_depth"
TRUST_DEPTH = "trust"
_VALID_DOCKS = frozenset({"today", "trades", "you"})


def get_partner_dock() -> str:
    tab = str(st.session_state.get(PARTNER_DOCK_KEY, "today"))
    return tab if tab in _VALID_DOCKS else "today"


def is_trust_depth() -> bool:
    return str(st.session_state.get(PARTNER_DEPTH_KEY, "")) == TRUST_DEPTH


def clear_partner_depth() -> None:
    st.session_state.pop(PARTNER_DEPTH_KEY, None)


def set_partner_dock(tab: str) -> None:
    if tab not in _VALID_DOCKS:
        tab = "today"
    from ui.components.answer_canvas import close_ask_overlay_silent
    from ui.components.proof_runtime import close_proof_ui_silent

    close_proof_ui_silent()
    close_ask_overlay_silent()
    if tab != "you":
        clear_partner_depth()
    st.session_state[PARTNER_DOCK_KEY] = tab
    for key in list(st.session_state.keys()):
        if str(key).startswith("partner_dock_stage_"):
            st.session_state.pop(key, None)
    st.session_state.pop("partner_ask_stage", None)
    st.rerun()


def dock_needs_reset(tab: str, *, active: str) -> bool:
    """True when dock button should fire even if tab already active (overlay open)."""
    from ui.components.answer_canvas import is_ask_overlay_open
    from ui.components.proof_runtime import is_proof_ui_open

    return active != tab or is_proof_ui_open() or is_ask_overlay_open()


def render_partner_dock(*, active: str) -> None:
    st.markdown('<div class="vc-nav-row">', unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3)
    with n1:
        wrap = '<div class="vc-nav-today">' if active == "today" else "<div>"
        st.markdown(wrap, unsafe_allow_html=True)
        if st.button("Brief", key="vc_nav_today", use_container_width=True):
            if dock_needs_reset("today", active=active):
                set_partner_dock("today")
        st.markdown("</div>", unsafe_allow_html=True)
    with n2:
        wrap = '<div class="vc-nav-trades">' if active == "trades" else "<div>"
        st.markdown(wrap, unsafe_allow_html=True)
        if st.button("Investments", key="vc_nav_trades", use_container_width=True):
            if dock_needs_reset("trades", active=active):
                set_partner_dock("trades")
        st.markdown("</div>", unsafe_allow_html=True)
    with n3:
        wrap = '<div class="vc-nav-you">' if active == "you" else "<div>"
        st.markdown(wrap, unsafe_allow_html=True)
        if st.button("Profile", key="vc_nav_you", use_container_width=True):
            if dock_needs_reset("you", active=active):
                set_partner_dock("you")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_ask_fab() -> None:
    from ui.components.answer_canvas import is_ask_overlay_open, open_ask_overlay
    from ui.components.proof_runtime import is_proof_ui_open

    if is_ask_overlay_open() or is_proof_ui_open():
        return
    st.markdown('<div class="vc-ask-wrap">', unsafe_allow_html=True)
    if st.button("Ask", key="vc_ask_pill"):
        open_ask_overlay()
    st.markdown("</div>", unsafe_allow_html=True)
