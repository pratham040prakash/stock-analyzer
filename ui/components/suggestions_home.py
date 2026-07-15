"""Suggestions home — nightly picks + live session."""

from __future__ import annotations

import streamlit as st

from analyzer.app_mode import is_simple_cloud_mode
from analyzer.autopilot_status import is_macos
from analyzer.market_session import market_session_status
from analyzer.session_phase import phase_banner_text, suggestions_ui_phase
from analyzer.suggestions_export import (
    build_combined_suggestions_csv,
    build_options_csv,
    build_suggestions_csv,
)
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
from ui.components.autopilot import render_autopilot_home_readonly, render_autopilot_loop_strip
from ui.components.data_mode_banner import render_data_mode_banner
from ui.navigation import request_nav_tab
from ui.components.watchlist_stats import (
    render_all_suggested_picks_table,
    render_selected_vs_all_banner,
    render_todays_track_record,
)


def render_suggestions_hero() -> None:
    session = market_session_status()
    st.subheader("Stock picks")
    st.caption(
        f"**{session['status']}** · star picks on **Home** · full list below · "
        "score after **3:30 PM** on Track Record"
    )


def render_weekly_hero_metric(*, days: int = 7) -> None:
    """Compact link — full analytics live on Track Record tab."""
    days = max(days, MIN_RETENTION_DAYS)
    eq = build_watchlist_success_report(days)
    from analyzer.options_watchlist_history import build_options_success_report

    opt = build_options_success_report(days)
    if eq.total_picks == 0 and opt.total_picks == 0:
        return
    eq_wr = f"{eq.win_rate_pct:.0f}%" if eq.win_rate_pct is not None else "—"
    opt_wr = f"{opt.win_rate_pct:.0f}%" if opt.win_rate_pct is not None else "—"
    c1, c2 = st.columns([4, 1])
    with c1:
        st.caption(
            f"Last {days}d — stocks **{eq.target_hits}**T · **{eq.stop_hits}**S · win **{eq_wr}** · "
            f"options **{opt.target_hits}**T · **{opt.stop_hits}**S · win **{opt_wr}** "
            f"— details on **Track Record**"
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
                    n = score_options_daily_watchlist(trade_date=session_target_date())
                    if n == 0:
                        st.caption("Options: no new rows scored (may need Kite NFO after close).")
                except Exception as exc:
                    st.warning(f"Options scoring failed: {exc}")
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
    """Full watchlist + scoring — daily guide lives on Home tab."""
    days = max(days, MIN_RETENTION_DAYS)
    report = build_watchlist_success_report(days)
    phase = suggestions_ui_phase()
    banner = phase_banner_text(phase)
    if banner:
        st.info(banner)

    st.caption("Daily guide and settings are on the **Home** tab.")
    render_data_mode_banner(key_prefix="sugg_data")

    if is_macos() and not is_simple_cloud_mode():
        render_autopilot_loop_strip()
    elif not is_macos() or is_simple_cloud_mode():
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
        opt_csv = build_options_csv(days=days, market=market)
        combined_csv = build_combined_suggestions_csv(days=days, market=market)
        if csv_data.strip().count("\n") > 0:
            st.download_button(
                "Export CSV — stocks",
                data=csv_data,
                file_name=f"suggestions_{days}d.csv",
                mime="text/csv",
                key="sugg_export_csv",
                use_container_width=True,
            )
        if opt_csv.strip().count("\n") > 0:
            st.download_button(
                "Export CSV — options",
                data=opt_csv,
                file_name=f"options_{days}d.csv",
                mime="text/csv",
                key="sugg_export_opt_csv",
                use_container_width=True,
            )
        if combined_csv.strip().count("\n") > 0:
            st.download_button(
                "Export CSV — combined",
                data=combined_csv,
                file_name=f"mis_combined_{days}d.csv",
                mime="text/csv",
                key="sugg_export_combined_csv",
                use_container_width=True,
            )
