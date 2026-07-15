"""Unified nightly prep — equity top-5, options ★, stars, checklist in one view."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.intraday_pulse_source import DEFAULT_INTRADAY_PULSE_PERIOD
from analyzer.market_session import market_session_status
from analyzer.options_trade_selection import (
    load_selected_option,
    option_selection_status_line,
)
from analyzer.morning_options_rescan import was_morning_options_rescan_sent
from analyzer.options_watchlist_history import fetch_options_snapshots_for_date
from analyzer.prep_status import prep_status_for, sync_selection_prep_step
from analyzer.trade_selection import load_selected_symbols, selection_status_line
from analyzer.watchlist_history import session_target_date
from analyzer.watchlist_pins import load_pinned_plans
from ui.components.options_expiry_watchlist import render_options_expiry_watchlist_block
from ui.components.prep_all import render_prep_all_bar


def _render_equity_top5_summary() -> None:
    pins = load_pinned_plans()
    stars = {s.upper() for s in load_selected_symbols()}
    st.markdown("##### 📈 Equity top 5")
    if not pins:
        st.caption("Run **Prep all** or **Quick scan** after close to save tomorrow's list.")
        return
    rows = []
    for p in pins[:5]:
        rows.append({
            "Rank": p.rank,
            "Stock": p.symbol,
            "Entry": f"₹{p.entry:,.2f}",
            "Stop": f"₹{p.stop_loss:,.2f}",
            "Target": f"₹{p.target:,.2f}",
            "Star": "⭐" if p.symbol.upper() in stars else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(selection_status_line())


def _render_options_star_summary() -> None:
    td = session_target_date()
    snaps = fetch_options_snapshots_for_date(td)
    starred = load_selected_option(td)
    st.markdown("##### 📅 Options ★ (Nifty / Bank Nifty)")
    if not snaps:
        st.caption("Run **Prep all** — saves CE/PE rows for tomorrow. Re-scan at **9:46 AM** after OR.")
        return
    recs = [s for s in snaps if s.recommended]
    if recs:
        rows = []
        for s in recs[:6]:
            is_star = (
                starred
                and starred["fno_symbol"] == s.fno_symbol
                and starred["option_type"] == s.option_type
                and abs(float(starred["strike"]) - s.strike) < 0.01
            )
            rows.append({
                "Index": s.fno_symbol,
                "Leg": f"{s.option_type} {s.strike:g}",
                "Prem": f"₹{s.entry:,.2f}",
                "★": "⭐" if is_star else "☆",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("Snapshot saved — no ★ recommended legs yet (re-scan after 9:45).")
    st.caption(option_selection_status_line(td))
    if was_morning_options_rescan_sent(td):
        st.success("9:46 AM **options re-scan** done — CE/PE ★ reflect opening range.")
    elif snaps:
        st.warning(
            "Nightly snapshot saved — **9:46 AM re-scan** still pending (tap **Re-scan after OR**)."
        )


def render_unified_prep_screen(market: str, *, period: str = DEFAULT_INTRADAY_PULSE_PERIOD) -> None:
    """Single prep hub: checklist, stars, equity + options picks, full options block."""
    sync_selection_prep_step(session_target_date())
    session = market_session_status()

    st.markdown("### 📋 Unified prep — equity + options")
    st.caption(
        f"Session **{session.get('status', '—')}** · prep for **{session_target_date()}** · "
        "one screen for stocks, CE/PE, stars, and checklist."
    )

    render_prep_all_bar(market, period=period)

    c1, c2 = st.columns(2)
    with c1:
        _render_equity_top5_summary()
    with c2:
        _render_options_star_summary()

    status = prep_status_for()
    if not status.get("selection"):
        st.warning("Star **2 stocks** in the watchlist below and **1 option** leg before bed.")
    elif not status.get("options"):
        st.info("Equity stars set — run **Prep all** or refresh options CE/PE below.")

    st.divider()
    render_options_expiry_watchlist_block(market, period=period)
