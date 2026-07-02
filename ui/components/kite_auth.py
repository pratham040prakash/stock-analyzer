"""Zerodha Kite OAuth redirect handling."""

from __future__ import annotations

import streamlit as st

from analyzer.zerodha import (
    exchange_request_token,
    load_env_credentials,
    save_access_token_to_env,
)


def handle_kite_redirect() -> None:
    """Auto-exchange request_token when Zerodha redirects back to Streamlit."""
    params = st.query_params
    request_token = params.get("request_token")
    if not request_token or st.session_state.get("kite_token_exchanged") == request_token:
        return

    creds = load_env_credentials()
    if not creds["api_key"] or not creds["api_secret"]:
        st.error("Set ZERODHA_API_KEY and ZERODHA_API_SECRET in .env first.")
        return

    try:
        access_token = exchange_request_token(
            creds["api_key"], creds["api_secret"], request_token
        )
        save_access_token_to_env(access_token)
        st.session_state["kite_token_exchanged"] = request_token
        st.session_state["kite_access_token"] = access_token
        st.query_params.clear()
        st.success("Zerodha connected! Access token saved to `.env` (valid until ~6 AM IST).")
    except Exception as exc:
        st.error(f"Login failed: {exc}. Click the login link below and try again immediately.")
