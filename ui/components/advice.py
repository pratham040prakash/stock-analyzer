"""Investment advice and signal display components."""

from __future__ import annotations

import streamlit as st

from analyzer.advisor import InvestmentAdvice
from analyzer.signals import AnalysisResult
from analyzer.varsity_knowledge import format_signal_context
from ui.theme import ACTION_COLORS, SIGNAL_ICONS


def render_advice(advice: InvestmentAdvice) -> None:
    color = ACTION_COLORS.get(advice.final_action, "#ffd600")
    st.markdown("### 💡 Investment Suggestion")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f"<div style='padding:12px;border-radius:8px;background:#1e1e1e;text-align:center'>"
        f"<p style='margin:0;color:#aaa;font-size:0.8rem'>Final Action</p>"
        f"<p style='margin:0;font-size:1.5rem;font-weight:700;color:{color}'>{advice.final_action}</p></div>",
        unsafe_allow_html=True,
    )
    c2.metric("Conviction", advice.conviction.title())
    c3.metric("Time Horizon", advice.time_horizon.split("—")[0].strip())
    c4.metric("Risk/Reward", advice.risk_reward)

    st.markdown(advice.summary)
    st.markdown(f"**Position sizing:** {advice.position_hint}")
    st.markdown(
        f"**Levels:** Entry {advice.entry_zone} · Stop {advice.stop_loss} · Target {advice.target}"
    )

    with st.expander("✅ Bullish factors", expanded=True):
        if advice.bullish_factors:
            for factor in advice.bullish_factors:
                st.markdown(f"- {factor}")
        else:
            st.caption("No strong bullish factors identified.")

    with st.expander("⚠️ Bearish factors / concerns"):
        if advice.bearish_factors:
            for factor in advice.bearish_factors:
                st.markdown(f"- {factor}")
        else:
            st.caption("No major bearish factors.")

    with st.expander("📋 Market standards checklist"):
        for label, passed, detail in advice.standards_checklist:
            icon = "✅" if passed else "❌"
            st.markdown(f"{icon} **{label}** — {detail}")

    with st.expander("🛡️ Risk reminders & portfolio rules"):
        for risk in advice.risks:
            st.markdown(f"- {risk}")
        st.markdown("**General rules:**")
        for tip in advice.portfolio_tips:
            st.markdown(f"- {tip}")


def render_signals(result: AnalysisResult) -> None:
    for sig in result.signals:
        icon = SIGNAL_ICONS.get(sig.signal, "⚪")
        score_bar = (sig.score + 1) / 2
        varsity = format_signal_context(sig.name)
        st.markdown(f"**{icon} {sig.name}** — {sig.detail}")
        st.caption(varsity)
        st.progress(score_bar)


def render_fundamentals(fund) -> None:
    for metric in fund.metrics:
        icon = SIGNAL_ICONS.get(metric.signal, "⚪")
        st.markdown(f"**{icon} {metric.name}:** {metric.value} — {metric.detail}")
        st.progress((metric.score + 1) / 2)
