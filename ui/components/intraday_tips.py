"""UI — top 10 intraday beginner tips."""

from __future__ import annotations

import streamlit as st

from analyzer.intraday_beginner_tips import (
    PHASE_LABELS,
    SessionTimingAdvice,
    build_capital_budget,
    checklist_phase_for_session,
    daily_mis_checklist_items,
    session_timing_advice,
    ten_intraday_tips,
    tips_summary_markdown,
)
from analyzer.market_session import market_session_status


def _checklist_storage_key() -> str:
    return f"mis_checklist_{market_session_status().get('date', 'today')}"


def render_daily_mis_checklist(advice: SessionTimingAdvice | None = None) -> None:
    """Interactive daily MIS checklist — tick steps as you complete them."""
    advice = advice or session_timing_advice()
    current_phase = checklist_phase_for_session(advice)
    items = daily_mis_checklist_items()
    storage = _checklist_storage_key()
    if storage not in st.session_state:
        st.session_state[storage] = {}

    done_map: dict = st.session_state[storage]
    done_count = sum(1 for it in items if done_map.get(it.id, False))

    with st.expander(
        f"✅ Daily MIS checklist ({done_count}/{len(items)} done)",
        expanded=advice.phase in ("pre_open", "opening", "weekend", "after_hours"),
    ):
        st.caption(
            f"**Now:** {advice.headline} · Follow in order — each step maps to a beginner tip (#)."
        )
        _, c2 = st.columns([3, 1])
        with c2:
            if st.button("Reset today's checks", key="mis_checklist_reset"):
                st.session_state[storage] = {}
                st.rerun()

        by_phase: dict[str, list] = {}
        for item in items:
            by_phase.setdefault(item.phase, []).append(item)

        for phase, phase_items in by_phase.items():
            highlight = " ← **you are here**" if phase == current_phase else ""
            st.markdown(f"**{PHASE_LABELS.get(phase, phase)}**{highlight}")
            for item in phase_items:
                row_l, row_r = st.columns([5, 1])
                with row_l:
                    checked = st.checkbox(
                        f"**Tip {item.tip_number}:** {item.label}",
                        value=bool(done_map.get(item.id, False)),
                        key=f"mis_chk_{storage}_{item.id}",
                    )
                    done_map[item.id] = checked
                    st.caption(f"→ {item.action}")
                with row_r:
                    if item.link_tab and item.link_label:
                        if st.button(
                            item.link_label,
                            key=f"mis_link_{storage}_{item.id}",
                            use_container_width=True,
                        ):
                            st.session_state["nav_tab"] = item.link_tab
                            if item.focus_key:
                                st.session_state[item.focus_key] = True
                            st.rerun()
            st.divider()

        st.session_state[storage] = done_map
        done_count = sum(1 for it in items if done_map.get(it.id, False))
        if done_count == len(items):
            st.success("All steps done for today — well prepared.")
        elif done_count >= len(items) - 2:
            st.info(f"Almost there — {len(items) - done_count} step(s) left.")


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
