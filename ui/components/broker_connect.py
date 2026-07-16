"""Broker connect / reconnect gates — no API credential forms."""

from __future__ import annotations

import streamlit as st

from analyzer.zerodha import get_kite_login_url, load_env_credentials
from ui.broker.bootstrap import reset_broker_bootstrap
from ui.broker.state import BrokerSnapshot
from ui.components.kite_connect import clear_kite_status_caches


def _remember_return_tab() -> None:
    tab = st.session_state.get("nav_tab")
    if tab:
        st.session_state["_broker_return_tab"] = tab


def render_broker_sign_in_button(*, key: str = "broker_sign_in", label: str = "Sign In") -> None:
    creds = load_env_credentials()
    if not creds.get("api_key"):
        st.caption("Complete broker setup in Settings to enable sign in.")
        return
    _remember_return_tab()
    st.link_button(
        label,
        get_kite_login_url(creds["api_key"]),
        type="primary",
        key=key,
        use_container_width=True,
    )


def render_broker_connect_gate(snapshot: BrokerSnapshot | dict | None = None) -> None:
    """Disconnected gate — no credential forms."""
    snap = _as_snapshot(snapshot)
    st.markdown("---")
    st.markdown("##### Broker not connected")
    st.caption("Connect Zerodha to sync holdings, positions, and funds automatically.")
    render_broker_sign_in_button(key="broker_connect_gate", label="Connect")
    st.markdown("---")


def render_broker_reconnect_gate(snapshot: BrokerSnapshot | dict | None = None) -> None:
    """Expired session gate."""
    snap = _as_snapshot(snapshot)
    st.markdown("---")
    st.markdown("##### Session expired")
    st.caption("Reconnect to Zerodha to refresh your portfolio.")
    render_broker_sign_in_button(key="broker_reconnect_gate", label="Sign In")
    if snap.last_sync_at:
        st.caption(f"Last sync · {snap.last_sync_at}")
    st.markdown("---")


def render_broker_error_gate(snapshot: BrokerSnapshot | dict | None = None) -> None:
    snap = _as_snapshot(snapshot)
    message = snap.error_message or "Unable to connect to Zerodha."
    st.markdown("---")
    st.warning(message)
    st.caption("Your most recently synced portfolio is available.")
    if st.button("Retry", key="broker_error_retry", type="primary", use_container_width=True):
        reset_broker_bootstrap()
        clear_kite_status_caches()
        st.rerun()
    st.markdown("---")


def render_portfolio_broker_gate(snapshot: BrokerSnapshot | dict | None = None) -> bool:
    """
    Render broker gate when session is not active.
    Returns True when the rest of Portfolio should be hidden.
    """
    snap = _as_snapshot(snapshot)
    if snap.connected():
        return False
    if snap.state == "expired":
        render_broker_reconnect_gate(snap)
        return True
    if snap.state in ("offline", "error"):
        render_broker_error_gate(snap)
        return False
    render_broker_connect_gate(snap)
    return True


def _as_snapshot(snapshot: BrokerSnapshot | dict | None) -> BrokerSnapshot:
    if snapshot is None:
        try:
            raw = st.session_state.get("broker_snapshot")
            return BrokerSnapshot.from_dict(raw)
        except Exception:
            return BrokerSnapshot()
    if isinstance(snapshot, BrokerSnapshot):
        return snapshot
    return BrokerSnapshot.from_dict(snapshot)
