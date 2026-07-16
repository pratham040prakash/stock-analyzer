"""Streamlit app — stock technical analysis with buy/sell signals."""

from __future__ import annotations

import streamlit as st

from analyzer.env_loader import load_app_env
from analyzer.india import indian_ticker_help
from analyzer.market_session import market_session_status
from analyzer.markets import MARKETS, is_india_market
from analyzer.app_mode import is_simple_cloud_mode
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured
from analyzer.varsity_knowledge import VARSITY_MODULE_URL
from ui.components.setup_wizard import render_setup_wizard_sidebar
from ui.components.data_health_panel import render_data_health_sidebar
from ui.components.autopilot import render_autopilot_sidebar
from ui.components.onboarding import render_sidebar_onboarding_button, render_start_here_onboarding
from ui.components.onboarding_tour import render_onboarding_tour
from ui.components.command_palette import render_command_palette, render_tab_quick_links
from ui.components.navigation_bar import render_app_navigation
from ui.components.theme_toggle import apply_theme_css, render_theme_toggle_sidebar
from ui.components.nse import render_nse_error_banner
from ui.components.broker_setup_wizard import ensure_broker_configured
from ui.components.broker_startup import run_broker_startup
from ui.components.kite_auth import process_oauth_callback_if_present
from ui.broker.oauth_log import startup_trace
from ui.components.telegram_subscribe import render_telegram_subscribe_sidebar
from ui.pages.beginner_risk import render_beginner_risk
from ui.pages.alpha_ai import render_alpha_ai
from ui.pages.backtest import render_backtest
from ui.pages.compare import render_compare
from ui.pages.daily_advisor import render_daily_advisor
from ui.pages.global_markets import render_global_markets
from ui.pages.intraday import render_intraday
from ui.pages.live_charts import render_live_charts_grid
from ui.pages.live_options_advisor import render_live_options_advisor
from ui.pages.market_pulse import render_market_pulse
from ui.pages.nse_options import render_nse_options
from ui.pages.penny_picks import render_penny_picks
from ui.pages.screener import render_screener
from ui.pages.single_stock import render_single_stock
from ui.pages.sip_goals import render_sip_goals
from ui.pages.track_record import render_track_record
from ui.pages.unified_home import render_unified_home
from ui.pages.varsity import render_varsity_guide
from ui.pages.watchlist import render_watchlist
from ui.pages.zerodha import render_zerodha
from ui.navigation import apply_pending_nav_tab, init_nav_state
from ui.theme import DISCLAIMER, MOBILE_CSS


def _hydrate_saved_portfolio() -> None:
    if st.session_state.get("zd_import"):
        _ensure_portfolio_streaming()
        return
    prof = portfolio_profile_key()
    saved = load_saved_portfolio(profile=prof)
    if saved and saved.holdings:
        st.session_state["zd_import"] = saved
        _ensure_portfolio_streaming()
        return

    if not st.session_state.get("_kite_portfolio_sync_attempted"):
        st.session_state["_kite_portfolio_sync_attempted"] = True
        from analyzer.portfolio_live import hydrate_portfolio_from_kite
        from analyzer.zerodha import load_env_credentials

        if load_env_credentials().get("access_token"):
            imp, err = hydrate_portfolio_from_kite(profile=prof)
            if imp and imp.holdings:
                st.session_state["zd_import"] = imp
                note = (
                    f"Auto-synced **{len(imp.holdings)}** holding(s) from Kite."
                    + (f" {imp.notes[0]}" if imp.notes else "")
                )
                st.session_state["_portfolio_auto_sync_msg"] = note
            elif err:
                st.session_state["_kite_sync_error"] = err

    _ensure_portfolio_streaming()


def _ensure_portfolio_streaming() -> None:
    from analyzer.portfolio_live import ensure_kite_stream_for_tracked

    ensure_kite_stream_for_tracked(
        st.session_state.get("zd_import"),
        profile=portfolio_profile_key(),
    )


def _run_background_task(task_name: str, fn) -> None:
    """Run a background hook; surface failures once per session."""
    try:
        fn()
    except Exception as exc:
        errors: list[str] = st.session_state.setdefault("_background_task_errors", [])
        msg = f"{task_name}: {exc}"
        if msg not in errors:
            errors.append(msg)


def _render_background_task_errors() -> None:
    errors = st.session_state.get("_background_task_errors") or []
    if not errors:
        return
    with st.expander("⚠️ Background task issues", expanded=True):
        for err in errors:
            st.warning(err)
        if st.button("Dismiss", key="dismiss_bg_errors"):
            st.session_state["_background_task_errors"] = []
            st.rerun()


def _maybe_validate_suggestions_eod() -> None:
    """Once per app session after close, score pending picks vs market."""
    if st.session_state.get("_suggestions_validated_session"):
        return
    session = market_session_status()
    if session.get("is_open"):
        return
    def _run() -> None:
        from analyzer.suggestion_journal import count_pending_validation
        from analyzer.eod_learning import run_eod_learning_cycle

        if count_pending_validation() <= 0:
            st.session_state["_suggestions_validated_session"] = True
            return
        run_eod_learning_cycle(send_telegram_alert=True)
        st.session_state["_suggestions_validated_session"] = True

    _run_background_task("EOD suggestion learning", _run)


def _maybe_score_watchlist_eod() -> None:
    """After close, auto-score today's full watchlist snapshot once per session."""
    if st.session_state.get("_watchlist_scored_session"):
        return
    session = market_session_status()
    if session.get("is_open"):
        return
    def _run() -> None:
        from analyzer.watchlist_history import prune_old_watchlist_data
        from analyzer.watchlist_learning import run_watchlist_learning_cycle

        run_watchlist_learning_cycle()
        prune_old_watchlist_data()
        try:
            from analyzer.options_watchlist_history import prune_old_options_data

            prune_old_options_data()
        except Exception as exc:
            raise RuntimeError(f"options history prune: {exc}") from exc
        try:
            from analyzer.mis_eod_summary import maybe_send_mis_eod_summary

            maybe_send_mis_eod_summary()
        except Exception as exc:
            raise RuntimeError(f"MIS EOD summary: {exc}") from exc
        st.session_state["_watchlist_scored_session"] = True

    _run_background_task("Watchlist EOD scoring", _run)


def _maybe_session_reminders() -> None:
    def _run() -> None:
        from analyzer.session_reminders import maybe_send_session_reminders

        maybe_send_session_reminders()

    _run_background_task("Session reminders", _run)


def _maybe_prep_morning_nag() -> None:
    def _run() -> None:
        from analyzer.prep_morning_nag import maybe_send_prep_morning_nag

        maybe_send_prep_morning_nag()

    _run_background_task("Prep morning nag", _run)


def _maybe_watchlist_live_alerts() -> None:
    def _run() -> None:
        from analyzer.watchlist_live_alerts import maybe_send_watchlist_live_alerts

        maybe_send_watchlist_live_alerts()

    _run_background_task("Watchlist live alerts", _run)


def _maybe_post_close_scan() -> None:
    def _run() -> None:
        from analyzer.post_close_scan_scheduler import maybe_run_post_close_scan

        maybe_run_post_close_scan()

    _run_background_task("Post-close Quick scan", _run)


def _maybe_autopilot_health_alert() -> None:
    def _run() -> None:
        from analyzer.autopilot_alerts import maybe_send_autopilot_failure_alert

        maybe_send_autopilot_failure_alert()

    _run_background_task("Autopilot health", _run)


def main() -> None:
    startup_trace(1, "app.main.enter")

    load_app_env()
    startup_trace(1, "load_app_env")

    st.set_page_config(page_title="Stock Analyzer", page_icon="📈", layout="wide")
    startup_trace(1, "st.set_page_config")

    # Section 9 — consume OAuth callback before nav, wizard, or startup skip.
    process_oauth_callback_if_present()

    apply_theme_css()
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)

    init_nav_state()
    apply_pending_nav_tab()
    startup_trace(2, "init_nav_state")

    if not ensure_broker_configured():
        startup_trace(2, "ensure_broker_configured", "BLOCKED — wizard shown")
        return
    startup_trace(2, "ensure_broker_configured", "OK")

    run_broker_startup()

    is_home = st.session_state.get("nav_tab") == "Home"
    startup_trace(13, "page_routing", f"nav_tab={st.session_state.get('nav_tab')}")

    st.title("📈 Stock Analyzer")

    with st.sidebar:
        st.header("Market")
        market = st.selectbox(
            "Exchange",
            options=list(MARKETS.keys()),
            format_func=lambda k: MARKETS[k]["label"],
            index=1,
        )
        period = st.selectbox("History period", options=["3mo", "6mo", "1y", "2y", "5y"], index=2)
        if not is_home:
            render_theme_toggle_sidebar()
            st.checkbox(
                "Compact navigation (mobile-friendly)",
                key="compact_nav",
                help="Collapsible nav groups instead of horizontal tabs",
            )
            if is_india_market(market):
                st.caption("Use **⌘ Jump** at the top for symbol, name, ISIN, or tab search.")
                with st.expander("Indian ticker help"):
                    st.markdown(indian_ticker_help())
                with st.expander("📚 Varsity TA (cached)"):
                    st.markdown(
                        f"[Full module]({VARSITY_MODULE_URL}) · 22 chapters stored in-app. "
                        "Open the **Varsity TA** tab for search and details."
                    )
                    if st.button("Open Varsity TA tab", key="go_varsity"):
                        from ui.navigation import request_nav_tab

                        request_nav_tab("Varsity TA")
            st.divider()
            render_setup_wizard_sidebar()
            render_data_health_sidebar()
            render_autopilot_sidebar()
            render_sidebar_onboarding_button()
            with st.expander("📱 Telegram & schedules (optional)", expanded=False):
                render_telegram_subscribe_sidebar()
                if telegram_configured():
                    if st.button("Send morning pick list", key="sidebar_morning_tg"):
                        from analyzer.suggestions_telegram import format_morning_suggestions_telegram

                        ok, msg = send_telegram_broadcast(
                            format_morning_suggestions_telegram(),
                            alert_type="morning",
                        )
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                st.caption(
                    "Telegram: morning list + EOD hit summary · configured in **⚙️ Setup**"
                )

    if is_home:
        st.session_state.setdefault("compact_nav", True)
        render_app_navigation()
        render_unified_home(market, period=period)
        return

    st.caption("Home · star stocks · track results")
    _ensure_portfolio_streaming()
    _maybe_prep_morning_nag()
    _maybe_session_reminders()
    _maybe_watchlist_live_alerts()
    _maybe_validate_suggestions_eod()
    _maybe_score_watchlist_eod()
    _maybe_post_close_scan()
    _maybe_autopilot_health_alert()

    st.info(DISCLAIMER)
    render_nse_error_banner()
    _render_background_task_errors()

    force_onboard = st.session_state.pop("_onboarding_force_show", False)
    hidden_session = st.session_state.get("_onboarding_hidden_session", False)
    if force_onboard or not hidden_session:
        render_start_here_onboarding(market, force_show=force_onboard)

    render_command_palette(market=market)
    render_tab_quick_links()
    render_onboarding_tour(force=force_onboard)

    if is_simple_cloud_mode():
        st.info(
            "**Simple nav mode** — only Suggestions, Track Record, and Alpha AI are shown. "
            "Remove `SIMPLE_CLOUD_MODE` from secrets (or set `0`) for the full menu."
        )
    else:
        try:
            from analyzer.zerodha import kite_runs_on_cloud

            if kite_runs_on_cloud():
                st.caption(
                    "Hosted on Streamlit Cloud — **Kite login & MIS autopilot** need a local run: "
                    "`streamlit run app.py` on your Mac."
                )
        except Exception:
            pass

    selected = render_app_navigation()

    if selected == "Risk & Goals":
        render_beginner_risk(market, period)
    elif selected == "SIP & Goals":
        render_sip_goals(market, period)
    elif selected == "Market Pulse":
        render_market_pulse(market, period)
    elif selected == "Daily Advisor":
        render_daily_advisor(period)
    elif selected == "Global Markets":
        render_global_markets()
    elif selected == "Single Stock":
        render_single_stock(market, period)
    elif selected == "Alpha AI":
        render_alpha_ai(market, period=period)
    elif selected == "Compare":
        render_compare(market, period)
    elif selected == "Home":
        render_unified_home(market, period=period)
    elif selected == "Suggestions":
        render_intraday(market, period=period)
    elif selected == "Live Charts":
        render_live_charts_grid(market)
    elif selected == "Live Options Coach":
        render_live_options_advisor(market, period=period)
    elif selected == "NSE Options":
        render_nse_options(market)
    elif selected == "Batch Scanner":
        render_watchlist(market, period)
    elif selected == "Screener":
        render_screener(market, period)
    elif selected == "Penny Picks":
        render_penny_picks(market, period)
    elif selected == "My Portfolio":
        render_zerodha(period)
    elif selected == "Backtest":
        render_backtest(market, period)
    elif selected == "Track Record":
        render_track_record()
    elif selected == "Varsity TA":
        render_varsity_guide()
    else:
        st.warning(f"Unknown page **{selected}** — pick **Home** from the nav bar above.")
        render_unified_home(market, period=period)


if __name__ == "__main__":
    main()
