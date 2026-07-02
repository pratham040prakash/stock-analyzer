"""UI for small-trader portfolio intraday strip."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.intraday_chart import intraday_chart
from analyzer.intraday_data import INTERVAL_OPTIONS
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from analyzer.small_trader_intraday import (
    MAX_SMALL_TRADER_STOCKS,
    scan_small_trader_portfolio,
    small_trader_intraday_tips,
)
from ui.components.intraday import render_live_verdict
from ui.theme import INTRADAY_SETUP_COLORS


def _load_portfolio():
    imp = st.session_state.get("zd_import")
    if imp and imp.holdings:
        return imp
    return load_saved_portfolio(profile=portfolio_profile_key())


def render_small_trader_portfolio_intraday(market: str, interval_key: str) -> bool:
    """
    Show intraday table for portfolios with ≤10 stocks.
    Returns True if panel was rendered (caller may adjust layout).
    """
    imp = _load_portfolio()
    if not imp or not imp.holdings:
        st.info(
            f"**Small trader mode:** Save up to **{MAX_SMALL_TRADER_STOCKS} stocks** in "
            "**My Portfolio** to see intraday action on all your holdings here."
        )
        return False

    n = len(imp.holdings)
    if n > MAX_SMALL_TRADER_STOCKS:
        st.caption(
            f"You have **{n} holdings** — intraday portfolio scan works best with "
            f"**≤{MAX_SMALL_TRADER_STOCKS}**. Use single-stock view below, or trim your saved portfolio."
        )
        return False

    interval = INTERVAL_OPTIONS.get(interval_key, "5m")

    with st.spinner(f"Scanning {n} holdings for intraday setups..."):
        report = scan_small_trader_portfolio(imp, interval=interval, market=market)

    if not report:
        return False

    st.subheader(f"Your portfolio — intraday ({n} stocks)")
    st.caption(
        f"Updated **{report.updated_at}** · {interval_key} candles · "
        "built for small traders who focus on a short watchlist."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Buy setups", report.buy_count)
    m2.metric("Sell / fade", report.sell_count)
    m3.metric("Wait", report.wait_count)
    m4.metric("Session", "OPEN" if report.session_open else "CLOSED")

    table = []
    for r in report.rows:
        if r.error:
            table.append({
                "Stock": r.nse_symbol,
                "Action": "ERROR",
                "LTP": "—",
                "vs VWAP": "—",
                "P&L %": "—",
                "Entry": "—",
                "Stop": "—",
                "Note": r.error[:40],
            })
            continue
        pnl_s = f"{r.pnl_pct:+.1f}" if r.pnl_pct is not None else "—"
        table.append({
            "Stock": r.nse_symbol,
            "Qty": int(r.quantity),
            "Action": r.action,
            "LTP": f"₹{r.price:,.2f}",
            "vs VWAP": "Above" if r.above_vwap else "Below",
            "P&L %": pnl_s,
            "Entry": f"₹{r.entry:,.2f}" if r.entry else "—",
            "Stop": f"₹{r.stop_loss:,.2f}" if r.stop_loss else "—",
            "Target": f"₹{r.target:,.2f}" if r.target else "—",
        })

    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    if report.focus_symbols:
        st.success(
            "**Today's focus (max 1–2 MIS trades):** "
            + ", ".join(report.focus_symbols)
        )

    st.markdown(small_trader_intraday_tips(report))

    with st.expander("Per-stock detail & charts"):
        for r in report.rows:
            if r.error or not r.verdict:
                st.error(f"**{r.nse_symbol}:** {r.error or 'No data'}")
                continue
            color = INTRADAY_SETUP_COLORS.get(r.action, "#ffd600")
            st.markdown(
                f"#### {r.nse_symbol} — "
                f"<span style='color:{color};font-weight:700'>{r.action}</span>",
                unsafe_allow_html=True,
            )
            st.caption(r.owner_note)
            st.markdown(r.hypothesis)
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button(f"Open {r.nse_symbol} chart below", key=f"st_open_{r.nse_symbol}"):
                    st.session_state["intraday_ticker"] = r.nse_symbol
                    st.rerun()
            with c2:
                st.caption(f"Confidence: {r.confidence}")
            if r.chart_df is not None and r.verdict.intraday:
                st.plotly_chart(
                    intraday_chart(r.chart_df, r.verdict.intraday),
                    use_container_width=True,
                    key=f"st_chart_{r.nse_symbol}",
                )
            render_live_verdict(r.verdict)
            st.divider()

    return True
