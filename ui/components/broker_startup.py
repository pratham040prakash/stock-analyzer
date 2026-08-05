"""Startup broker pipeline — runs before any page renders."""

from __future__ import annotations

import streamlit as st

from analyzer.kite_stream import start_kite_ticker_on_app_start
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from analyzer.zerodha import hydrate_kite_access_token
from ui.broker.bootstrap import broker_bootstrap
from ui.broker.oauth_log import oauth_log_exception, startup_trace


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
    Cold-start broker pipeline (OAuth is owned by BrokerSessionService.initialize).

    Order:
    1. hydrate_kite_access_token
    2. broker_bootstrap
    3. hydrate portfolio / ticker
    """
    startup_trace(3, "run_broker_startup.enter")

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
