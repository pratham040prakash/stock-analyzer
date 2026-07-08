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

        from analyzer.portfolio_live import post_kite_login_sync
        from analyzer.portfolio_store import portfolio_profile_key

        sync = post_kite_login_sync(profile=portfolio_profile_key())
        if sync.get("holdings"):
            st.session_state["zd_import"] = sync["holdings"]

        name = sync.get("user_name") or sync.get("user_id") or "your account"
        n = sync.get("holdings_count", 0)
        if sync.get("error") and not n:
            st.warning(
                f"Zerodha logged in as **{name}**, but holdings could not be loaded: "
                f"{sync['error']}"
            )
        elif n:
            wl = sync.get("watchlist_added", 0)
            wl_note = (
                f" Synced **{wl}** symbols from Kite positions/orders into watchlist."
                if wl
                else ""
            )
            st.success(
                f"Zerodha connected as **{name}** — fetched **{n} holdings** from Kite.{wl_note} "
                "Open **My Portfolio** or **Daily Advisor** for insights. "
                "*(Kite marketwatch has no API — paste extra symbols in My Portfolio if needed.)*"
            )
        else:
            wl_total = sync.get("watchlist_total", 0)
            wl_note = (
                f" **{wl_total}** watchlist symbols from Kite activity."
                if wl_total
                else " Paste watchlist symbols under **My Portfolio → Kite watchlist mirror**."
            )
            st.success(
                f"Zerodha connected as **{name}**. "
                f"No delivery holdings in Kite.{wl_note}"
            )
        st.caption(
            "Redirect to `127.0.0.1` is normal — Zerodha returns here once so the app "
            "can save your login token, then fetches profile & holdings via API."
        )
        return True
    except Exception as exc:
        st.session_state[failed_key] = True
        st.query_params.clear()
        detail = _checksum_error_message(exc)
        st.error(f"Login failed: {detail}")
        return False
