"""Watchlist scanner tab."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.markets import PRESET_WATCHLISTS, format_price, is_india_market, parse_tickers
from analyzer.watchlist import scan_watchlist


def render_watchlist(market: str, period: str) -> None:
    st.subheader("Batch Scanner")
    st.info(
        "**Batch Scanner** = scan any ticker list for signals. "
        "**Intraday tab → Top MIS picks** = your nightly top-5 with entry/stop/target for tomorrow."
    )
    st.caption(
        "Parallel scan of multiple symbols — not your MIS workflow. "
        "For **2 equity trades tomorrow**, use **Intraday → Top MIS picks**."
    )
    if is_india_market(market):
        preset_options = {
            "India Nifty 50 (top 15)": "nse_nifty",
            "India Nifty 50 (full)": "nse_nifty_full",
            "India IT": "nse_it",
            "India Banks": "nse_banks",
            "India Pharma": "nse_pharma",
            "India ETFs": "india_etfs",
            "India Indices": "india_indices",
        }
        default_idx = 0
    else:
        preset_options = {
            "US Mega Cap": "us_mega",
            "US Tech": "us_tech",
        }
        default_idx = 0
    preset_label = st.selectbox("Preset watchlist", list(preset_options.keys()), index=default_idx)
    preset_tickers = PRESET_WATCHLISTS[preset_options[preset_label]]

    custom = st.text_area(
        "Tickers (comma or newline separated)",
        value=", ".join(preset_tickers),
        height=100,
    )
    scan_btn = st.button("Scan batch", type="primary", key="watchlist_scan")

    if not scan_btn:
        st.markdown(
            "Scan multiple stocks at once. Results are ranked by bullish score (highest first)."
        )
        return

    tickers = parse_tickers(custom, market)
    if not tickers:
        st.error("Add at least one ticker.")
        return

    with st.spinner(f"Scanning {len(tickers)} tickers..."):
        rows = scan_watchlist(tickers, period=period, market=market)

    table_data = []
    for row in rows:
        if row.error:
            table_data.append({
                "Ticker": row.ticker,
                "Name": row.name,
                "Price": "—",
                "Recommendation": "ERROR",
                "Score": "—",
                "Confidence": row.error[:60],
            })
        else:
            table_data.append({
                "Ticker": row.ticker,
                "Name": row.name[:30],
                "Price": format_price(row.price, row.ticker),
                "Combined": row.recommendation,
                "Score": f"{row.score:+.1f}",
                "Technical": f"{row.technical_score:+.1f}",
                "Fundamental": f"{row.fundamental_score:+.1f}",
            })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    buys = [r for r in rows if not r.error and r.recommendation in ("STRONG BUY", "BUY")]
    sells = [r for r in rows if not r.error and r.recommendation in ("STRONG SELL", "SELL")]
    if buys:
        st.success(f"**Top bullish:** {', '.join(f'{r.ticker} ({r.score:+.0f})' for r in buys[:5])}")
    if sells:
        st.warning(f"**Bearish:** {', '.join(f'{r.ticker} ({r.score:+.0f})' for r in sells[:5])}")

    if rows and not rows[0].error:
        top = rows[0]
        st.info(
            f"**Best suggestion from scan:** **{top.name}** ({top.ticker}) — "
            f"Combined **{top.recommendation}** (score {top.score:+.0f}, "
            f"Tech {top.technical_score:+.0f}, Fund {top.fundamental_score:+.0f}). "
            f"Analyze in Single Stock tab for full investment advice."
        )
