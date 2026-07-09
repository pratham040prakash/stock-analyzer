"""Suggestions home — nightly picks + live session."""

from __future__ import annotations

import streamlit as st

from analyzer.app_mode import is_simple_cloud_mode
from analyzer.autopilot_status import is_macos
from analyzer.market_session import market_session_status
from analyzer.session_phase import phase_banner_text, suggestions_ui_phase
from analyzer.suggestions_export import build_suggestions_csv
from analyzer.watchlist_history import (
    MIN_RETENTION_DAYS,
    build_watchlist_success_report,
    can_score_trade_date,
    session_target_date,
)
from analyzer.watchlist_learning import run_watchlist_learning_cycle
from analyzer.options_watchlist_history import score_options_daily_watchlist
from ui.components.intraday_watchlist import render_intraday_watchlist_block
from ui.components.morning_cockpit import render_morning_cockpit
from ui.components.autopilot import render_autopilot_home_readonly
from ui.components.data_mode_banner import render_data_mode_banner
from ui.components.live_session_strip import render_live_session_strip
from ui.components.daily_cheat_sheet import render_daily_cheat_sheet
from ui.navigation import request_nav_tab
from ui.components.watchlist_stats import (
    render_all_suggested_picks_table,
    render_selected_vs_all_banner,
    render_todays_track_record,
)


def render_suggestions_hero() -> None:
    session = market_session_status()
    st.subheader("Suggestions — did they hit target?")
    st.markdown(
        "1. **After market close** → **Quick scan** (saves top 5 with Entry · Stop · Target)  \n"
        "2. **Next session** → trade from the list (**star your top 2** to compare vs full top 5)  \n"
        "3. **After 3:30 PM IST** → app scores **Hit target?** vs the day's high/low"
    )
    st.caption(f"Session: **{session['status']}** · {session.get('time_ist', '')}")
    if is_simple_cloud_mode():
        st.caption(
            "Cloud view — enable **🤖 Autopilot** on your Mac for hands-free scan + scoring."
        )
    else:
        st.caption("Sidebar → **⚙️ Setup** + **🤖 Autopilot** for zero-touch daily loop.")


def render_weekly_hero_metric(*, days: int = 7) -> None:
    """Compact link — full analytics live on Track Record tab."""
    days = max(days, MIN_RETENTION_DAYS)
    report = build_watchlist_success_report(days)
    if report.total_picks == 0:
        return
    wr = f"{report.win_rate_pct:.0f}%" if report.win_rate_pct is not None else "—"
    c1, c2 = st.columns([4, 1])
    with c1:
        st.caption(
            f"Last {days}d: **{report.target_hits}** targets · **{report.stop_hits}** stops "
            f"· win **{wr}** — details on **Track Record**"
        )
    with c2:
        if st.button("Track Record →", key="sugg_go_track_record", use_container_width=True):
            request_nav_tab("Track Record")
            st.rerun()


def _render_score_button(market: str) -> None:
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


def render_suggestions_core(
    market: str,
    *,
    period: str = "1y",
    max_trades: int = 3,
    days: int = 7,
) -> None:
    """Session-aware layout: live / post-close / pre-market."""
    days = max(days, MIN_RETENTION_DAYS)
    report = build_watchlist_success_report(days)
    phase = suggestions_ui_phase()
    banner = phase_banner_text(phase)
    if banner:
        st.info(banner)

    render_data_mode_banner(key_prefix="sugg_data")
    render_live_session_strip(market=market)
    render_daily_cheat_sheet(key_prefix="sugg_cheat")

    if not is_macos() or is_simple_cloud_mode():
        render_autopilot_home_readonly()

    render_weekly_hero_metric(days=days)
    render_selected_vs_all_banner(days=days)

    if phase == "live":
        render_morning_cockpit(market, key_prefix="sugg_cockpit")
        st.divider()
        render_todays_track_record(market=market)
        st.divider()
        st.markdown("#### Tonight's stock suggestions")
        render_intraday_watchlist_block(
            market, period=period, max_concurrent_trades=max_trades, as_top_section=True,
        )
        _render_score_button(market)

    elif phase == "post_close":
        render_todays_track_record(market=market)
        _render_score_button(market)
        st.divider()
        st.markdown("#### Quick scan for tomorrow")
        render_intraday_watchlist_block(
            market, period=period, max_concurrent_trades=max_trades, as_top_section=True,
        )

    else:
        if report.total_picks == 0:
            st.info("Run **Quick scan** after close — or enable **Autopilot** in the sidebar.")
        st.markdown("#### Today's stock suggestions")
        render_intraday_watchlist_block(
            market, period=period, max_concurrent_trades=max_trades, as_top_section=True,
        )
        st.divider()
        render_todays_track_record(market=market)
        if phase != "weekend":
            render_morning_cockpit(market, key_prefix="sugg_cockpit")
        _render_score_button(market)

    with st.expander(f"All suggestions — last {days} days", expanded=report.total_picks > 0):
        render_all_suggested_picks_table(days=days, market=market)
        csv_data = build_suggestions_csv(days=days, market=market)
        if csv_data.strip().count("\n") > 0:
            st.download_button(
                "Export CSV (suggestions + hit/miss)",
                data=csv_data,
                file_name=f"suggestions_{days}d.csv",
                mime="text/csv",
                key="sugg_export_csv",
                use_container_width=True,
            )
