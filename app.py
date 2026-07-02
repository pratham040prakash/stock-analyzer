"""Streamlit app — stock technical analysis with buy/sell signals."""

from __future__ import annotations

import streamlit as st

from analyzer.env_loader import load_app_env
from analyzer.india import indian_ticker_help, search_indian_stocks
from analyzer.kite_stream import start_kite_ticker_on_app_start, ws_subscription_status
from analyzer.market_session import market_session_status
from analyzer.markets import MARKETS, is_india_market
from analyzer.morning_briefing import build_morning_briefing
from analyzer.providers import data_source_status
from analyzer.telegram_notify import format_morning_telegram, send_telegram_broadcast, telegram_configured
from analyzer.varsity_knowledge import VARSITY_MODULE_URL
from ui.components.nse import render_nse_error_banner
from ui.components.telegram_subscribe import render_telegram_subscribe_sidebar
from ui.pages.backtest import render_backtest
from ui.pages.daily_advisor import render_daily_advisor
from ui.pages.global_markets import render_global_markets
from ui.pages.intraday import render_intraday
from ui.pages.live_charts import render_live_charts_grid
from ui.pages.market_pulse import render_market_pulse
from ui.pages.nse_options import render_nse_options
from ui.pages.single_stock import render_single_stock
from ui.pages.track_record import render_track_record
from ui.pages.varsity import render_varsity_guide
from ui.pages.watchlist import render_watchlist
from ui.pages.zerodha import render_zerodha
from ui.theme import DISCLAIMER, MOBILE_CSS, NAV_TABS


def _maybe_validate_suggestions_eod() -> None:
    """Once per app session after close, score pending picks vs market."""
    if st.session_state.get("_suggestions_validated_session"):
        return
    session = market_session_status()
    if session.get("market_open"):
        return
    try:
        from analyzer.suggestion_journal import count_pending_validation
        from analyzer.eod_learning import run_eod_learning_cycle

        if count_pending_validation() <= 0:
            st.session_state["_suggestions_validated_session"] = True
            return
        run_eod_learning_cycle(send_telegram_alert=True)
        st.session_state["_suggestions_validated_session"] = True
    except Exception:
        pass


def main() -> None:
    load_app_env()
    st.set_page_config(page_title="Stock Analyzer", page_icon="📈", layout="wide")
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    st.title("📈 Stock Analyzer")
    st.caption("Multi-indicator technical analysis · Watchlist scanner · Backtesting")

    start_kite_ticker_on_app_start()
    _maybe_validate_suggestions_eod()

    with st.sidebar:
        st.header("Market")
        market = st.selectbox(
            "Exchange",
            options=list(MARKETS.keys()),
            format_func=lambda k: MARKETS[k]["label"],
            index=1,
        )
        period = st.selectbox("History period", options=["3mo", "6mo", "1y", "2y", "5y"], index=2)

        if is_india_market(market):
            st.divider()
            st.subheader("Find Indian Stock")
            search_q = st.text_input("Search by name", placeholder="e.g. Reliance, TCS, HDFC Bank")
            if search_q:
                results = search_indian_stocks(search_q, max_results=8)
                if results:
                    for r in results:
                        sym_short = r["symbol"].replace(".NS", "").replace(".BO", "")
                        if st.button(f"{r['symbol']} — {r['name'][:28]}", key=f"sr_{r['symbol']}"):
                            st.session_state["single_ticker"] = sym_short
                            st.session_state["bt_ticker"] = sym_short
                            st.session_state["intraday_ticker"] = sym_short
                            st.session_state["nav_tab"] = "Single Stock"
                            st.rerun()
                else:
                    st.caption("No NSE/BSE results. Try a different name.")

            with st.expander("Indian ticker help"):
                st.markdown(indian_ticker_help())

            with st.expander("📚 Varsity TA (cached)"):
                st.markdown(
                    f"[Full module]({VARSITY_MODULE_URL}) · 22 chapters stored in-app. "
                    "Open the **Varsity TA** tab for search and details."
                )
                if st.button("Open Varsity TA tab", key="go_varsity"):
                    st.session_state["nav_tab"] = "Varsity TA"
                    st.rerun()

        st.divider()
        render_telegram_subscribe_sidebar()
        if telegram_configured():
            if st.button("Send morning briefing now", key="sidebar_morning_tg"):
                with st.spinner("Building morning briefing..."):
                    mb = build_morning_briefing(period=period)
                    ok, msg = send_telegram_broadcast(
                        format_morning_telegram(mb),
                        alert_type="morning",
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        st.caption("Schedule: `bash scripts/install_morning_schedule.sh` (8:30 AM)")

        if is_india_market(market):
            st.divider()
            st.subheader("Data feeds")
            ds = data_source_status()
            if ds["kite_configured"]:
                ws = ws_subscription_status()
                if ws["nifty50_mode"]:
                    st.success(
                        f"Live: **{ds['primary_intraday']}** · "
                        f"WebSocket **Nifty 50** ({ws['subscribed_tokens']} tokens)"
                    )
                else:
                    st.success(f"Live: **{ds['primary_intraday']}**")
                    if not ws["market_open"]:
                        st.caption("WebSocket: Nifty index only (market closed)")
            else:
                st.caption(ds["upgrade_hint"])

    st.info(DISCLAIMER)
    render_nse_error_banner()

    if "nav_tab" not in st.session_state:
        st.session_state["nav_tab"] = NAV_TABS[0]

    selected = st.radio(
        "Section",
        NAV_TABS,
        horizontal=True,
        label_visibility="collapsed",
        key="nav_tab",
    )

    if selected == "Market Pulse":
        render_market_pulse(market, period)
    elif selected == "Daily Advisor":
        render_daily_advisor(period)
    elif selected == "Global Markets":
        render_global_markets()
    elif selected == "Single Stock":
        render_single_stock(market, period)
    elif selected == "Intraday":
        render_intraday(market)
    elif selected == "Live Charts":
        render_live_charts_grid(market)
    elif selected == "NSE Options":
        render_nse_options(market)
    elif selected == "Watchlist":
        render_watchlist(market, period)
    elif selected == "Zerodha Portfolio":
        render_zerodha(period)
    elif selected == "Backtest":
        render_backtest(market, period)
    elif selected == "Track Record":
        render_track_record()
    elif selected == "Varsity TA":
        render_varsity_guide()


if __name__ == "__main__":
    main()
