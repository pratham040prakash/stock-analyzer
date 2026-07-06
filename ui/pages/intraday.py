"""Intraday tab — live candles, stories, and trade suggestions."""

from __future__ import annotations

from datetime import timedelta

import streamlit as st

from analyzer.candle_narrative import analyze_live_chart
from analyzer.intraday_chart import intraday_chart
from analyzer.intraday_data import INTERVAL_OPTIONS, fetch_intraday
from analyzer.market_session import market_session_status
from analyzer.intraday_prefs import load_intraday_prefs, save_intraday_prefs, session_to_prefs
from analyzer.intraday_signals import add_intraday_indicators
from analyzer.intraday_beginner_tips import (
    DEFAULT_INTRADAY_ALLOCATION_PCT,
    DEFAULT_MAX_CONCURRENT_TRADES,
    penny_stock_intraday_warning,
    session_timing_advice,
)
from analyzer.intraday_trade_plan import DEFAULT_MAX_RISK_PCT, discipline_intro
from analyzer.intraday_stock_picker import investopedia_screen_summary
from analyzer.nse_options import enrich_with_nse_chain
from analyzer.varsity_knowledge import format_signal_context
from ui.components.intraday import render_candle_stories, render_live_verdict
from ui.components.morning_cockpit import render_morning_cockpit
from ui.components.intraday_tips import (
    render_capital_budget_panel,
    render_daily_mis_checklist,
    render_session_timing_banner,
    render_ten_tips_expander,
)
from ui.components.options_expiry_watchlist import render_options_expiry_watchlist_block
from ui.components.prep_all import render_prep_all_bar
from ui.components.small_trader_intraday import render_small_trader_portfolio_intraday
from ui.components.suggestions_home import render_suggestions_core, render_suggestions_hero
from ui.components.watchlist_stats import (
    render_learning_honesty_banner,
    render_options_learning_panel,
    render_watchlist_learning_panel,
)
from ui.theme import MOBILE_CSS, SIGNAL_ICONS


def _hydrate_intraday_prefs() -> None:
    """Load saved capital settings into session on first visit."""
    if st.session_state.get("_intraday_prefs_loaded"):
        return
    prefs = load_intraday_prefs()
    for key, value in {
        "intraday_capital": int(prefs.capital),
        "intraday_allocation_pct": int(prefs.allocation_pct),
        "intraday_max_risk_pct": float(prefs.max_risk_pct),
        "intraday_max_trades": int(prefs.max_trades),
    }.items():
        st.session_state.setdefault(key, value)
    st.session_state["_intraday_prefs_loaded"] = True


def _persist_intraday_prefs() -> None:
    save_intraday_prefs(
        session_to_prefs(
            float(st.session_state.get("intraday_capital", 50_000)),
            float(st.session_state.get("intraday_allocation_pct", DEFAULT_INTRADAY_ALLOCATION_PCT)),
            float(st.session_state.get("intraday_max_risk_pct", DEFAULT_MAX_RISK_PCT)),
            int(st.session_state.get("intraday_max_trades", DEFAULT_MAX_CONCURRENT_TRADES)),
        )
    )


def display_intraday_live(ticker: str, interval_key: str, market: str) -> None:
    interval = INTERVAL_OPTIONS[interval_key]
    session = market_session_status()
    account_inr = float(st.session_state.get("intraday_allocated_pool", 25_000))
    max_risk_pct = float(st.session_state.get("intraday_max_risk_pct", DEFAULT_MAX_RISK_PCT))
    max_trades = int(st.session_state.get("intraday_max_trades", DEFAULT_MAX_CONCURRENT_TRADES))
    timing = session_timing_advice()

    try:
        df, meta = fetch_intraday(ticker, interval=interval, market=market)
    except Exception as exc:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("NSE Session", session["status"])
        c2.metric("IST Time", session["time_ist"])
        c3.caption("Data fetch failed")
        c4.caption("Auto-refresh: 30s")
        st.error(str(exc))
        if not session["is_open"]:
            st.info(
                "Indian market is **closed**. Charts show the **last trading session**. "
                f"**{session.get('next_session', '')}** — use **Market Pulse** for swing/long "
                "suggestions and **Global Markets** for overnight bias."
            )
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NSE Session", session["status"])
    c2.metric("IST Time", session["time_ist"])
    lag = f" — {meta['lag_note']}" if meta.get("lag_note") else ""
    c3.caption(f"Data: **{meta.get('source', 'Yahoo')}**{lag}")
    c4.caption("Auto-refresh: 30s")

    try:
        verdict = analyze_live_chart(df, ticker, interval)
        if verdict.options:
            chain, picks, err = enrich_with_nse_chain(verdict.options.action, ticker)
            verdict.options.nse_chain = chain
            verdict.options.nse_picks = picks
            verdict.options.nse_error = err
        analysis = verdict.intraday
        df_ind = add_intraday_indicators(df)

        st.caption(
            f"**{meta['symbol']}** · {meta['session_date']} · {meta['bars']} candles · "
            f"{interval_key} · source **{meta.get('source', 'Yahoo')}**"
        )

        render_live_verdict(
            verdict,
            account_inr=account_inr,
            max_risk_pct=max_risk_pct,
            max_trades=max_trades,
        )
        penny_warn = penny_stock_intraday_warning(analysis.last_price)
        if penny_warn:
            st.warning(penny_warn)
        if not timing.allow_new_entries and verdict.action in ("BUY", "STRONG BUY", "SELL", "STRONG SELL"):
            st.warning(
                f"**Session timing:** {timing.headline} — prefer WAIT for new entries right now."
            )

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("LTP", f"₹{analysis.last_price:,.2f}")
        m2.metric("VWAP", f"₹{analysis.vwap:,.2f}")
        m3.metric("OR High", f"₹{analysis.opening_range_high:,.2f}")
        m4.metric("OR Low", f"₹{analysis.opening_range_low:,.2f}")
        m5.metric("RSI (7)", f"{analysis.rsi:.0f}" if analysis.rsi else "—")

        st.plotly_chart(intraday_chart(df_ind, analysis), use_container_width=True)

        render_candle_stories(verdict)

        st.subheader("Intraday signals")
        for sig in analysis.signals:
            icon = SIGNAL_ICONS.get(sig.bias, "⚪")
            st.markdown(f"{icon} **{sig.name}** — {sig.detail}")
            st.caption(format_signal_context(sig.name))

        st.caption(analysis.note if analysis else "")
    except Exception as exc:
        st.error(str(exc))
        if not session["is_open"]:
            st.info(
                "Indian market is **closed**. Charts show the **last trading session**. "
                f"**{session.get('next_session', '')}** — use **Market Pulse** for swing/long "
                "suggestions and **Global Markets** for overnight bias. "
                "Auto-refresh every **30 sec** picks up any new candle data."
            )


@st.fragment(run_every=timedelta(seconds=30))
def intraday_live_panel(ticker: str, interval_key: str, market: str) -> None:
    """Auto-refreshes every 30s when Intraday tab is open."""
    display_intraday_live(ticker, interval_key, market)


@st.fragment(run_every=timedelta(seconds=30))
def small_trader_portfolio_panel(market: str, interval_key: str) -> None:
    """Auto-refresh portfolio intraday strip every 30s."""
    render_small_trader_portfolio_intraday(market, interval_key)


def render_intraday(market: str, *, period: str = "1y") -> None:
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    _hydrate_intraday_prefs()
    max_trades = int(st.session_state.get("intraday_max_trades", DEFAULT_MAX_CONCURRENT_TRADES))

    render_suggestions_hero()
    render_suggestions_core(market, period=period, max_trades=max_trades)

    with st.expander("⚙️ Evening prep, capital & morning checklist", expanded=False):
        timing = render_session_timing_banner()
        render_morning_cockpit(market)
        render_daily_mis_checklist(timing)
        render_prep_all_bar(market, period=period)
        capital_focus = st.session_state.pop("intraday_focus_capital", False)
        with st.expander("Capital & risk settings", expanded=capital_focus):
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.number_input(
                    "Total capital (₹)",
                    min_value=5_000,
                    max_value=10_000_000,
                    step=5_000,
                    key="intraday_capital",
                    on_change=_persist_intraday_prefs,
                )
            with r2:
                st.slider(
                    "MIS allocation (%)",
                    min_value=10,
                    max_value=80,
                    step=5,
                    key="intraday_allocation_pct",
                    on_change=_persist_intraday_prefs,
                )
            with r3:
                st.slider(
                    "Max risk per trade (%)",
                    min_value=0.5,
                    max_value=3.0,
                    step=0.25,
                    key="intraday_max_risk_pct",
                    on_change=_persist_intraday_prefs,
                )
            with r4:
                _mt_opts = [1, 2, 3]
                _mt_default = int(st.session_state.get("intraday_max_trades", DEFAULT_MAX_CONCURRENT_TRADES))
                st.selectbox(
                    "Max trades today",
                    options=_mt_opts,
                    index=_mt_opts.index(_mt_default) if _mt_default in _mt_opts else 1,
                    key="intraday_max_trades",
                    on_change=_persist_intraday_prefs,
                )
            allocated = render_capital_budget_panel(
                float(st.session_state["intraday_capital"]),
                float(st.session_state["intraday_allocation_pct"]),
                float(st.session_state["intraday_max_risk_pct"]),
                int(st.session_state["intraday_max_trades"]),
            )
            st.session_state["intraday_allocated_pool"] = allocated

    with st.expander("📅 Options CE/PE — Nifty & Bank Nifty (advanced)", expanded=False):
        st.caption("Optional — equity suggestions above work without Kite or NSE options.")
        render_options_expiry_watchlist_block(market, period=period)

    with st.expander("🧠 Auto-learning & strategy tuning", expanded=False):
        render_learning_honesty_banner()
        render_watchlist_learning_panel()
        render_options_learning_panel()

    with st.expander("📊 Charts & single-stock deep dive", expanded=False):
        st.caption(discipline_intro())
        render_ten_tips_expander()
        c1, c2, c3 = st.columns([2, 1, 1])
        default_t = st.session_state.get("intraday_ticker", st.session_state.get("single_ticker", "RELIANCE"))
        with c1:
            ticker = st.text_input("Stock", value=default_t, key="intraday_ticker_input").strip().upper()
        with c2:
            interval_key = st.selectbox("Candle", list(INTERVAL_OPTIONS.keys()), index=1, key="intraday_interval")
        with c3:
            auto = st.checkbox("Auto-refresh", value=True, key="intraday_auto")
            if st.button("Refresh now", key="intraday_refresh"):
                st.rerun()
        if auto:
            small_trader_portfolio_panel(market, interval_key)
        else:
            render_small_trader_portfolio_intraday(market, interval_key)
        st.session_state["intraday_ticker"] = ticker
        if not ticker:
            st.warning("Enter a stock symbol (e.g. RELIANCE, TCS, HDFCBANK).")
        elif auto:
            intraday_live_panel(ticker, interval_key, market)
        else:
            display_intraday_live(ticker, interval_key, market)
        st.caption(investopedia_screen_summary())
