"""Prominent data-source banner for Suggestions (Kite / Yahoo / NSE)."""

from __future__ import annotations

import streamlit as st

from analyzer.data_health import build_data_health
from analyzer.market_session import market_session_status
from analyzer.nse_session import is_nse_available, nse_status_message


def render_data_mode_banner(*, key_prefix: str = "dmb") -> None:
    """Show whether live gates and cockpit data are trustworthy."""
    health = build_data_health()
    session = market_session_status()
    nse_ok = is_nse_available()
    nse_msg = nse_status_message()

    if health.kite_live:
        mode = "🟢 **Kite live**"
        detail = "Spot, OR, and option gates use real-time quotes."
        box = st.success
    elif health.kite_market_data == "personal_app":
        mode = "🔴 **Personal Kite app**"
        detail = health.warning or "Create a **Connect** app for live quotes."
        box = st.error
    elif health.kite_logged_in and not health.kite_live:
        mode = "🟡 **Kite logged in — quotes blocked**"
        detail = health.warning or "Reconnect with a Connect app + market data."
        box = st.warning
    elif session.get("is_open"):
        mode = "🟡 **Yahoo fallback (~15–20 min lag)**"
        detail = (
            health.warning
            or "Entry gate & OR may be stale — log in with Kite Connect before trading."
        )
        box = st.warning
    else:
        mode = "⚪ **Market closed**"
        detail = "Fix Kite before 9:15 AM IST for tomorrow's live session."
        box = st.info

    cols = st.columns([3, 1])
    with cols[0]:
        box(f"{mode} — {detail}")
    with cols[1]:
        if not nse_ok and nse_msg:
            st.caption(f"NSE: {nse_msg[:80]}")
        elif not nse_ok:
            st.caption("NSE: circuit open")
        else:
            st.caption("NSE: OK")

    if st.button("Refresh data check", key=f"{key_prefix}_refresh"):
        h2 = build_data_health(probe_kite=True)
        if h2.kite_live:
            st.success("Kite live quotes OK")
        else:
            st.caption(h2.detail or h2.warning)
