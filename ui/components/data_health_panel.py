"""Data health panel for sidebar."""

from __future__ import annotations

import streamlit as st

from analyzer.data_health import build_data_health


def render_data_health_sidebar(*, probe_kite: bool = False) -> None:
    health = build_data_health(probe_kite=probe_kite)
    with st.expander("📡 Data health", expanded=bool(health.warning)):
        st.caption(f"Intraday source: **{health.primary}**")
        if health.kite_logged_in:
            st.caption(f"Kite: **{health.kite_market_data}**")
        if health.kite_market_data == "personal_app":
            st.error("Personal app — create a **Connect** app for live quotes")
        elif health.warning:
            st.warning(health.warning)
        elif health.ok_for_live_cockpit:
            st.success("Live cockpit data OK")
        elif health.kite_logged_in:
            st.info("Using Yahoo until Kite Connect quotes are active")
        st.caption(health.detail)
        if st.button("Refresh Kite check", key="data_health_probe"):
            h2 = build_data_health(probe_kite=True)
            if h2.kite_live:
                st.success("Kite live quotes OK")
            else:
                st.info(h2.detail)
