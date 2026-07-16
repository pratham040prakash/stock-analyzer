"""Startup broker pipeline — runs before any page renders."""

from __future__ import annotations

import streamlit as st

from analyzer.kite_stream import start_kite_ticker_on_app_start
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from analyzer.zerodha import hydrate_kite_access_token, load_env_credentials
from ui.broker.bootstrap import broker_bootstrap, reset_broker_bootstrap
from ui.broker.oauth_log import oauth_log, oauth_log_exception, startup_trace
from ui.components.kite_auth import (
    _clear_oauth_query_params,
    get_request_token,
    handle_kite_redirect,
)


def _hydrate_saved_portfolio() -> None:
    if st.session_state.get("zd_import"):
        return
    prof = portfolio_profile_key()
    saved = load_saved_portfolio(profile=prof)
    if saved and saved.holdings:
        st.session_state["zd_import"] = saved


def _show_broker_toast() -> None:
    toast = st.session_state.pop("_broker_toast", None)
    if toast:
        st.success(toast)


def run_broker_startup() -> None:
    """
    Strict startup order:
    1. load_env_credentials
    2. handle_kite_redirect (if request_token) — BEFORE broker_bootstrap
    3. hydrate_kite_access_token
    4. broker_bootstrap
    5. hydrate portfolio / ticker
    """
    startup_trace(3, "run_broker_startup.enter")

    startup_trace(3, "load_env_credentials")
    creds = load_env_credentials()
    request_token = get_request_token()
    oauth_callback = bool(request_token)
    startup_trace(
        3,
        "run_broker_startup.oauth_check",
        f"token_present={oauth_callback} api_key={'yes' if creds.get('api_key') else 'no'}",
    )

    # OAuth callback path — must finish before broker_bootstrap.
    if oauth_callback:
        startup_trace(4, "run_broker_startup.oauth_path", "handle_kite_redirect before bootstrap")
        oauth_ok = False
        try:
            oauth_ok = handle_kite_redirect(quiet=True)
        except Exception as exc:
            oauth_log_exception("handle_kite_redirect failed", exc)
            st.session_state["_broker_toast"] = (
                "Unable to complete Zerodha sign in. Please try again."
            )

        _clear_oauth_query_params()

        startup_trace(9, "hydrate_kite_access_token")
        hydrate_kite_access_token()

        if oauth_ok:
            reset_broker_bootstrap()

        startup_trace(10, "broker_bootstrap", "after OAuth callback")
        try:
            broker_bootstrap(force_sync=True)
            oauth_log("Broker bootstrap completed", "after OAuth callback")
        except Exception as exc:
            oauth_log_exception("broker_bootstrap failed", exc)
            from ui.broker.state import load_broker_snapshot, save_broker_snapshot

            snap = load_broker_snapshot()
            snap.state = "error"
            snap.error_message = (
                "Unable to connect to Zerodha. Your most recently synced portfolio is available."
            )
            save_broker_snapshot(snap)
            st.session_state["broker_snapshot"] = snap.to_dict()

        _hydrate_saved_portfolio()
        try:
            start_kite_ticker_on_app_start()
        except Exception:
            pass

        return_tab = st.session_state.pop("_broker_return_tab", None)
        if return_tab and oauth_ok:
            st.session_state["nav_tab"] = return_tab

        st.session_state["_broker_startup_done"] = True
        _show_broker_toast()

        # Sync browser URL after OAuth processing.
        if get_request_token() or oauth_ok:
            startup_trace(11, "st.rerun", "strip OAuth params from browser URL")
            st.rerun()
        startup_trace(12, "run_broker_startup.oauth_path.done")
        return

    # Normal cold-start path (no OAuth callback in URL).
    startup_done = bool(st.session_state.get("_broker_startup_done"))
    if startup_done:
        startup_trace(3, "run_broker_startup.skip", "session already initialized")
        _show_broker_toast()
        return

    status = st.empty()
    status.info("Checking Broker…")

    startup_trace(9, "hydrate_kite_access_token")
    hydrate_kite_access_token()
    status.info("Synchronizing Portfolio…")

    startup_trace(10, "broker_bootstrap")
    try:
        broker_bootstrap(force_sync=not st.session_state.get("_broker_bootstrap_done"))
    except Exception as exc:
        oauth_log_exception("broker_bootstrap failed", exc)
        from ui.broker.state import load_broker_snapshot, save_broker_snapshot

        snap = load_broker_snapshot()
        snap.state = "error"
        snap.error_message = (
            "Unable to connect to Zerodha. Your most recently synced portfolio is available."
        )
        save_broker_snapshot(snap)
        st.session_state["broker_snapshot"] = snap.to_dict()

    _hydrate_saved_portfolio()
    try:
        start_kite_ticker_on_app_start()
    except Exception:
        pass

    st.session_state["_broker_startup_done"] = True
    status.empty()
    _show_broker_toast()
    startup_trace(12, "run_broker_startup.done")
