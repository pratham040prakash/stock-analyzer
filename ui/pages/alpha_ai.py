"""Alpha AI v3.0 — institutional equity research tab."""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

from analyzer.alpha_ai_report import build_alpha_ai_report, compare_alpha_reports
from analyzer.alpha_ai_export import report_to_markdown, report_to_pdf_bytes
from analyzer.alpha_ai_llm import llm_enabled
from analyzer.india import indian_ticker_help
from analyzer.markets import format_price, is_india_market
from ui.theme import MOBILE_CSS, REC_COLORS


def _stars(n: int) -> str:
    return "★" * n + "☆" * (5 - n)


def _stars_10(score: float) -> str:
    return _stars(max(0, min(5, int(round(score / 2)))))


def _radar_chart(checklist: dict[str, float]) -> go.Figure:
    labels = [k for k in checklist if k != "Overall"]
    values = [checklist[k] for k in labels]
    labels.append(labels[0])
    values.append(values[0])
    fig = go.Figure(
        data=go.Scatterpolar(
            r=values,
            theta=labels,
            fill="toself",
            fillcolor="rgba(0, 200, 83, 0.2)",
            line=dict(color="#00c853"),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=360,
        margin=dict(l=40, r=40, t=30, b=30),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _render_executive_summary(report, horizon: str) -> None:
    color = REC_COLORS.get(report.recommendation.upper().replace(" ", " "), "#ffd600")
    st.markdown("## Executive Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investment Score", f"{report.overall_score}/100")
    c2.markdown(
        f"<p style='margin:0;color:#aaa;font-size:0.85rem'>Grade</p>"
        f"<p style='font-size:1.4rem'>{_stars(report.investment_grade_stars)}</p>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"<p style='margin:0;color:#aaa;font-size:0.85rem'>Recommendation</p>"
        f"<p style='font-size:1.2rem;font-weight:700;color:{color}'>{report.recommendation}</p>",
        unsafe_allow_html=True,
    )
    c4.metric("Confidence", f"{report.confidence_pct or 0:.0f}%")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Risk Level", report.risk_level)
    d2.metric("Horizon Focus", horizon)
    d3.metric("Price", format_price(report.price, report.symbol) if report.price else "—")
    if report.expected_cagr:
        d4.metric("3Y CAGR (est.)", report.expected_cagr.get("3 Years", "N/A")[:20])
    st.caption(f"{report.name} · {report.sector} · {report.generated_at}")


def _render_snapshot(report) -> None:
    st.markdown("## Quick Snapshot")
    cols = st.columns(4)
    for i, cat in enumerate(report.snapshot):
        with cols[i % 4]:
            st.markdown(f"**{cat.name}**")
            st.markdown(f"{cat.score:.1f}/10 · {_stars_10(cat.score)}")


def _render_buy_decision(report) -> None:
    st.markdown("## Buy Decision")
    badge_color = {"YES": "#00c853", "NO": "#ff5252", "WAIT": "#ffd600"}.get(report.buy_decision, "#aaa")
    st.markdown(
        f"<p style='font-size:1.5rem;font-weight:700;color:{badge_color}'>Should Buy? {report.buy_decision}</p>",
        unsafe_allow_html=True,
    )
    st.markdown(report.buy_decision_why)


def _render_entry(report) -> None:
    st.markdown("## Entry Strategy")
    e = report.entry
    if not e:
        st.markdown(report.entry_strategy)
        return
    c1, c2 = st.columns(2)
    c1.markdown(f"**Ideal buy zone:** {e.ideal_buy_zone}")
    c1.markdown(f"**Aggressive zone:** {e.aggressive_buy_zone}")
    c1.markdown(f"**Stop loss:** {e.stop_loss}")
    c1.markdown(f"**Risk/Reward:** {e.risk_reward}")
    c2.markdown(f"**Support:** {', '.join(e.support_levels)}")
    c2.markdown(f"**Resistance:** {', '.join(e.resistance_levels)}")
    c2.markdown(f"**Target 1 / 2 / 3:** {e.target_1} · {e.target_2} · {e.target_3}")
    c2.markdown(f"**SIP:** {e.sip_entry}")
    c2.markdown(f"**Lump sum:** {e.lump_sum_entry}")
    if getattr(e, "or_confirm_note", None):
        st.info(e.or_confirm_note)


def _render_export_buttons(report) -> None:
    md = report_to_markdown(report)
    st.download_button(
        "Download Markdown",
        md,
        file_name=f"alpha_ai_{report.symbol.replace('.', '_')}.md",
        mime="text/markdown",
        key=f"dl_md_{report.symbol}",
    )
    try:
        pdf = report_to_pdf_bytes(report)
        st.download_button(
            "Download PDF",
            pdf,
            file_name=f"alpha_ai_{report.symbol.replace('.', '_')}.pdf",
            mime="application/pdf",
            key=f"dl_pdf_{report.symbol}",
        )
    except RuntimeError as exc:
        st.caption(str(exc))


def _render_report_body(report) -> None:
    st.caption(f"Report mode: **{getattr(report, 'report_mode', 'equity')}**")
    if getattr(report, "section_sources", None):
        with st.expander("Data sources by section", expanded=False):
            for sec, srcs in report.section_sources.items():
                st.markdown(f"- **{sec}:** {', '.join(srcs)}")
    if llm_enabled():
        st.caption("LLM narrative: enabled (OPENAI_API_KEY)")
    if report.llm_narrative:
        st.markdown("### AI Narrative")
        st.markdown(report.llm_narrative)

    _render_export_buttons(report)

    if report.data_gaps:
        with st.expander("Data gaps (not fabricated)", expanded=False):
            for g in report.data_gaps:
                st.markdown(f"- {g}")

    _render_executive_summary(report, st.session_state.get("alpha_ai_horizon", "3 Years"))
    _render_snapshot(report)
    _render_buy_decision(report)
    _render_entry(report)

    with st.expander("Business Analysis", expanded=False):
        st.markdown(report.business_overview)

    with st.expander("Financial Analysis", expanded=False):
        st.dataframe(
            [{"Metric": m.name, "Value": m.value, "Rating": m.rating, "Note": m.note} for m in report.financial_metrics],
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(report.financial_analysis)

    with st.expander("Valuation", expanded=False):
        st.markdown(f"**{report.valuation_verdict}**")
        st.markdown(report.valuation_detail)

    with st.expander("Technical Analysis", expanded=False):
        st.markdown(report.technical_analysis)
        st.caption(f"Swing: {report.swing_setup} · Long-term: {report.long_term_setup}")

    with st.expander("News & Sentiment", expanded=False):
        st.markdown(report.news_sentiment)

    with st.expander("Risk Analysis", expanded=False):
        for r in report.risks:
            st.markdown(f"- **{r.category}** ({r.level}): {r.detail}")

    if report.red_flags:
        st.markdown("## AI Red Flags")
        for flag in report.red_flags:
            st.warning(flag)

    with st.expander("Competitive Moat", expanded=False):
        if report.moat_score is not None:
            st.metric("Moat Score (ESTIMATE)", f"{report.moat_score:.1f}/10")
        st.caption(report.moat_detail)
        if report.moat_dimensions:
            st.dataframe(
                [{"Dimension": n, "Score (0–10)": s} for n, s in report.moat_dimensions],
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Scenario Analysis", expanded=False):
        for s in report.scenarios:
            prob = f"{s.probability_pct:.0f}%" if s.probability_pct is not None else "—"
            st.markdown(
                f"**{s.name}** ({prob}) — Target {s.target_price} · CAGR {s.expected_cagr}\n\n{s.description}"
            )

    with st.expander("Macro Context", expanded=False):
        st.markdown(report.macro_summary)

    with st.expander("Portfolio Impact", expanded=False):
        st.markdown(report.portfolio_impact)
        if report.suggested_weight_pct is not None:
            st.metric("Suggested max weight", f"{report.suggested_weight_pct:.0f}%")
        if report.portfolio_allocation_options:
            st.caption(
                "Allocation options (ESTIMATE): "
                + " · ".join(f"{x:.0f}%" for x in report.portfolio_allocation_options)
            )

    st.markdown("## AI Checklist")
    if report.checklist_scores:
        st.plotly_chart(_radar_chart(report.checklist_scores), use_container_width=True)
        qcols = st.columns(4)
        for i, (k, v) in enumerate(report.checklist_scores.items()):
            qcols[i % 4].metric(k, f"{v:.0f}")

    st.markdown("## Final Verdict")
    st.markdown(report.final_verdict_detail)
    st.markdown(report.action_plan)
    st.caption(f"Score breakdown: {report.score_breakdown}")


def render_alpha_ai(market: str, period: str) -> None:
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    st.subheader("Alpha AI v3.0 — Institutional Research")
    st.caption(
        "Decision support · FACT / ASSUMPTION / ESTIMATE labeled · "
        "Goal: preserve capital + compound toward **₹10 Cr** · Not financial advice."
    )

    default = "TCS" if is_india_market(market) else "AAPL"
    if "alpha_ai_ticker" not in st.session_state:
        st.session_state["alpha_ai_ticker"] = default

    mode = st.radio(
        "Mode",
        ["Single Stock", "Compare", "Portfolio"],
        horizontal=True,
        key="alpha_ai_mode",
    )

    c1, c2 = st.columns([3, 1])
    with c1:
        if mode == "Portfolio":
            ticker = st.text_input("Analyze vs your portfolio", key="alpha_ai_ticker", value=default).strip()
            compare_raw = ""
            portfolio_mode = True
        elif mode == "Single Stock":
            ticker = st.text_input("NSE / ticker", key="alpha_ai_ticker").strip()
            compare_raw = ""
            portfolio_mode = False
        else:
            compare_raw = st.text_input(
                "Compare tickers (comma-separated, max 4)",
                value="TCS, INFY, HCLTECH",
                key="alpha_ai_compare",
            ).strip()
            ticker = ""
            portfolio_mode = False
    with c2:
        horizon = st.selectbox("Horizon focus", ["Swing", "6 Months", "1 Year", "3 Years", "5 Years", "10 Years"], index=3)
        st.session_state["alpha_ai_horizon"] = horizon

    if not st.button("Generate Alpha AI Report", type="primary", key="alpha_ai_run"):
        st.info("Enter a symbol and generate a full v3.0 institutional report — executive summary first.")
        if is_india_market(market):
            with st.expander("Ticker help"):
                st.markdown(indian_ticker_help())
        return

    if mode == "Compare":
        symbols = [s.strip() for s in compare_raw.split(",") if s.strip()][:4]
        if len(symbols) < 2:
            st.error("Enter at least two tickers to compare.")
            return
        reports = []
        with st.spinner("Building comparison…"):
            for sym in symbols:
                try:
                    reports.append(build_alpha_ai_report(sym, market=market, period=period))
                except Exception as exc:
                    st.error(f"{sym}: {exc}")
        if len(reports) < 2:
            return
        ranked = compare_alpha_reports(reports)
        st.markdown("## Comparison Rankings")
        st.dataframe(
            [{"Rank": i + 1, "Symbol": s, "Score": sc, "Recommendation": rec} for i, (s, sc, rec) in enumerate(ranked)],
            use_container_width=True,
            hide_index=True,
        )
        st.success(f"**Winner:** {ranked[0][0]} (score {ranked[0][1]}/100) — {ranked[0][2]}")
        for r in sorted(reports, key=lambda x: x.overall_score, reverse=True):
            with st.expander(f"{r.name} ({r.symbol}) — {r.overall_score}/100 · {r.recommendation}"):
                _render_report_body(r)
        return

    if not ticker:
        st.error("Enter a ticker symbol.")
        return

    with st.spinner(f"Building Alpha AI v3.0 report for {ticker}…"):
        try:
            report = build_alpha_ai_report(
                ticker, market=market, period=period, portfolio_mode=portfolio_mode
            )
        except Exception as exc:
            st.error(f"Report failed: {exc}")
            return

    _render_report_body(report)

    st.divider()
    st.caption("Alpha AI uses Yahoo/NSE feeds + internal models. Verify all numbers in annual reports before investing.")
