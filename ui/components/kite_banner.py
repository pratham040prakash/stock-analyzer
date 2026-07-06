"""Prominent Kite / NFO status banner when token is missing or expired."""

from __future__ import annotations

import streamlit as st

from analyzer.kite_status import kite_connection_status
from analyzer.zerodha import get_kite_login_url, load_env_credentials
from ui.components.kite_connect import clear_kite_status_caches, render_kite_connect


def render_kite_banner(*, cache_key: str = "_kite_status_cache") -> None:
    """Show one-click login when Kite token is missing or expired."""
    cached = st.session_state.get(cache_key)
    if cached is None:
        cached = kite_connection_status(probe=True)
        st.session_state[cache_key] = cached

    level = cached.get("level", "ok")
    if level == "ok":
        return
    if level == "limited":
        market = cached.get("market_data", "")
        if market == "personal_app":
            st.error(f"**{cached.get('headline', 'Personal API app')}**")
            st.markdown(cached.get("detail", ""))
        else:
            st.info(f"**{cached.get('headline', 'Kite')}** — {cached.get('detail', '')}")
        return

    creds = load_env_credentials()
    headline = cached.get("headline", "Kite issue")
    detail = cached.get("detail", "")

    if level == "missing":
        st.info(f"**{headline}** — {detail}")
        render_kite_connect(compact=True, key_prefix=f"banner_{cache_key}")
        return

    c1, c2 = st.columns([4, 1])
    with c1:
        st.warning(f"**{headline}** — {detail}")
        if creds.get("api_key"):
            st.link_button(
                "Login with Zerodha",
                get_kite_login_url(creds["api_key"]),
                type="primary",
                key=f"kite_banner_login_{cache_key}",
            )
            st.caption("One click · auto-saves token · no My Portfolio tab needed")
        else:
            render_kite_connect(compact=True, key_prefix=f"banner_{cache_key}")
    with c2:
        if st.button("Retry", key=f"kite_banner_retry_{cache_key}", use_container_width=True):
            clear_kite_status_caches()
            st.session_state.pop(cache_key, None)
            st.rerun()
