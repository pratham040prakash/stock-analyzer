"""Intraday tab — live candles, stories, and trade suggestions."""

from __future__ import annotations

from datetime import timedelta

import streamlit as st

from analyzer.candle_narrative import analyze_live_chart
from analyzer.intraday_chart import intraday_chart
from analyzer.intraday_data import INTERVAL_OPTIONS, fetch_intraday, market_session_status
from analyzer.intraday_signals import add_intraday_indicators
from analyzer.intraday_stock_picker import investopedia_screen_summary
from analyzer.nse_options import enrich_with_nse_chain
from analyzer.varsity_knowledge import format_signal_context
from ui.components.intraday import render_candle_stories, render_live_verdict
from ui.components.small_trader_intraday import render_small_trader_portfolio_intraday
from ui.theme import SIGNAL_ICONS


def display_intraday_live(ticker: str, interval_key: str, market: str) -> None:
    interval = INTERVAL_OPTIONS[interval_key]
    session = market_session_status()

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

        render_live_verdict(verdict)

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


def render_intraday(market: str) -> None:
    st.subheader("Intraday — Live Charts & Candle Stories")
    st.markdown(
        "Reads the **live chart** candle-by-candle (Varsity TA), tells you **what each candle means**, "
        "and gives a **BUY / SELL / WAIT** suggestion from the **current candle**. "
        "With **≤10 stocks** in **My Portfolio**, you get a **full watchlist scan** above."
    )

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

    st.divider()
    st.markdown("#### Single stock — deep dive")

    st.session_state["intraday_ticker"] = ticker

    if not ticker:
        st.warning("Enter a stock symbol (e.g. RELIANCE, TCS, HDFCBANK).")
        return

    if auto:
        intraday_live_panel(ticker, interval_key, market)
    else:
        display_intraday_live(ticker, interval_key, market)

    st.divider()
    st.markdown("#### How we pick intraday stocks")
    st.caption(investopedia_screen_summary())
    st.markdown(
        "**Intraday tips**\n"
        "- **Liquidity** — Nifty 50 names with high volume; avoid illiquid strikes\n"
        "- **Volatility** — target ~2–5% daily range; skip dead or extreme movers\n"
        "- **Nifty correlation** — trade long when index is bullish and stock tracks Nifty\n"
        "- **VWAP** — price above = bullish bias for the day; below = bearish\n"
        "- **Opening range** (first 15 min on 5m chart) — breakout/breakdown signals\n"
        "- **Square off** MIS positions before 3:20 PM IST to avoid auto square-off\n"
        "- For **true tick-by-tick** data, connect Zerodha Kite API (₹500/mo data subscription)"
    )
