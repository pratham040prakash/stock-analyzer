"""Prominent Kite status banner — sign-in only, no API credential forms."""

from __future__ import annotations

import streamlit as st

from analyzer.kite_status import kite_connection_status
from ui.components.broker_connect import (
    render_broker_connect_gate,
    render_broker_reconnect_gate,
)
from ui.components.kite_connect import clear_kite_status_caches


def render_kite_banner(*, cache_key: str = "_kite_status_cache") -> None:
    """Show reconnect prompt when Kite token is missing or expired."""
    cached = st.session_state.get(cache_key)
    if cached is None:
        cached = kite_connection_status(probe=True)
        st.session_state[cache_key] = cached

    level = cached.get("level", "ok")
    if level in ("ok", "limited"):
        return

    snapshot = st.session_state.get("broker_snapshot") or {"state": "disconnected"}
    if level == "expired":
        render_broker_reconnect_gate(snapshot)
    elif level == "missing":
        st.info("Complete one-time broker setup to connect Zerodha.")
    else:
        render_broker_connect_gate(snapshot)

    if st.button("Retry", key=f"kite_banner_retry_{cache_key}", use_container_width=True):
        clear_kite_status_caches()
        st.session_state.pop(cache_key, None)
        st.rerun()
