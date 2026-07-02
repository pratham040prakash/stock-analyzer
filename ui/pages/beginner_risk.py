"""Beginner risk & goals — chart trend, market risk, fundamentals, position sizing."""

from __future__ import annotations

import streamlit as st

from analyzer.combined import analyze_combined
from analyzer.data import fetch_stock_data
from analyzer.delivery_quality import build_delivery_snapshot
from analyzer.earnings_calendar import fetch_corporate_event
from analyzer.options_analytics import build_options_analytics
from analyzer.indicators import add_indicators
from analyzer.market_risk import assess_market_risk, assess_nifty_market_risk
from analyzer.markets import format_price, is_india_market
from analyzer.risk import suggest_position_size
from ui.components.delivery_quality import render_delivery_banner
from ui.components.earnings_calendar import render_earnings_banner
from ui.components.iv_rank import render_iv_banner
from ui.theme import ACTION_COLORS


RISK_COLORS = {
    "Low": "#00c853",
    "Moderate": "#ffd600",
    "High": "#ff6e40",
    "Very High": "#d50000",
}


def _render_risk_card(assessment, *, show_ticker: bool = True) -> None:
    color = RISK_COLORS.get(assessment.risk_level, "#ffd600")
    title = f"{assessment.name}" if show_ticker else "Overall market"
    st.markdown(f"#### {title}")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f"<div style='padding:10px;border-radius:8px;background:#1e1e1e;text-align:center'>"
        f"<p style='margin:0;color:#aaa;font-size:0.75rem'>Risk level</p>"
        f"<p style='margin:0;font-size:1.3rem;font-weight:700;color:{color}'>{assessment.risk_level}</p></div>",
        unsafe_allow_html=True,
    )
    c2.metric("Risk score", f"{assessment.risk_score:.0f}/100", help="Higher = riskier for beginners")
    c3.metric("Chart trend", assessment.trend.direction)
    c4.metric("Nifty regime", assessment.market_regime)

    t1, t2, t3 = st.columns(3)
    if assessment.trend.return_1m_pct is not None:
        t1.metric("1M return", f"{assessment.trend.return_1m_pct:+.1f}%")
    if assessment.trend.return_3m_pct is not None:
        t2.metric("3M return", f"{assessment.trend.return_3m_pct:+.1f}%")
    if assessment.volatility_atr_pct is not None:
        t3.metric("Daily volatility (ATR)", f"{assessment.volatility_atr_pct:.1f}%")

    st.info(assessment.beginner_verdict)
    st.caption(assessment.trend.summary)

    if assessment.positive_factors:
        with st.expander("Positive factors", expanded=True):
            for p in assessment.positive_factors:
                st.markdown(f"- {p}")

    if assessment.risk_factors:
        with st.expander("Risk factors to watch", expanded=assessment.risk_level in ("High", "Very High")):
            for r in assessment.risk_factors:
                st.markdown(f"- {r}")

    st.markdown(
        f"**Fundamental quality:** {assessment.fundamental_grade} · "
        f"**Max suggested allocation:** {assessment.max_suggested_allocation_pct:.0f}% of portfolio · "
        f"**Stop-loss:** {assessment.stop_loss_note}"
    )
    st.caption(f"💡 {assessment.experience_tip}")


def render_beginner_risk(market: str, period: str) -> None:
    st.subheader("Risk & Goals (Beginner)")
    st.caption(
        "Chart-based **market risk**, recent **trend**, **fundamentals**, and **position sizing** — "
        "built for learning, not guaranteed profits."
    )

    st.markdown("### Your profile")
    g1, g2, g3 = st.columns(3)
    with g1:
        experience = st.selectbox(
            "Experience",
            options=["new", "some"],
            format_func=lambda x: "Very new (< 6 months)" if x == "new" else "Some experience (6M+)",
            key="beginner_experience",
        )
    with g2:
        goal = st.selectbox(
            "Primary goal",
            options=["learning", "long_term", "trading"],
            format_func=lambda x: {
                "learning": "Learn first (no real money)",
                "long_term": "Long-term investing (1–3 years)",
                "trading": "Short-term trading (weeks)",
            }[x],
            key="beginner_goal",
        )
    with g3:
        capital = st.number_input(
            "Portfolio capital (₹)" if is_india_market(market) else "Portfolio capital ($)",
            min_value=10000.0,
            value=500000.0,
            step=25000.0,
            key="beginner_capital",
        )

    risk_pct = st.slider(
        "Max risk per trade (% of capital)",
        min_value=0.5,
        max_value=3.0,
        value=1.0,
        step=0.5,
        help="Beginners should stay at 1% — lose small while learning.",
        key="beginner_risk_pct",
    )

    if goal == "learning":
        st.warning(
            "Learning mode: use **paper trades** only. Write down entry, stop, and target — "
            "check after 4 weeks in **Track Record**."
        )
    elif experience == "new" and goal == "trading":
        st.warning(
            "Short-term trading is the hardest path for beginners. "
            "Consider long-term SIP in Nifty index funds while you learn charts."
        )

    st.divider()
    st.markdown("### Market risk (Nifty 50)")
    if is_india_market(market):
        with st.spinner("Analyzing market trend and volatility..."):
            try:
                nifty_risk = assess_nifty_market_risk(period)
                _render_risk_card(nifty_risk, show_ticker=False)
            except Exception as exc:
                st.error(f"Could not assess market risk: {exc}")
    else:
        st.info("Switch sidebar to **India (Auto)** for Nifty market risk.")

    st.divider()
    st.markdown("### Stock risk check")
    default = "RELIANCE" if is_india_market(market) else "AAPL"
    ticker = st.text_input("Stock to analyze", value=default, key="beginner_risk_ticker").strip()

    if st.button("Analyze risk", type="primary", key="beginner_risk_analyze"):
        if not ticker:
            st.error("Enter a ticker.")
            return
        with st.spinner(f"Assessing {ticker}..."):
            try:
                df, info = fetch_stock_data(ticker, period=period, market=market)
                df = add_indicators(df)
                combined = analyze_combined(df, info["symbol"], yf_info=info)
                earnings_ev = fetch_corporate_event(info["symbol"], market=market)
                delivery_snap = build_delivery_snapshot(info["symbol"], df=df) if is_india_market(market) else None
                options_iv = (
                    build_options_analytics(info["symbol"].replace(".NS", "").replace(".BO", ""))
                    if is_india_market(market)
                    else None
                )
                assessment = assess_market_risk(
                    df,
                    info["symbol"],
                    name=info.get("name", ticker),
                    yf_info=info,
                    fund=combined.fundamental,
                    goal=goal,
                    experience=experience,
                    earnings_event=earnings_ev,
                    delivery_snapshot=delivery_snap,
                    options_analytics=options_iv,
                )
                st.session_state["beginner_stock_risk"] = assessment
                st.session_state["beginner_stock_earnings"] = earnings_ev
                st.session_state["beginner_stock_delivery"] = delivery_snap
                st.session_state["beginner_stock_iv"] = options_iv
                st.session_state["beginner_stock_price"] = info.get("nse_last_price") or combined.technical.current_price
                st.session_state["beginner_stock_stop"] = combined.technical.stop_loss
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

    if assessment := st.session_state.get("beginner_stock_risk"):
        _render_risk_card(assessment)
        if ev := st.session_state.get("beginner_stock_earnings"):
            st.markdown("**Earnings calendar**")
            horizon = "options" if goal == "trading" else ("long" if goal == "long_term" else "all")
            render_earnings_banner(ev, horizon=horizon)
        if dv := st.session_state.get("beginner_stock_delivery"):
            st.markdown("**Delivery & volume**")
            render_delivery_banner(dv)
        if iv := st.session_state.get("beginner_stock_iv"):
            st.markdown("**IV rank (options)**")
            horizon = "options" if goal == "trading" else ("long" if goal == "long_term" else "all")
            render_iv_banner(iv, horizon=horizon)
        price = st.session_state.get("beginner_stock_price")
        stop = st.session_state.get("beginner_stock_stop")
        if price and stop and goal != "learning":
            pos = suggest_position_size(capital, float(price), float(stop), risk_pct=risk_pct)
            sym = "₹" if is_india_market(market) else "$"
            st.markdown("### Position size (risk control)")
            if pos["shares"] > 0:
                st.success(
                    f"Suggested **{pos['shares']} shares** (~{sym}{pos['value']:,.0f}) · "
                    f"risk {sym}{pos['risk_amount']:,.0f} ({risk_pct}% of capital) · "
                    f"entry {format_price(price, assessment.ticker)} · stop {format_price(stop, assessment.ticker)}"
                )
            else:
                st.caption("Adjust capital or stop — inputs invalid for sizing.")
        elif goal == "learning":
            st.caption("Learning mode: note suggested shares on paper only.")

    st.divider()
    st.markdown("### Where to learn more in this app")
    st.markdown(
        "| Tab | Use for |\n"
        "|-----|--------|\n"
        "| **Varsity TA** | Free structured lessons (start here) |\n"
        "| **Single Stock** | Full technical + fundamental + advice |\n"
        "| **Market Pulse** | Scan Nifty 50 by trend |\n"
        "| **Backtest** | See how strategies behaved in the past |\n"
        "| **Track Record** | Validate suggestions over time |"
    )
