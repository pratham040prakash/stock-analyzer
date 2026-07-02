"""NSE Options tab."""

from __future__ import annotations

import streamlit as st

from analyzer.candle_narrative import analyze_live_chart
from analyzer.intraday_data import fetch_intraday
from analyzer.nse_options import (
    chain_summary_markdown,
    fetch_contract_info,
    fetch_market_status,
    fetch_option_chain,
    recommend_nse_strikes,
)
from analyzer.options_analytics import analyze_and_record_chain
from ui.components.intraday import render_candle_stories, render_options_verdict
from ui.components.iv_rank import render_iv_banner


def render_nse_options(market: str) -> None:
    st.subheader("NSE India — Options Chain & CE/PE Picks")
    st.markdown(
        "Live data from **[NSE India](https://www.nseindia.com/)** option chain API. "
        "Combines OI, volume, IV with candle-based CE/PE suggestion."
    )

    try:
        ms = fetch_market_status()
        cap = ms.get("marketState", [{}])[0]
        st.caption(
            f"Market: **{cap.get('marketStatus', '—')}** · "
            f"{cap.get('index', '')} {cap.get('last', '')} ({cap.get('percentChange', 0):+.2f}%)"
        )
    except Exception:
        pass

    c1, c2 = st.columns([2, 1])
    default = st.session_state.get("nse_opt_symbol", "RELIANCE")
    with c1:
        sym = st.text_input("F&O symbol", value=default, key="nse_opt_sym").strip().upper()
    with c2:
        run = st.button("Load NSE chain", type="primary", key="nse_load")

    st.session_state["nse_opt_symbol"] = sym
    if not sym:
        st.info("Enter **RELIANCE**, **TCS**, **NIFTY**, **BANKNIFTY**, etc.")
        return

    try:
        info = fetch_contract_info(sym)
        expiries = info.get("expiryDates") or []
    except Exception as exc:
        st.error(f"Cannot load NSE contract info for {sym}: {exc}")
        return

    expiry = st.selectbox("Expiry date", expiries, key="nse_expiry_sel") if expiries else None
    if not run and "nse_chain_cache" not in st.session_state:
        st.caption("Click **Load NSE chain** to fetch live CE/PE data.")
        return

    if run:
        with st.spinner(f"Fetching NSE option chain for {sym}..."):
            try:
                chain = fetch_option_chain(sym, expiry=expiry)
                analytics = analyze_and_record_chain(chain)
                df, _ = fetch_intraday(sym, "5m", market)
                verdict = analyze_live_chart(df, sym, "5m")
                action = verdict.options.action if verdict.options else "NO TRADE"
                picks = recommend_nse_strikes(chain, action)
                st.session_state["nse_chain_cache"] = (chain, verdict, picks, analytics)
            except Exception as exc:
                st.error(str(exc))
                return

    cached = st.session_state.get("nse_chain_cache")
    if cached and len(cached) == 4:
        chain, verdict, picks, analytics = cached
    else:
        chain, verdict, picks = cached if cached else (None, None, [])
        analytics = None

    if chain:
        st.markdown(chain_summary_markdown(chain))
        if analytics:
            render_iv_banner(analytics, horizon="options", symbol=sym)
            with st.expander("PCR & OI details"):
                from analyzer.options_analytics import analytics_markdown
                st.markdown(analytics_markdown(analytics))
    if verdict and verdict.options:
        verdict.options.nse_chain = chain
        verdict.options.nse_picks = picks
        render_options_verdict(verdict.options)
    elif picks:
        for pick in picks:
            st.success(pick.reason)

    if verdict:
        st.divider()
        render_candle_stories(verdict)
