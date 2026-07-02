"""NSE status banner."""

from __future__ import annotations

import streamlit as st

from analyzer.nse_session import get_recent_nse_errors, nse_status_message, reset_nse_circuit


def render_nse_error_banner() -> None:
    status = nse_status_message()
    if status:
        c1, c2 = st.columns([5, 1])
        with c1:
            st.info(status)
        with c2:
            if st.button("Retry NSE", key="retry_nse_circuit", help="Reset pause and try NSE again"):
                reset_nse_circuit()
                st.rerun()
        return
    errors = get_recent_nse_errors()
    if errors:
        st.warning("**NSE:** " + " · ".join(errors[:3]))
