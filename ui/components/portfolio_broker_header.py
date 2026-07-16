"""Portfolio broker status header — connected session summary."""

from __future__ import annotations

import streamlit as st

from ui.broker.state import BrokerSnapshot


def render_portfolio_broker_header(snapshot: BrokerSnapshot | dict | None = None) -> None:
    snap = _as_snapshot(snapshot)
    if not snap.connected():
        return

    status_label = "Broker Connected"
    if snap.state == "limited":
        status_label = "Broker Connected (limited quotes)"

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Broker Status", status_label)
    c2.metric("Last Sync", snap.last_sync_at or "—")
    c3.metric("Portfolio Value", _inr(snap.portfolio_value_inr))
    c4.metric("Today's P&L", _inr(snap.today_unrealized_pnl_inr))
    c5.metric("Cash", _inr(snap.available_cash_inr))
    c6.metric("Positions", str(snap.positions_count))

    if snap.user_name or snap.user_id:
        st.caption(
            f"Zerodha · {snap.user_name or snap.user_id}"
            + (f" · {snap.holdings_count} holdings" if snap.holdings_count else "")
        )


def _inr(value: float) -> str:
    if not value:
        return "—"
    if abs(value) >= 100000:
        return f"₹{value / 100000:.2f} L"
    return f"₹{value:,.0f}"


def _as_snapshot(snapshot: BrokerSnapshot | dict | None) -> BrokerSnapshot:
    if snapshot is None:
        raw = st.session_state.get("broker_snapshot")
        return BrokerSnapshot.from_dict(raw)
    if isinstance(snapshot, BrokerSnapshot):
        return snapshot
    return BrokerSnapshot.from_dict(snapshot)
