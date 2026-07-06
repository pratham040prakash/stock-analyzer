"""Alpha AI — institutional equity research tab."""

from __future__ import annotations

import streamlit as st

from analyzer.alpha_ai_report import build_alpha_ai_report
from analyzer.india import indian_ticker_help
from analyzer.markets import format_price, is_india_market
from ui.theme import MOBILE_CSS, REC_COLORS


def _stars(n: int) -> str:
    return "★" * n + "☆" * (5 - n)


def render_alpha_ai(market: str, period: str) -> None:
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    st.subheader("Alpha AI — Institutional Research")
    st.caption(
        "Evidence-based report · FACT / ASSUMPTION / ESTIMATE labeled · "
        "Goal: **₹10 Cr** via preservation + compound growth · Not financial advice."
    )

    default = "TCS" if is_india_market(market) else "AAPL"
    if "alpha_ai_ticker" not in st.session_state:
        st.session_state["alpha_ai_ticker"] = default

    c1, c2 = st.columns([3, 1])
    with c1:
        ticker = st.text_input("NSE / ticker", key="alpha_ai_ticker").strip()
    with c2:
        horizon = st.selectbox("Horizon focus", ["1 Year", "3 Years", "5 Years"], index=1)

    if not st.button("Generate Alpha AI Report", type="primary", key="alpha_ai_run"):
        st.info("Enter a symbol (e.g. **TCS**, **HDFCBANK**, **RELIANCE**) and generate a full 18-step report.")
        if is_india_market(market):
            with st.expander("Ticker help"):
                st.markdown(indian_ticker_help())
        return

    if not ticker:
        st.error("Enter a ticker symbol.")
        return

    with st.spinner(f"Building institutional report for {ticker}…"):
        try:
            report = build_alpha_ai_report(ticker, market=market, period=period)
        except Exception as exc:
            st.error(f"Report failed: {exc}")
            return

    color = REC_COLORS.get(report.verdict.upper().replace(" ", " "), "#ffd600")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Price", format_price(report.price, report.symbol) if report.price else "—")
    m2.metric("Investment Score", f"{report.overall_score}/100")
    m3.markdown(
        f"<p style='margin:0;color:#aaa;font-size:0.85rem'>Grade</p>"
        f"<p style='font-size:1.3rem'>{_stars(report.investment_grade_stars)}</p>",
        unsafe_allow_html=True,
    )
    m4.markdown(
        f"<p style='margin:0;color:#aaa;font-size:0.85rem'>Verdict</p>"
        f"<p style='font-size:1.2rem;font-weight:700;color:{color}'>{report.verdict}</p>",
        unsafe_allow_html=True,
    )
    st.caption(f"{report.name} · {report.sector} · Generated {report.generated_at}")

    if report.data_gaps:
        with st.expander("⚠️ Data gaps (not fabricated)", expanded=False):
            for g in report.data_gaps:
                st.markdown(f"- {g}")

    st.markdown("### 1 · Business Overview")
    st.markdown(report.business_overview)

    st.markdown("### 2 · Financial Health")
    st.dataframe(
        [{"Metric": m.name, "Value": m.value, "Rating": m.rating, "Note": m.note} for m in report.financial_metrics],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### 3 · Valuation")
    st.markdown(f"**{report.valuation_verdict}**")
    st.markdown(report.valuation_detail)

    st.markdown("### 4 · Technical Analysis")
    st.markdown(report.technical_summary)
    st.caption(f"Swing: {report.swing_setup} · Long-term: {report.long_term_setup} · Risk: **{report.technical_risk}**")

    st.markdown("### 5 · Growth Analysis")
    st.markdown(report.growth_notes)

    st.markdown("### 6 · Competitive Moat")
    if report.moat_score is not None:
        st.metric("Moat Score (ESTIMATE)", f"{report.moat_score:.1f}/10")
    st.caption(report.moat_detail)

    st.markdown("### 7 · Risk Analysis")
    for r in report.risks:
        st.markdown(f"- **{r.category}** ({r.level}): {r.detail}")

    st.markdown("### 8 · Macro")
    st.markdown(report.macro_summary)

    st.markdown("### 9 · News & Events")
    st.markdown(report.news_summary)

    st.markdown("### 10 · AI Prediction (probabilities)")
    if report.probabilities:
        cols = st.columns(len(report.probabilities))
        for col, (k, v) in zip(cols, report.probabilities.items()):
            col.metric(k, f"{v:.0f}%")
    st.caption(f"Model confidence (ESTIMATE): **{report.prediction_confidence}%**")

    st.markdown("### 11 · Entry Strategy")
    st.markdown(report.entry_strategy)

    st.markdown("### 12 · Portfolio Impact")
    st.markdown(report.portfolio_impact)
    if report.suggested_weight_pct is not None:
        st.metric("Suggested max weight", f"{report.suggested_weight_pct:.0f}%")

    st.markdown("### 13 · Scenarios")
    for s in report.scenarios:
        prob = f"{s.probability_pct:.0f}%" if s.probability_pct is not None else "—"
        st.markdown(f"**{s.name}** ({prob}): {s.description}")

    st.markdown("### 14 · Expected CAGR")
    st.markdown(report.cagr_notes)

    st.markdown("### 15 · Red Flags")
    for f in report.red_flags:
        st.markdown(f"- {f}")

    st.markdown("### 16 · Quality Score")
    qcols = st.columns(4)
    for i, (k, v) in enumerate(report.quality_scores.items()):
        qcols[i % 4].metric(k, f"{v:.0f}")
    st.caption(f"Overall **{report.overall_score}/100** — {report.score_breakdown}")

    st.markdown("### 17 · Investment Verdict")
    st.markdown(f"**{report.verdict}** · {_stars(report.investment_grade_stars)} · Focus horizon: **{horizon}**")
    for h, rec in report.horizons.items():
        st.caption(f"{h}: {rec}")

    st.markdown("### 18 · Action Plan")
    st.markdown(report.action_plan)

    st.divider()
    st.caption(
        "Alpha AI uses Yahoo/NSE feeds + internal models. "
        "Verify all numbers in annual reports before investing."
    )
