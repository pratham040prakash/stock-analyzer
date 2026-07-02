"""Single stock analysis tab."""

from __future__ import annotations

import streamlit as st

from analyzer.advisor import generate_advice
from analyzer.candle_narrative import narrate_session
from analyzer.candlesticks import detect_patterns_at
from analyzer.combined import analyze_combined
from analyzer.data import fetch_benchmark, fetch_stock_data
from analyzer.delivery_quality import build_delivery_snapshot
from analyzer.earnings_calendar import fetch_corporate_event
from analyzer.india import indian_ticker_help
from analyzer.indicators import add_indicators
from analyzer.market_pulse import india_market_pulse
from analyzer.markets import format_market_cap, format_price, is_india_market
from analyzer.nse_options import enrich_with_nse_chain
from analyzer.options_signal import suggest_options_daily
from analyzer.relative_strength import compute_relative_strength
from analyzer.risk import capital_from_kite_margins, suggest_position_size
from analyzer.zerodha import fetch_kite_margins
from ui.charts import price_chart
from ui.components.delivery_quality import render_delivery_banner
from ui.components.earnings_calendar import render_earnings_banner
from ui.components.advice import render_advice, render_fundamentals, render_signals
from ui.components.intraday import render_options_verdict
from ui.theme import REC_COLORS, SIGNAL_ICONS


def render_single_stock(market: str, period: str) -> None:
    default = "RELIANCE" if is_india_market(market) else "AAPL"
    if "single_ticker" not in st.session_state:
        st.session_state["single_ticker"] = default
    ticker = st.text_input("Ticker symbol", key="single_ticker").strip()
    analyze_btn = st.button("Analyze", type="primary", key="single_analyze")

    if not analyze_btn:
        if is_india_market(market):
            st.markdown(
                "Enter an Indian ticker — e.g. **RELIANCE**, **TCS**, **SBI**, **L&T**, "
                "**BAJAJ AUTO**, **M&M**, or **RELIANCE.NS** / **RELIANCE.BO**"
            )
            with st.expander("Indian ticker formats & tips"):
                st.markdown(indian_ticker_help())
        else:
            st.markdown("Enter a ticker (e.g. **AAPL**, **MSFT**, **TSLA**) and click **Analyze**.")
        return

    if not ticker:
        st.error("Please enter a ticker symbol.")
        return

    with st.spinner(f"Fetching and analyzing {ticker}..."):
        try:
            df, info = fetch_stock_data(ticker, period=period, market=market)
            df = add_indicators(df)
            combined = analyze_combined(df, info["symbol"], yf_info=info)
            result = combined.technical
            fund = combined.fundamental
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            if is_india_market(market):
                st.info("Try **Search** in the sidebar to find the correct NSE/BSE symbol.")
            return

    if info.get("resolved_from"):
        st.caption(f"Resolved **{info['resolved_from']}** → **{info['symbol']}** ({info.get('exchange', '')})")
    sources = info.get("data_sources", ["Yahoo Finance"])
    st.caption(f"Data: {' + '.join(sources)}")

    comb_color = REC_COLORS.get(combined.combined_recommendation, "#ffd600")
    col1, col2, col3, col4, col5 = st.columns(5)
    price = info.get("nse_last_price") or result.current_price
    col1.metric("Price", format_price(price, info["symbol"]))
    col2.markdown(
        f"<div style='text-align:center'>"
        f"<p style='margin:0;color:#aaa;font-size:0.85rem'>Combined</p>"
        f"<p style='margin:0;font-size:1.4rem;font-weight:700;color:{comb_color}'>"
        f"{combined.combined_recommendation}</p></div>",
        unsafe_allow_html=True,
    )
    col3.metric("Combined Score", f"{combined.combined_score:+.1f}")
    col4.metric("Technical", f"{result.composite_score:+.1f}")
    col5.metric("Fundamental", f"{fund.composite_score:+.1f}")

    rs = None
    market_pulse = None
    if is_india_market(market):
        try:
            market_pulse = india_market_pulse(period)
        except Exception:
            pass

    if not info["symbol"].startswith("^"):
        try:
            bench_df, bench_info = fetch_benchmark(market, period)
            rs = compute_relative_strength(
                df, bench_df,
                benchmark_symbol=bench_info["symbol"],
                benchmark_name=bench_info.get("benchmark_name", "Benchmark"),
            )
            if rs.periods:
                a1, a2, a3 = st.columns(3)
                p = rs.periods[0]
                a1.metric(f"Stock {p.label}", f"{p.stock_return_pct:+.1f}%")
                a2.metric(f"{rs.benchmark_name} {p.label}", f"{p.benchmark_return_pct:+.1f}%")
                a3.metric("Alpha vs Index", f"{p.alpha_pct:+.1f}%", help=rs.verdict)
        except Exception:
            pass

    advice = generate_advice(combined, info, rs, market_pulse, df)
    render_advice(advice)

    with st.spinner("Checking earnings calendar…"):
        earnings_ev = fetch_corporate_event(info["symbol"], market=market)
    st.markdown("### 📅 Earnings & events")
    render_earnings_banner(earnings_ev)

    if is_india_market(market):
        with st.spinner("Fetching NSE delivery %…"):
            delivery_snap = build_delivery_snapshot(info["symbol"], df=df)
        st.markdown("### 📦 Delivery & volume quality")
        render_delivery_banner(delivery_snap)

    st.divider()
    left, right = st.columns([1.4, 1])

    with left:
        st.subheader(f"{info['name']} ({info['symbol']})")
        st.plotly_chart(price_chart(df, info["symbol"]), use_container_width=True)

    with right:
        st.subheader("Technical Signals")
        render_signals(result)
        st.divider()
        st.subheader("Fundamental Analysis")
        render_fundamentals(fund)
        st.divider()
        st.subheader("Key Levels")
        lvl1, lvl2 = st.columns(2)
        lvl1.metric("Support (20d low)", format_price(result.support, info["symbol"]))
        lvl2.metric("Resistance (20d high)", format_price(result.resistance, info["symbol"]))
        lvl3, lvl4 = st.columns(2)
        lvl3.metric("Stop Loss (2× ATR)", format_price(result.stop_loss, info["symbol"]))
        lvl4.metric("Take Profit (3× ATR)", format_price(result.take_profit, info["symbol"]))
        if is_india_market(market) and result.stop_loss and price:
            capital = None
            try:
                margins = fetch_kite_margins()
                capital = capital_from_kite_margins(margins)
            except Exception:
                pass
            cap_input = st.number_input(
                "Capital for position sizing (₹)",
                min_value=10000.0,
                value=float(capital or 500000),
                step=10000.0,
                key=f"pos_cap_{info['symbol']}",
            )
            pos = suggest_position_size(cap_input, float(price), float(result.stop_loss))
            if pos["shares"] > 0:
                st.caption(
                    f"Suggested: **{pos['shares']} shares** (~₹{pos['value']:,.0f}) · "
                    f"risk ₹{pos['risk_amount']:,.0f} · {pos['note']}"
                )
        st.divider()
        st.subheader("Company Info")
        st.write(f"**Exchange:** {info.get('exchange', 'N/A')}")
        st.write(f"**Sector:** {info['sector']}")
        st.write(f"**Industry:** {info['industry']}")
        st.write(f"**Market Cap:** {format_market_cap(info.get('market_cap'), info['symbol'])}")
        if info.get("isin"):
            st.write(f"**ISIN:** {info['isin']}")
        if info.get("roe") is not None:
            st.write(f"**ROE:** {info['roe'] * 100:.1f}%")
        if info.get("debt_to_equity") is not None:
            st.write(f"**Debt/Equity:** {info['debt_to_equity']:.2f}")
        if info.get("revenue_growth") is not None:
            st.write(f"**Revenue Growth:** {info['revenue_growth'] * 100:+.1f}%")
        if info.get("earnings_growth") is not None:
            st.write(f"**Earnings Growth:** {info['earnings_growth'] * 100:+.1f}%")
        if info.get("profit_margin") is not None:
            st.write(f"**Profit Margin:** {info['profit_margin'] * 100:.1f}%")
        if info.get("pe_ratio"):
            st.write(f"**P/E Ratio:** {info['pe_ratio']:.2f}")
        if info.get("dividend_yield"):
            st.write(f"**Dividend Yield:** {info['dividend_yield'] * 100:.2f}%")
        if info.get("fifty_two_week_low") and info.get("fifty_two_week_high"):
            st.write(
                f"**52-Week Range:** {format_price(info['fifty_two_week_low'], info['symbol'])}"
                f" – {format_price(info['fifty_two_week_high'], info['symbol'])}"
            )

    st.divider()
    st.subheader("📖 Daily candle stories (Varsity TA)")
    daily_stories = narrate_session(df, last_n=10, vol_sma_col="VOL_SMA_20")
    if daily_stories:
        latest = daily_stories[-1]
        icon = SIGNAL_ICONS.get(latest.bias, "⚪")
        st.markdown(f"**Latest:** {icon} {latest.story}")
        with st.expander("Story for each of the last 10 daily candles"):
            for candle in daily_stories:
                st.markdown(f"{SIGNAL_ICONS.get(candle.bias, '⚪')} {candle.story}")
        daily_patterns = detect_patterns_at(df, -1)
        daily_options = suggest_options_daily(
            latest,
            daily_patterns,
            result.composite_score,
            result.support,
            result.resistance,
            info["symbol"],
        )
        chain, picks, err = enrich_with_nse_chain(
            daily_options.action,
            info["symbol"].replace(".NS", "").replace(".BO", ""),
        )
        daily_options.nse_chain = chain
        daily_options.nse_picks = picks
        daily_options.nse_error = err
        st.markdown("#### Options (daily timeframe — CE / PE)")
        render_options_verdict(daily_options)
