"""Penny / low-priced stock picks — India only."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.markets import format_price, is_india_market
from analyzer.penny_stocks import (
    DEFAULT_MAX_PRICE_INR,
    MAX_PRICE_OPTIONS,
    format_penny_tips,
    scan_penny_stocks,
)
from ui.navigation import request_nav_tab


def render_penny_picks(market: str, period: str) -> None:
    st.subheader("Penny Stock Picks")
    st.markdown(
        "Scans a curated **low-price NSE universe** (under your ₹ cap) for **momentum + liquidity**. "
        "Ranked for **swing** setups — not long-term quality."
    )

    if not is_india_market(market):
        st.warning("Switch **Exchange** in the sidebar to **India** to scan penny stocks on NSE.")
        return

    st.error(
        "**High risk:** Penny stocks can go to zero. Pump-and-dump, low liquidity, and corporate "
        "governance issues are common. Never invest money you need for goals or emergencies."
    )

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        max_price = st.selectbox(
            "Max price (₹)",
            options=list(MAX_PRICE_OPTIONS),
            index=list(MAX_PRICE_OPTIONS).index(DEFAULT_MAX_PRICE_INR),
            key="penny_max_price",
        )
    with c2:
        top_n = st.slider("Top picks", min_value=3, max_value=10, value=5, key="penny_top_n")
    with c3:
        st.caption("Universe: ~50 liquid NSE names often in the penny/small-cap band. Live price filter applies.")

    if st.button("Scan penny stocks", type="primary", key="penny_scan"):
        with st.spinner(f"Scanning NSE names under ₹{max_price:g}..."):
            st.session_state["penny_report"] = scan_penny_stocks(
                max_price_inr=float(max_price),
                period=period,
                market=market,
                limit=top_n,
            )

    report = st.session_state.get("penny_report")
    if not report:
        st.info(
            f"Click **Scan penny stocks** to rank setups under **₹{max_price:g}**. "
            "Example band: ₹10–20 names with volume and delivery filters."
        )
        st.markdown(format_penny_tips())
        return

    st.caption(
        f"Scanned **{report.scanned}** symbols · **{report.matched_price}** under ₹{report.max_price_inr:g} · "
        f"showing top **{len(report.picks)}**"
    )

    if not report.picks:
        st.warning(
            f"No strong setups under ₹{report.max_price_inr:g} right now. "
            "Try a higher cap (₹50) or check **Market Pulse** / **Screener** for larger names."
        )
        if report.avoid:
            with st.expander("Filtered out (sample)"):
                for line in report.avoid:
                    st.caption(f"· {line}")
        st.markdown(format_penny_tips())
        return

    best = report.picks[0]
    st.success(
        f"**Best penny setup today:** {best.name} ({best.nse_symbol}) @ "
        f"{format_price(best.price, best.ticker)} — score **{best.penny_score:.0f}** · "
        f"{best.short_action} ({best.short_score:+.0f})"
    )

    table = []
    for p in report.picks:
        table.append({
            "Rank": p.rank,
            "Stock": p.nse_symbol,
            "Name": p.name[:22],
            "Price": format_price(p.price, p.ticker),
            "Score": f"{p.penny_score:.0f}",
            "Swing": f"{p.short_action} ({p.short_score:+.0f})",
            "Combined": p.combined_rec,
            "Vol×": f"{p.volume_ratio:.1f}" if p.volume_ratio else "—",
            "Del%": f"{p.delivery_pct:.0f}" if p.delivery_pct is not None else "—",
            "RSI": f"{p.rsi:.0f}" if p.rsi is not None else "—",
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    st.markdown("#### Why these names")
    for p in report.picks:
        with st.expander(f"#{p.rank} {p.nse_symbol} — {format_price(p.price, p.ticker)}", expanded=p.rank <= 2):
            st.markdown(p.thesis)
            if p.risk_flags:
                for flag in p.risk_flags:
                    st.warning(flag)
            else:
                st.caption("Still high risk by definition — penny band.")
            if st.button(f"Analyze {p.nse_symbol}", key=f"penny_open_{p.nse_symbol}"):
                request_nav_tab("Single Stock", single_ticker=p.nse_symbol)

    if report.avoid:
        with st.expander("Filtered out (liquidity / churn)"):
            for line in report.avoid:
                st.caption(f"· {line}")

    st.divider()
    st.markdown(format_penny_tips())
    st.caption(report.disclaimer)
