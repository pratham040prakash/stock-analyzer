"""Global Markets tab — world indices and India impact."""

from __future__ import annotations

from datetime import timedelta

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from analyzer.global_impact import build_india_impact_report
from analyzer.global_markets import WORLD_INDICES, build_global_heatmap_df, fetch_intraday_5m
from analyzer.india_macro import build_india_macro_snapshot
from analyzer.intraday_data import market_session_status
from ui.charts import global_normalized_chart
from ui.components.india_macro import render_india_macro_strip
from ui.theme import GLOBAL_BIAS_COLORS


def global_markets_live_body() -> None:
    with st.spinner("Pulling world markets..."):
        report = build_india_impact_report()

    session = market_session_status()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("NSE session", session["status"])
    s2.caption(session.get("next_session", ""))
    s3.caption(f"Last updated: **{report.fetched_at}**")
    s4.caption("Auto-refresh: **30 sec**")

    if not session["is_open"]:
        st.info(
            f"**Indian market closed** — bias below is for the **next session** "
            f"({session.get('next_session', '')}). Global markets still update live."
        )

    st.caption(f"Data as of **{report.fetched_at}**")

    bias_color = GLOBAL_BIAS_COLORS.get(report.predicted_nifty_bias, "#ffd600")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f"<div style='padding:12px;border-radius:8px;background:#1e1e1e;text-align:center'>"
        f"<p style='margin:0;color:#aaa;font-size:0.8rem'>India bias</p>"
        f"<p style='margin:0;font-size:1.5rem;font-weight:700;color:{bias_color}'>"
        f"{report.predicted_nifty_bias}</p></div>",
        unsafe_allow_html=True,
    )
    c2.metric("Spillover score", f"{report.spillover_score:+.0f}")
    c3.metric("Predicted Nifty move", f"{report.predicted_move_pct:+.2f}%")
    c4.metric("Confidence", report.confidence.title())

    st.markdown(report.narrative)
    st.info(f"**What to do in India:** {report.india_action} · {report.ce_pe_hint}")

    try:
        macro = build_india_macro_snapshot()
        render_india_macro_strip(macro)
    except Exception:
        pass

    if report.drivers:
        st.markdown("**Global drivers affecting India:**")
        for driver in report.drivers:
            st.markdown(f"- {driver}")

    st.divider()
    st.subheader("🌍 World markets snapshot")
    heat = build_global_heatmap_df(report.global_snapshot.quotes)

    def color_pct(val):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            v = float(val)
            if v > 0.3:
                return "background-color: #1b5e20; color: white"
            if v < -0.3:
                return "background-color: #b71c1c; color: white"
        except (TypeError, ValueError):
            pass
        return ""

    styled = heat.style.map(color_pct, subset=["1D %", "5m %"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    if report.global_snapshot.errors:
        with st.expander("Fetch warnings"):
            for err in report.global_snapshot.errors:
                st.caption(err)

    st.divider()
    st.subheader("🔗 Correlation with Nifty (60 days)")
    if report.correlations:
        corr_df = pd.DataFrame([
            {
                "Market": c.market,
                "Correlation": c.correlation_60d,
                "Beta": c.beta_60d,
                "Latest 1D %": c.latest_1d_pct,
            }
            for c in report.correlations
        ])
        st.dataframe(corr_df, use_container_width=True, hide_index=True)

        fig_c = go.Figure(go.Bar(
            x=[c.market for c in report.correlations[:10]],
            y=[c.correlation_60d for c in report.correlations[:10]],
            marker_color=[
                "#00c853" if c.correlation_60d > 0 else "#d50000"
                for c in report.correlations[:10]
            ],
        ))
        fig_c.update_layout(
            height=320, template="plotly_dark",
            title="Top correlations with Nifty 50",
            yaxis_title="Correlation",
        )
        st.plotly_chart(fig_c, use_container_width=True)

    st.divider()
    st.subheader("📈 Global vs India (1 month)")
    label_map = {s: n for s, n, _, _ in WORLD_INDICES}
    chart_syms = ["^NSEI", "^GSPC", "^IXIC", "^HSI", "^N225", "CL=F", "INR=X"]
    st.plotly_chart(global_normalized_chart(chart_syms, label_map, "1mo"), use_container_width=True)

    st.divider()
    st.subheader("⏱️ Intraday (5m) — US & India")
    ic1, ic2 = st.columns(2)
    with ic1:
        try:
            us = fetch_intraday_5m("^GSPC")
            if not us.empty:
                st.plotly_chart(
                    go.Figure(go.Scatter(x=us.index, y=us["Close"], name="S&P 500")).update_layout(
                        height=280, template="plotly_dark", title="S&P 500 (5m)",
                    ),
                    use_container_width=True,
                )
        except Exception as exc:
            st.caption(f"S&P 5m: {exc}")
    with ic2:
        try:
            nin = fetch_intraday_5m("^NSEI")
            if not nin.empty:
                st.plotly_chart(
                    go.Figure(go.Scatter(x=nin.index, y=nin["Close"], name="Nifty")).update_layout(
                        height=280, template="plotly_dark", title="Nifty 50 (5m)",
                    ),
                    use_container_width=True,
                )
        except Exception as exc:
            st.caption(f"Nifty 5m: {exc}")

    st.markdown("**How prediction works:**")
    for risk in report.risks:
        st.markdown(f"- {risk}")
    st.caption(
        "Spillover = Σ(beta × global % move × correlation weight). "
        "Positive score → bullish Nifty bias; negative → bearish. Not financial advice."
    )


@st.fragment(run_every=timedelta(seconds=30))
def global_markets_live() -> None:
    global_markets_live_body()


def render_global_markets() -> None:
    st.subheader("Global Markets → India Impact")
    st.markdown(
        "Tracks **US, Europe, Asia, oil, USD/INR** every **30 seconds**, measures correlation with "
        "**Nifty**, and predicts **bullish/bearish** bias for Indian stocks."
    )
    auto = st.checkbox("Auto-refresh (30 sec)", value=True, key="global_auto")
    if st.button("Refresh now", key="global_refresh"):
        st.rerun()
    if auto:
        global_markets_live()
    else:
        with st.spinner("Loading..."):
            global_markets_live_body()
