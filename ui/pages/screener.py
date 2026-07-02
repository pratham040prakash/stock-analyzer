"""Custom stock screener tab."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.markets import PRESET_WATCHLISTS, format_price, is_india_market, parse_tickers
from analyzer.screener import PRESET_SCREENS, ScreenerCriteria, criteria_summary, run_screener
from ui.navigation import request_nav_tab


def _universe_options(market: str) -> dict[str, str]:
    if is_india_market(market):
        return {
            "Nifty 50 (full)": "nse_nifty_full",
            "Nifty 50 (top 15)": "nse_nifty",
            "India IT": "nse_it",
            "India Banks": "nse_banks",
            "India Pharma": "nse_pharma",
            "Penny candidates (NSE)": "nse_penny",
            "Custom list": "custom",
        }
    return {
        "US Mega Cap": "us_mega",
        "US Tech": "us_tech",
        "Custom list": "custom",
    }


def _build_custom_criteria(
    preset: ScreenerCriteria,
    *,
    min_combined: float | None,
    min_short: float | None,
    min_long: float | None,
    max_rsi: float | None,
    min_vol: float | None,
    min_delivery: float | None,
    skip_speculative: bool,
    skip_earnings_days: int | None,
    max_pe: float | None,
    min_roe_pct: float | None,
    above_sma20: bool,
    above_sma200: bool,
) -> ScreenerCriteria:
    overrides = ScreenerCriteria(
        min_combined_score=min_combined,
        min_short_score=min_short,
        min_long_score=min_long,
        max_rsi=max_rsi,
        min_volume_ratio=min_vol,
        min_delivery_pct=min_delivery,
        exclude_speculative_delivery=skip_speculative,
        exclude_earnings_within_days=skip_earnings_days,
        max_pe=max_pe,
        min_roe=min_roe_pct / 100.0 if min_roe_pct else None,
        above_sma20=True if above_sma20 else None,
        above_sma200=True if above_sma200 else None,
    )
    from analyzer.screener import merge_criteria

    return merge_criteria(preset, overrides)


def render_screener(market: str, period: str) -> None:
    st.subheader("Custom Screener")
    st.markdown(
        "Scan a universe with **technical + fundamental + India delivery/earnings** filters. "
        "Pick a preset or tune sliders, then open matches in **Single Stock**."
    )

    universe_opts = _universe_options(market)
    u1, u2 = st.columns([2, 1])
    with u1:
        universe_label = st.selectbox("Universe", list(universe_opts.keys()), key="scr_universe")
    with u2:
        preset_name = st.selectbox(
            "Screen preset",
            ["Custom"] + list(PRESET_SCREENS.keys()),
            key="scr_preset",
        )

    preset_key = universe_opts[universe_label]
    if preset_key == "nse_penny":
        from analyzer.penny_stocks import penny_universe_yahoo

        penny_list = penny_universe_yahoo()
        ticker_text = ", ".join(penny_list)
        st.caption(f"**{len(penny_list)}** penny-band NSE symbols · use **Penny Picks** tab for ranked best")
    elif preset_key == "custom":
        default_tickers = ", ".join(PRESET_WATCHLISTS.get("nse_nifty_full" if is_india_market(market) else "us_mega", []))
        ticker_text = st.text_area("Tickers (comma or newline)", value=default_tickers, height=80, key="scr_tickers")
    else:
        ticker_text = ", ".join(PRESET_WATCHLISTS[preset_key])
        st.caption(f"**{len(PRESET_WATCHLISTS[preset_key])}** symbols in universe")

    with st.expander("Filter tweaks (optional)", expanded=preset_name == "Custom"):
        c1, c2, c3 = st.columns(3)
        with c1:
            min_combined = st.number_input("Min combined score", value=0.0, min_value=-100.0, max_value=100.0, step=5.0)
            min_short = st.number_input("Min swing score", value=0.0, min_value=0.0, max_value=100.0, step=5.0)
            max_rsi = st.number_input("Max RSI (oversold)", value=0.0, min_value=0.0, max_value=100.0, step=5.0)
        with c2:
            min_long = st.number_input("Min long-term score", value=0.0, min_value=0.0, max_value=100.0, step=5.0)
            min_vol = st.number_input("Min volume vs 20d avg (×)", value=0.0, min_value=0.0, max_value=5.0, step=0.1)
            max_pe = st.number_input("Max P/E (0 = off)", value=0.0, min_value=0.0, max_value=200.0, step=1.0)
        with c3:
            min_delivery = st.number_input("Min delivery % (India)", value=0.0, min_value=0.0, max_value=100.0, step=5.0)
            min_roe = st.number_input("Min ROE % (0 = off)", value=0.0, min_value=0.0, max_value=50.0, step=1.0)
            skip_earn = st.number_input("Skip earnings within (days, 0=off)", value=0, min_value=0, max_value=30, step=1)
        f1, f2, f3 = st.columns(3)
        with f1:
            above_sma20 = st.checkbox("Price above SMA-20", value=False)
        with f2:
            above_sma200 = st.checkbox("Price above SMA-200", value=False)
        with f3:
            skip_spec = st.checkbox("Exclude speculative delivery", value=False)

    run = st.button("Run screener", type="primary", key="scr_run")

    base = PRESET_SCREENS.get(preset_name, ScreenerCriteria(name="Custom"))
    criteria = _build_custom_criteria(
        base,
        min_combined=min_combined if min_combined > 0 else None,
        min_short=min_short if min_short > 0 else None,
        min_long=min_long if min_long > 0 else None,
        max_rsi=max_rsi if max_rsi > 0 else None,
        min_vol=min_vol if min_vol > 0 else None,
        min_delivery=min_delivery if min_delivery > 0 else None,
        skip_speculative=skip_spec,
        skip_earnings_days=skip_earn if skip_earn > 0 else None,
        max_pe=max_pe if max_pe > 0 else None,
        min_roe_pct=min_roe if min_roe > 0 else None,
        above_sma20=above_sma20,
        above_sma200=above_sma200,
    )
    criteria = ScreenerCriteria(**{**criteria.__dict__, "name": preset_name if preset_name != "Custom" else "Custom"})

    st.caption(f"**Active filters:** {criteria_summary(criteria)}")

    if not run:
        st.info(
            "Presets: **Quality compounders**, **Swing momentum**, **Penny momentum (risky)**, "
            "**Oversold bounce**, **Breakout watch**, **Value hunters**."
        )
        return

    tickers = parse_tickers(
        ticker_text if preset_key in ("custom", "nse_penny") else ", ".join(PRESET_WATCHLISTS[preset_key]),
        market,
    )
    if not tickers:
        st.error("Add at least one ticker to the universe.")
        return

    with st.spinner(f"Scanning {len(tickers)} stocks (parallel)…"):
        results = run_screener(tickers, criteria, period=period, market=market)

    st.markdown(f"### Matches: **{len(results)}** / {len(tickers)} scanned")
    if not results:
        st.warning("No stocks passed all filters. Loosen criteria or try a smaller preset.")
        return

    table = []
    for r in results:
        table.append({
            "Stock": r.nse_symbol,
            "Name": (r.name or "")[:28],
            "Price": format_price(r.price, r.ticker),
            "Combined": r.combined_rec,
            "Score": f"{r.combined_score:+.0f}",
            "Swing": f"{r.short_action} ({r.short_score:+.0f})",
            "Long": f"{r.long_action} ({r.long_score:+.0f})",
            "RSI": f"{r.rsi:.0f}" if r.rsi is not None else "—",
            "Vol×": f"{r.volume_ratio:.1f}" if r.volume_ratio else "—",
            "Del%": f"{r.delivery_pct:.0f}" if r.delivery_pct is not None else "—",
            "P/E": f"{r.pe:.1f}" if r.pe else "—",
            "ROE%": f"{r.roe * 100:.0f}" if r.roe else "—",
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    st.markdown("**Open in Single Stock**")
    cols = st.columns(min(5, len(results)))
    for i, row in enumerate(results[:10]):
        with cols[i % len(cols)]:
            if st.button(row.nse_symbol, key=f"scr_open_{row.nse_symbol}_{i}"):
                request_nav_tab("Single Stock", single_ticker=row.nse_symbol)

    top = results[0]
    st.success(
        f"Top match: **{top.name}** ({top.nse_symbol}) — {top.combined_rec} "
        f"({top.combined_score:+.0f}) · Swing {top.short_action} · Long {top.long_action}"
    )
