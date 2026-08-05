"""Live Charts grid page — all stocks, minute narratives."""
# APEX-012-LIFECYCLE: QUARANTINED

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from analyzer.intraday_chart import intraday_chart
from analyzer.intraday_data import INTERVAL_OPTIONS, fetch_intraday
from analyzer.market_session import market_session_status
from analyzer.live_charts_grid import LiveChartRow, clear_live_charts_cache, fetch_live_charts_grid
from analyzer.providers import data_source_status
from ui.theme import INTRADAY_SETUP_COLORS


def _live_chart_row_card(row: LiveChartRow, show_chart: bool) -> None:
    color = INTRADAY_SETUP_COLORS.get(row.action, "#ffd600")
    title = f"**{row.nse_symbol}** · {row.action} ({row.confidence}) · {row.candle_type} @ {row.current_time}"
    with st.expander(title, expanded=row.action in ("STRONG BUY", "STRONG SELL")):
        if row.error:
            st.error(row.error)
            return

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("LTP", f"₹{row.price:,.2f}")
        c2.metric("Action", row.action)
        c3.metric("Score", f"{row.score:+.1f}")
        if row.entry:
            c4.metric("Entry", f"₹{row.entry:,.2f}")
            c5.metric("Stop / Target", f"₹{row.stop_loss:,.2f} / ₹{row.target:,.2f}")
        else:
            c4.metric("Entry", "—")
            c5.metric("Stop / Target", "—")

        st.markdown(
            f"<p style='margin:0.5rem 0;font-size:1.05rem;color:{color};font-weight:600'>"
            f"{row.action}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(row.hypothesis)
        st.markdown(f"**Latest candle ({row.current_time}):** {row.minute_story}")
        st.caption(row.session_story)

        if show_chart and row.chart_df is not None and row.verdict and row.verdict.intraday:
            st.plotly_chart(
                intraday_chart(row.chart_df, row.verdict.intraday),
                use_container_width=True,
                key=f"live_grid_chart_{row.nse_symbol}_{row.interval}",
            )

        if row.verdict:
            st.markdown("**Per-minute candle log**")
            minute_rows = []
            for c in reversed(row.verdict.recent_candles[-15:]):
                minute_rows.append({
                    "Time": c.time,
                    "Candle": c.candle_type,
                    "Close": f"₹{c.close:,.2f}",
                    "Chg%": f"{c.change_pct:+.2f}%",
                    "Bias": c.bias.upper(),
                    "What happened": c.story.split("—", 1)[-1].strip()[:120],
                })
            st.dataframe(pd.DataFrame(minute_rows), use_container_width=True, hide_index=True)

            if row.verdict.reasons:
                st.markdown("**Why buy/sell/wait:**")
                for reason in row.verdict.reasons[:5]:
                    st.markdown(f"- {reason}")


@st.fragment(run_every=timedelta(seconds=60))
def live_charts_grid_panel(
    universe: str,
    interval_key: str,
    action_filter: str,
    show_charts: bool,
) -> None:
    display_live_charts_grid(universe, interval_key, action_filter, show_charts)


def display_live_charts_grid(
    universe: str,
    interval_key: str,
    action_filter: str,
    show_charts: bool,
) -> None:
    interval = INTERVAL_OPTIONS[interval_key]
    session = market_session_status()
    ds = data_source_status()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NSE Session", session["status"])
    c2.metric("IST", session["time_ist"])
    c3.metric("Data source", ds["primary_intraday"])
    c4.caption("Refresh: every **60 sec**")

    with st.spinner(f"Scanning {universe} on {interval_key} candles…"):
        report = fetch_live_charts_grid(universe=universe, interval=interval, cache_ttl=60)

    st.caption(
        f"**{report.universe}** · {report.interval} · session **{report.session_date}** · "
        f"updated **{report.updated_at}** · {ds['upgrade_hint']}"
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BUY", report.buy_count)
    m2.metric("SELL", report.sell_count)
    m3.metric("WAIT", report.wait_count)
    m4.metric("Errors", report.error_count)

    rows = report.rows
    if action_filter == "BUY":
        rows = [r for r in rows if r.action in ("STRONG BUY", "BUY")]
    elif action_filter == "SELL":
        rows = [r for r in rows if r.action in ("STRONG SELL", "SELL")]
    elif action_filter == "WAIT":
        rows = [r for r in rows if r.action == "WAIT"]

    summary = []
    for r in rows:
        summary.append({
            "Symbol": r.nse_symbol,
            "Action": r.action,
            "Conf": r.confidence,
            "Time": r.current_time,
            "Candle": r.candle_type,
            "LTP": f"₹{r.price:,.2f}",
            "Score": f"{r.score:+.1f}",
            "Entry": f"₹{r.entry:,.2f}" if r.entry else "—",
            "Stop": f"₹{r.stop_loss:,.2f}" if r.stop_loss else "—",
            "Target": f"₹{r.target:,.2f}" if r.target else "—",
            "Minute story": (r.minute_story[:90] + "…") if len(r.minute_story) > 90 else r.minute_story,
        })
    st.markdown("#### All stocks — live verdicts")
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

    st.markdown("#### Charts + minute-by-minute stories")
    for row in rows:
        _live_chart_row_card(row, show_chart=show_charts)


def render_live_charts_grid(market: str) -> None:
    st.subheader("Live Charts — All Stocks")
    st.markdown(
        "Scans **every stock** in the selected universe on **1-minute (or 5m/15m) candles**, "
        "narrates **what each minute bar is doing**, and gives a **buy / sell / wait hypothesis**. "
        "Uses **Kite live candles** when your token is in `.env`; otherwise Yahoo (lagged)."
    )

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        universe = st.selectbox(
            "Universe",
            ["Nifty 10 (fast)", "Nifty 50", "Indices"],
            index=0,
            key="live_grid_universe",
        )
    with c2:
        interval_key = st.selectbox(
            "Candle",
            list(INTERVAL_OPTIONS.keys()),
            index=0,
            key="live_grid_interval",
        )
    with c3:
        action_filter = st.selectbox("Filter", ["All", "BUY", "SELL", "WAIT"], key="live_grid_filter")
    with c4:
        auto = st.checkbox("Auto-refresh", value=True, key="live_grid_auto")
        show_charts = st.checkbox("Show charts", value=True, key="live_grid_charts")

    if st.button("Refresh now", key="live_grid_refresh"):
        clear_live_charts_cache()
        st.rerun()

    if auto:
        live_charts_grid_panel(universe, interval_key, action_filter, show_charts)
    else:
        display_live_charts_grid(universe, interval_key, action_filter, show_charts)

    st.divider()
    st.markdown(
        "**How to read this**\n"
        "- **Minute story** — what the latest candle did (body, wicks, volume, patterns)\n"
        "- **Hypothesis** — suggested entry, stop, and target from VWAP + opening range\n"
        "- **Nifty 50** takes 2–4 min on first load; use **Nifty 10** for faster updates\n"
        "- For MIS, square off before **3:20 PM IST**"
    )
