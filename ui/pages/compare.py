"""Compare 2–4 stocks side by side."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.compare import compare_stocks, pick_winner
from analyzer.markets import format_price, is_india_market, parse_tickers


PRESETS: dict[str, list[str]] = {
    "IT giants": ["TCS.NS", "INFY.NS", "HCLTECH.NS"],
    "Bank leaders": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS"],
    "Conglomerates": ["RELIANCE.NS", "TATASTEEL.NS", "ADANIENT.NS"],
}


def render_compare(market: str, period: str) -> None:
    st.subheader("Compare Stocks")
    st.markdown(
        "Side-by-side **combined score**, swing/long setup, fundamentals, and **vs Nifty** — "
        "pick the strongest name for your horizon."
    )

    preset = st.selectbox(
        "Quick preset",
        ["Custom"] + list(PRESETS.keys()),
        key="cmp_preset",
    )
    default_text = ", ".join(PRESETS.get(preset, ["RELIANCE", "TCS", "INFY"]) if preset != "Custom" else ["RELIANCE", "TCS"])

    tickers_text = st.text_input(
        "Tickers to compare (2–4)",
        value=default_text,
        key="cmp_tickers",
    )

    if st.button("Compare", type="primary", key="cmp_run"):
        tickers = parse_tickers(tickers_text, market)[:4]
        if len(tickers) < 2:
            st.error("Enter at least 2 tickers.")
        else:
            with st.spinner(f"Comparing {len(tickers)} stocks..."):
                st.session_state["compare_rows"] = compare_stocks(
                    tickers, period=period, market=market,
                )

    rows = st.session_state.get("compare_rows")
    if not rows:
        st.info("Example: compare **RELIANCE**, **TCS**, **INFY** for long-term quality vs momentum.")
        return

    table = []
    for r in rows:
        if r.error:
            table.append({"Stock": r.ticker, "Result": f"Error: {r.error[:60]}"})
            continue
        roe_s = f"{r.roe * 100:.0f}%" if r.roe is not None else "—"
        table.append({
            "Stock": r.ticker.replace(".NS", ""),
            "Name": r.name[:24],
            "Price": format_price(r.price, r.ticker),
            "Combined": r.combined_rec,
            "Score": f"{r.combined_score:+.0f}",
            "Swing": f"{r.short_action} ({r.short_score:+.0f})",
            "Long": f"{r.long_action} ({r.long_score:+.0f})",
            "RSI": f"{r.rsi:.0f}" if r.rsi is not None else "—",
            "P/E": f"{r.pe:.1f}" if r.pe else "—",
            "ROE": roe_s,
            "vs Nifty": r.rs_verdict,
            "3M α": f"{r.alpha_3m:+.1f}%" if r.alpha_3m is not None else "—",
            "Del%": f"{r.delivery_pct:.0f}" if r.delivery_pct is not None else "—",
        })

    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    winner = pick_winner(rows)
    if winner:
        st.success(
            f"**Top pick (combined score):** {winner.name} ({winner.ticker.replace('.NS', '')}) — "
            f"{winner.combined_rec} ({winner.combined_score:+.0f}) · "
            f"Swing {winner.short_action} · Long {winner.long_action}"
        )

    st.markdown("#### Open in Single Stock")
    cols = st.columns(min(4, len(rows)))
    for i, r in enumerate(rows):
        if r.error:
            continue
        sym = r.ticker.replace(".NS", "").replace(".BO", "")
        with cols[i % len(cols)]:
            if st.button(sym, key=f"cmp_open_{sym}_{i}"):
                st.session_state["single_ticker"] = sym
                st.session_state["nav_tab"] = "Single Stock"
                st.rerun()

    if is_india_market(market):
        st.caption("Delivery % from NSE (same day). Compare long-term names on **Long** column, swings on **Swing**.")
