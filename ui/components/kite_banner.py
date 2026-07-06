"""Prominent Kite / NFO status banner when token is missing or expired."""

from __future__ import annotations

import streamlit as st

from analyzer.kite_status import kite_connection_status
from ui.navigation import request_nav_tab


def render_kite_banner(*, cache_key: str = "_kite_status_cache") -> None:
    """Show fix link when Kite token is missing or expired."""
    cached = st.session_state.get(cache_key)
    if cached is None:
        cached = kite_connection_status(probe=True)
        st.session_state[cache_key] = cached

    level = cached.get("level", "ok")
    if level == "ok":
        return

    headline = cached.get("headline", "Kite issue")
    detail = cached.get("detail", "")
    c1, c2 = st.columns([5, 1])
    with c1:
        if level == "missing":
            st.info(f"**{headline}** — {detail}")
        else:
            st.warning(f"**{headline}** — {detail}")
    with c2:
        if st.button("Fix in 10s", key=f"kite_banner_fix_{cache_key}", use_container_width=True):
            request_nav_tab("My Portfolio")
        if st.button("Retry", key=f"kite_banner_retry_{cache_key}", use_container_width=True):
            st.session_state.pop(cache_key, None)
            st.rerun()
