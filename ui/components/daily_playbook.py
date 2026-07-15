"""Daily step-by-step playbook — prominent beginner guide."""

from __future__ import annotations

import streamlit as st

from analyzer.daily_playbook import build_daily_playbook, format_playbook_text
from analyzer.intraday_prefs import load_intraday_prefs, save_intraday_prefs


def render_daily_playbook(*, market: str = "india", key_prefix: str = "playbook") -> None:
    """Your next step + full day routine."""
    prefs = load_intraday_prefs()
    pb = build_daily_playbook(market=market)

    st.markdown("#### 🧭 Your daily guide (step-by-step)")
    goal_inr = pb.daily_profit_target_inr
    st.success(
        f"**Today's realistic goal: +₹{goal_inr:,.0f}** · max loss **₹{pb.max_loss_inr:,.0f}** · "
        f"focus **{pb.focus_symbol or 'set tonight'}** · "
        f"{'✅ may trade' if pb.can_trade_today else '⛔ sit out / WAIT only'}",
        icon="🎯",
    )
    st.info(f"**👉 Next step:** {pb.next_step}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Long-term goal", f"₹{pb.wealth_goal_inr/1e7:.0f} Cr")
    with c2:
        st.metric("Mode", "Equity only" if pb.equity_only else "Equity + options")
    with c3:
        st.metric("Verdict", pb.verdict)

    for w in pb.warnings:
        st.warning(w)

    with st.expander("📋 Full day steps (follow in order)", expanded=True):
        for step in pb.steps:
            if step.status == "blocked":
                st.markdown(f"🚫 ~~{step.window} — {step.title}~~ _(skip: {step.skip_if})_")
                continue
            prefix = "**👉 NOW**" if step.is_current else step.emoji
            st.markdown(f"{prefix} **{step.window}** — {step.title}")
            st.caption(step.action)

        st.divider()
        st.markdown("**Daily rules**")
        for rule in pb.rules:
            st.caption(f"• {rule}")

        st.download_button(
            "Copy guide as text",
            data=format_playbook_text(pb),
            file_name=f"daily-playbook-{pb.trade_date}.txt",
            mime="text/plain",
            key=f"{key_prefix}_dl",
        )

    with st.expander("⚙️ Beginner settings", expanded=False):
        st.caption("Tuned for ₹9k recovery — equity-first, small daily goals.")
        cap = st.number_input(
            "Trading capital (₹)",
            min_value=1000,
            max_value=5_000_000,
            value=int(prefs.capital),
            step=500,
            key=f"{key_prefix}_cap",
        )
        min_pct = st.slider(
            "Daily profit goal %",
            min_value=1.0,
            max_value=5.0,
            value=float(prefs.min_daily_profit_pct),
            step=0.5,
            key=f"{key_prefix}_minpct",
        )
        beginner = st.checkbox("Beginner mode (1 trade max)", value=prefs.beginner_mode, key=f"{key_prefix}_beg")
        equity_only = st.checkbox(
            "Equity only (no index options)",
            value=prefs.equity_only,
            key=f"{key_prefix}_eq",
        )
        if st.button("Save settings", key=f"{key_prefix}_save"):
            prefs.capital = float(cap)
            prefs.min_daily_profit_pct = float(min_pct)
            prefs.target_daily_profit_pct = float(min_pct) * 2
            prefs.stretch_daily_profit_pct = float(min_pct) * 3
            prefs.profit_mode = "conservative"
            prefs.max_trades = 1
            prefs.allocation_pct = 40.0
            prefs.max_risk_pct = 1.0
            prefs.beginner_mode = beginner
            prefs.equity_only = equity_only
            save_intraday_prefs(prefs)
            st.success("Saved — playbook refreshed.")
            st.rerun()
