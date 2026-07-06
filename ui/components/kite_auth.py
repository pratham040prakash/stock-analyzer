"""Zerodha Kite OAuth redirect handling."""

from __future__ import annotations

import streamlit as st

from analyzer.zerodha import (
    exchange_request_token,
    load_env_credentials,
    save_access_token_to_env,
)
from ui.components.kite_connect import clear_kite_status_caches


def handle_kite_redirect() -> bool:
    """
    Auto-exchange request_token when Zerodha redirects back to Streamlit.
    Call once at app startup so any tab receives the OAuth callback.
    Returns True if a new token was saved this run.
    """
    params = st.query_params
    request_token = params.get("request_token")
    if not request_token or st.session_state.get("kite_token_exchanged") == request_token:
        return False

    creds = load_env_credentials()
    if not creds["api_key"] or not creds["api_secret"]:
        st.error(
            "Zerodha redirected with a login token, but API Key/Secret are missing. "
            "Open sidebar **Zerodha Kite** and save credentials first."
        )
        return False

    try:
        access_token = exchange_request_token(
            creds["api_key"], creds["api_secret"], request_token
        )
        save_access_token_to_env(access_token)
        st.session_state["kite_token_exchanged"] = request_token
        st.session_state["kite_access_token"] = access_token
        clear_kite_status_caches()
        st.query_params.clear()
        st.success("Zerodha connected! Access token saved to `.env` (valid until ~6 AM IST).")
        return True
    except Exception as exc:
        st.error(f"Login failed: {exc}. Click **Login with Zerodha** and try again immediately.")
        return False
