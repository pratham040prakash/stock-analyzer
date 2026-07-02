"""UI — log intraday trades and show today's journal."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.intraday_journal import (
    count_trades_on_date,
    fetch_intraday_trades,
    log_intraday_trade,
)
from analyzer.market_session import market_session_status


def render_log_trade_panel(
    symbol: str,
    action: str,
    *,
    entry: float | None = None,
    stop_loss: float | None = None,
    target: float | None = None,
    price_at_log: float | None = None,
    suggested_shares: int | None = None,
    max_trades: int = 3,
) -> None:
    """One-click trade log with entry/stop/target pre-filled from the plan."""
    if action in ("WAIT", "FLAT", "NO TRADE"):
        return

    today_count = count_trades_on_date()
    with st.expander(
        f"📝 Log this trade ({today_count}/{max_trades} logged today)",
        expanded=st.session_state.pop("intraday_focus_journal", False),
    ):
        st.caption("Saves entry · stop · target for **Track Record** review tonight.")
        if today_count >= max_trades:
            st.warning(
                f"You planned **{max_trades}** trades today — at limit. "
                "Only log if this replaces a cancelled trade."
            )

        c1, c2 = st.columns(2)
        with c1:
            shares = st.number_input(
                "Shares (optional)",
                min_value=0,
                value=int(suggested_shares or 0),
                step=1,
                key=f"log_shares_{symbol}",
            )
        with c2:
            notes = st.text_input(
                "Note (optional)",
                placeholder="e.g. OR breakout, half booked at target",
                key=f"log_notes_{symbol}",
            )

        e1, e2, e3 = st.columns(3)
        e1.caption(f"Entry **₹{entry:,.2f}**" if entry else "Entry —")
        e2.caption(f"Stop **₹{stop_loss:,.2f}**" if stop_loss else "Stop —")
        e3.caption(f"Target **₹{target:,.2f}**" if target else "Target —")

        if st.button(f"Log {action} {symbol}", type="primary", key=f"log_trade_{symbol}"):
            log_intraday_trade(
                symbol=symbol,
                action=action,
                entry=entry,
                stop_loss=stop_loss,
                target=target,
                price_at_log=price_at_log,
                shares=shares if shares > 0 else None,
                notes=notes,
            )
            st.success(f"Logged **{action} {symbol}** — review in Track Record tonight.")
            st.rerun()


def render_todays_trade_journal(*, max_trades: int = 3) -> None:
    """Table of trades logged today on the Intraday tab."""
    today = market_session_status().get("date", "")
    trades = fetch_intraday_trades(trade_date=today, limit=20)
    if not trades:
        st.caption("No trades logged today. Use **Log this trade** on a chart after you enter.")
        return

    st.markdown(f"#### Today's trade log ({len(trades)}/{max_trades} slots)")
    rows = []
    for t in trades:
        rows.append({
            "Time": t.created_at.split(" ")[-2] if " " in t.created_at else t.created_at,
            "Symbol": t.symbol,
            "Action": t.action,
            "Entry": f"₹{t.entry:,.2f}" if t.entry else "—",
            "Stop": f"₹{t.stop_loss:,.2f}" if t.stop_loss else "—",
            "Target": f"₹{t.target:,.2f}" if t.target else "—",
            "Shares": t.shares or "—",
            "Note": t.notes[:40] or "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
