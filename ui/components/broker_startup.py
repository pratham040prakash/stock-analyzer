"""Startup broker pipeline — runs before any page renders."""

from __future__ import annotations

import streamlit as st

from analyzer.kite_stream import start_kite_ticker_on_app_start
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from analyzer.zerodha import hydrate_kite_access_token
from ui.broker.bootstrap import broker_bootstrap, reset_broker_bootstrap
from ui.broker.oauth_log import oauth_log, oauth_log_exception
from ui.components.kite_auth import handle_kite_redirect, has_kite_oauth_callback


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
    Personal desktop startup:
    1. OAuth callback (request_token) — always when present in URL
    2. broker_bootstrap — verify + sync
    3. hydrate cached portfolio + optional ticker
    """
    oauth_callback = has_kite_oauth_callback()
    startup_done = bool(st.session_state.get("_broker_startup_done"))

    if startup_done and not oauth_callback:
        oauth_log("Startup skipped", "session already initialized")
        _show_broker_toast()
        return

    if oauth_callback and startup_done:
        oauth_log("Callback on return visit", "re-running OAuth handler after prior startup")

    status = st.empty() if not startup_done else None
    if status:
        status.info("Checking Broker…")
    elif oauth_callback:
        oauth_log("Broker bootstrap started", "OAuth return path")

    oauth_ok = False
    try:
        oauth_ok = handle_kite_redirect(quiet=True)
    except Exception as exc:
        oauth_log_exception("handle_kite_redirect failed", exc)
        st.session_state["_broker_toast"] = (
            "Unable to complete Zerodha sign in. Please try again."
        )

    if oauth_ok:
        reset_broker_bootstrap()

    hydrate_kite_access_token()
    if status:
        status.info("Synchronizing Portfolio…")

    try:
        broker_bootstrap(force_sync=oauth_ok or not st.session_state.get("_broker_bootstrap_done"))
        if oauth_ok:
            oauth_log("Broker bootstrap completed", "after OAuth callback")
    except Exception as exc:
        oauth_log_exception("broker_bootstrap failed", exc)
        from ui.broker.state import BrokerSnapshot, load_broker_snapshot, save_broker_snapshot

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

    if not startup_done:
        st.session_state["_broker_startup_done"] = True
        if status:
            status.empty()

    _show_broker_toast()
