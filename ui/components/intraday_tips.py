"""UI — top 10 intraday beginner tips."""

from __future__ import annotations

import streamlit as st

from analyzer.intraday_beginner_tips import (
    SessionTimingAdvice,
    build_capital_budget,
    session_timing_advice,
    ten_intraday_tips,
    tips_summary_markdown,
)


def render_session_timing_banner(advice: SessionTimingAdvice | None = None) -> SessionTimingAdvice:
    advice = advice or session_timing_advice()
    if advice.phase in ("core", "pre_open"):
        st.info(f"**{advice.headline}** — {advice.detail}")
    elif advice.prefer_exit or advice.phase == "opening":
        st.warning(f"**{advice.headline}** — {advice.detail}")
    else:
        st.caption(f"**{advice.headline}** — {advice.detail}")
    return advice


def render_capital_budget_panel(
    total_capital: float,
    allocation_pct: float,
    max_risk_pct: float,
    max_concurrent_trades: int,
) -> float:
    """Show MIS pool sizing; returns allocated INR for trade plans."""
    budget = build_capital_budget(
        total_capital,
        allocation_pct=allocation_pct,
        max_risk_pct=max_risk_pct,
        max_concurrent_trades=max_concurrent_trades,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total capital", f"₹{budget.total_capital_inr:,.0f}")
    c2.metric("MIS pool today", f"₹{budget.allocated_inr:,.0f}")
    c3.metric("Per trade budget", f"₹{budget.per_trade_budget_inr:,.0f}")
    c4.metric("Max risk/trade", f"₹{budget.max_risk_per_trade_inr:,.0f}")
    for note in budget.notes[:2]:
        st.caption(note)
    return budget.allocated_inr


def render_ten_tips_expander(expanded: bool = False) -> None:
    with st.expander("📋 Top 10 intraday tips (beginners)", expanded=expanded):
        st.caption(tips_summary_markdown())
        for tip in ten_intraday_tips():
            st.markdown(f"**{tip.number}. {tip.title}** — {tip.summary}")
            st.caption(f"App: {tip.app_help}")
