"""Focused home: nightly suggestions + target hit tracking."""

from __future__ import annotations

import streamlit as st

from analyzer.market_session import market_session_status
from analyzer.watchlist_history import (
    MIN_RETENTION_DAYS,
    build_watchlist_success_report,
    can_score_trade_date,
    session_target_date,
)
from analyzer.watchlist_learning import run_watchlist_learning_cycle
from analyzer.options_watchlist_history import score_options_daily_watchlist
from ui.components.intraday_watchlist import render_intraday_watchlist_block
from ui.components.watchlist_stats import (
    render_all_suggested_picks_table,
    render_todays_track_record,
    render_watchlist_success_banner,
)


def render_suggestions_hero() -> None:
    session = market_session_status()
    st.subheader("Suggestions — did they hit target?")
    st.markdown(
        "1. **After market close** → **Quick scan** (saves top 5 with Entry · Stop · Target)  \n"
        "2. **Next session** → trade from the list (star your top 2 if you want)  \n"
        "3. **After 3:30 PM IST** → app scores **Hit target?** vs the day's high/low"
    )
    st.caption(f"Session: **{session['status']}** · {session.get('time_ist', '')}")


def render_suggestions_core(
    market: str,
    *,
    period: str = "1y",
    max_trades: int = 3,
    days: int = 7,
) -> None:
    """Primary loop: results summary → tonight's scan → history."""
    days = max(days, MIN_RETENTION_DAYS)
    report = build_watchlist_success_report(days)

    if report.total_picks > 0:
        render_watchlist_success_banner(days=days)
    else:
        st.info(
            "No scored suggestions yet. Run **Quick scan** below after today's close — "
            "results appear here tomorrow evening."
        )

    render_todays_track_record(market=market)

    st.divider()
    st.markdown("#### Tonight's stock suggestions")
    render_intraday_watchlist_block(
        market,
        period=period,
        max_concurrent_trades=max_trades,
        as_top_section=True,
    )

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("Score today's picks", key="sugg_score_today", use_container_width=True):
            with st.spinner("Scoring vs session high/low…"):
                run_watchlist_learning_cycle(market=market)
                try:
                    score_options_daily_watchlist(trade_date=session_target_date())
                except Exception:
                    pass
            st.rerun()
    with c1:
        td = session_target_date()
        if not can_score_trade_date(td):
            st.caption(f"Scoring for **{td}** unlocks after **3:30 PM IST**.")
        else:
            st.caption("Tap **Score today's picks** if results still show Pending.")

    with st.expander(f"All suggestions — last {days} days", expanded=report.total_picks > 0):
        render_all_suggested_picks_table(days=days, market=market)
