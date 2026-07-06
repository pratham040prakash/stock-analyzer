"""Zerodha Kite OAuth redirect handling."""

from __future__ import annotations

import streamlit as st

from analyzer.zerodha import (
    exchange_request_token,
    load_env_credentials,
    save_access_token_to_env,
)
from ui.components.kite_connect import clear_kite_status_caches

_CHECKSUM_HELP = (
    "**Invalid checksum** almost always means the **API Secret does not match your API Key**.\n\n"
    "1. Open [developers.kite.trade](https://developers.kite.trade/) → your app\n"
    "2. If you **regenerated** the secret, copy the **new** secret into sidebar **Zerodha Kite** → Save\n"
    "3. Confirm API key in `.env` matches the app you logged into\n"
    "4. Click **Login with Zerodha** again (each login link works **once** — do not refresh the callback URL)"
)


def _query_param(name: str) -> str:
    val = st.query_params.get(name)
    if isinstance(val, list):
        val = val[0] if val else ""
    return str(val or "").strip()


def _checksum_error_message(exc: Exception) -> str:
    msg = str(exc).lower()
    if "checksum" in msg:
        return _CHECKSUM_HELP
    if "token" in msg and "expired" in msg:
        return "Request token expired — click **Login with Zerodha** again and complete login within 2 minutes."
    return str(exc)


def handle_kite_redirect() -> bool:
    """
    Auto-exchange request_token when Zerodha redirects back to Streamlit.
    Call once at app startup so any tab receives the OAuth callback.
    Returns True if a new token was saved this run.
    """
    request_token = _query_param("request_token")
    if not request_token:
        return False

    failed_key = f"kite_failed_token_{request_token}"
    if st.session_state.get("kite_token_exchanged") == request_token:
        st.query_params.clear()
        return False
    if st.session_state.get(failed_key):
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
        from analyzer.zerodha import hydrate_kite_access_token

        hydrate_kite_access_token()
        clear_kite_status_caches()
        st.query_params.clear()
        st.success("Zerodha connected! Access token saved to `.env` (valid until ~6 AM IST).")
        return True
    except Exception as exc:
        st.session_state[failed_key] = True
        st.query_params.clear()
        detail = _checksum_error_message(exc)
        st.error(f"Login failed: {detail}")
        return False
