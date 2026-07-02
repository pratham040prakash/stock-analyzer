"""Intraday verdict and candle narrative UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.candle_narrative import LiveChartVerdict
from analyzer.intraday_trade_plan import IntradayTradePlan, build_intraday_trade_plan, discipline_intro
from analyzer.nse_options import chain_summary_markdown
from ui.theme import INTRADAY_SETUP_COLORS, OPTIONS_COLORS, SIGNAL_ICONS


def render_nse_chain_table(chain, action: str) -> None:
    """Show NSE CE/PE table (filtered by suggested side)."""
    show_ce = "CE" in action
    show_pe = "PE" in action
    if action in ("NO TRADE", "WAIT"):
        show_ce = show_pe = True

    rows = []
    strike_set = sorted({leg.strike for leg in chain.legs})
    ce_map = {leg.strike: leg for leg in chain.ce_legs}
    pe_map = {leg.strike: leg for leg in chain.pe_legs}

    for strike in strike_set:
        row = {"Strike": f"{strike:g}"}
        if show_ce:
            ce = ce_map.get(strike)
            if ce:
                row["CE LTP"] = f"₹{ce.ltp or 0:,.2f}"
                row["CE OI"] = f"{ce.open_interest:,}"
                row["CE Vol"] = f"{ce.volume:,}"
                row["CE IV%"] = f"{ce.iv:.1f}" if ce.iv else "—"
        if show_pe:
            pe = pe_map.get(strike)
            if pe:
                row["PE LTP"] = f"₹{pe.ltp or 0:,.2f}"
                row["PE OI"] = f"{pe.open_interest:,}"
                row["PE Vol"] = f"{pe.volume:,}"
                row["PE IV%"] = f"{pe.iv:.1f}" if pe.iv else "—"
        rows.append(row)

    with st.expander(f"Full NSE chain — {chain.expiry} ({len(strike_set)} strikes)", expanded=False):
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_options_verdict(options, show_nse_table: bool = True) -> None:
    """CE / PE options suggestion from candles + NSE live chain."""
    color = OPTIONS_COLORS.get(options.action, "#ffd600")
    st.markdown("### 🎯 Options suggestion (CE / PE)")
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f"<div style='padding:14px;border-radius:8px;background:#1a237e;text-align:center;border:2px solid {color}'>"
        f"<p style='margin:0;color:#aaa;font-size:0.85rem'>CE / PE Action</p>"
        f"<p style='margin:0;font-size:1.7rem;font-weight:800;color:{color}'>{options.action}</p></div>",
        unsafe_allow_html=True,
    )
    c2.metric("Confidence", options.confidence.title())
    c3.caption("**CE** = Call · **PE** = Put · Data: [NSE India](https://www.nseindia.com/)")

    st.markdown(options.summary)
    st.info(f"**Strike rule:** {options.strike_hint}")
    st.warning(f"**Invalidation:** {options.invalidation}")

    if getattr(options, "nse_chain", None):
        chain = options.nse_chain
        st.markdown("#### 📡 NSE live option chain")
        st.markdown(chain_summary_markdown(chain))
        if options.nse_picks:
            st.markdown("**Recommended contracts to buy (from NSE data + candles):**")
            for pick in options.nse_picks:
                leg = pick.leg
                st.success(
                    f"**#{pick.rank} {leg.option_type} {leg.strike:g}** · Exp {leg.expiry} · "
                    f"**LTP ₹{leg.ltp or 0:,.2f}** · Bid ₹{leg.bid or 0:,.2f} / Ask ₹{leg.ask or 0:,.2f}\n\n"
                    f"{pick.reason}"
                )
        elif options.action not in ("NO TRADE", "WAIT"):
            st.caption("No liquid strikes matched filters — widen search or pick next expiry on NSE.")

        if show_nse_table and chain:
            render_nse_chain_table(chain, options.action)

    elif getattr(options, "nse_error", None):
        st.caption(f"NSE option chain unavailable: {options.nse_error}")

    if options.reasons:
        with st.expander("Why this CE/PE?", expanded=True):
            for reason in options.reasons:
                st.markdown(f"- {reason}")
    with st.expander("Options risk reminders"):
        for note in options.risk_notes:
            st.markdown(f"- {note}")


def render_entry_exit_plan(
    plan: IntradayTradePlan,
    *,
    show_capital_hint: bool = True,
) -> None:
    """Entry/exit discipline card — exits defined before entry."""
    st.markdown("### 🚪 Entry & exit plan (before you trade)")
    st.caption(discipline_intro())

    if plan.can_enter:
        st.success(plan.summary)
    elif plan.side != "FLAT":
        st.error(plan.summary)
    else:
        st.warning(plan.skip_reason or plan.summary)

    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Entry", f"₹{plan.entry:,.2f}" if plan.entry else "—")
    e2.metric("Stop (full exit)", f"₹{plan.stop_loss:,.2f}" if plan.stop_loss else "—")
    e3.metric("Target", f"₹{plan.target:,.2f}" if plan.target else "—")
    e4.metric("R:R", f"{plan.risk_reward_ratio:.1f}×" if plan.risk_reward_ratio else "—")

    if plan.risk_per_share is not None:
        st.caption(
            f"Risk **₹{plan.risk_per_share:,.2f}/share** "
            f"({plan.risk_pct_of_price:.1f}% of entry)"
            + (
                f" · Size hint **{plan.suggested_shares}** shares "
                f"(max loss ≈ ₹{plan.max_loss_inr:,.0f})"
                if plan.suggested_shares and plan.max_loss_inr and show_capital_hint
                else ""
            )
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Entry rules**")
        for rule in plan.entry_rules:
            st.markdown(f"- {rule}")
    with c2:
        st.markdown("**Exit rules** (more important than entry)")
        for rule in plan.exit_rules:
            st.markdown(f"- {rule}")


def render_live_verdict(
    verdict: LiveChartVerdict,
    *,
    account_inr: float | None = None,
    max_risk_pct: float = 1.0,
    max_trades: int = 3,
    show_trade_log: bool = True,
) -> "IntradayTradePlan | None":
    """Buy/sell + CE/PE suggestions from current candle. Returns trade plan if built."""
    if verdict.options:
        render_options_verdict(verdict.options)

    st.markdown("### 📈 Equity suggestion (cash / MIS)")
    color = INTRADAY_SETUP_COLORS.get(verdict.action, "#ffd600")
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f"<div style='padding:14px;border-radius:8px;background:#1e1e1e;text-align:center'>"
        f"<p style='margin:0;color:#aaa;font-size:0.85rem'>Action</p>"
        f"<p style='margin:0;font-size:1.6rem;font-weight:700;color:{color}'>{verdict.action}</p></div>",
        unsafe_allow_html=True,
    )
    c2.metric("Confidence", verdict.confidence.title())
    current = verdict.current_candle
    c3.metric("Current candle", current.candle_type if current else "—")

    st.markdown(verdict.summary)
    if verdict.reasons:
        with st.expander("Why this suggestion?", expanded=True):
            for reason in verdict.reasons:
                st.markdown(f"- {reason}")

    plan = build_intraday_trade_plan(
        verdict.action,
        verdict.entry,
        verdict.stop_loss,
        verdict.target,
        account_inr=account_inr,
        max_risk_pct=max_risk_pct,
        entry_reasons=verdict.reasons,
    )
    render_entry_exit_plan(plan)

    if verdict.action == "WAIT":
        st.warning("Wait for a clearer candle (engulfing, marubozu, or OR breakout) before entering.")

    if show_trade_log:
        from ui.components.intraday_journal import render_log_trade_panel

        render_log_trade_panel(
            verdict.ticker,
            verdict.action,
            entry=verdict.entry,
            stop_loss=verdict.stop_loss,
            target=verdict.target,
            price_at_log=verdict.intraday.last_price if verdict.intraday else None,
            suggested_shares=plan.suggested_shares,
            max_trades=max_trades,
        )

    return plan


def render_candle_stories(verdict: LiveChartVerdict) -> None:
    """Per-candle narrative table and session story."""
    st.subheader("📖 Candle stories")
    st.markdown(verdict.session_story)

    if verdict.current_candle:
        st.markdown("#### Current (live) candle")
        icon = SIGNAL_ICONS.get(verdict.current_candle.bias, "⚪")
        st.markdown(f"{icon} {verdict.current_candle.story}")

    rows = []
    for candle in reversed(verdict.recent_candles):
        rows.append({
            "Time": candle.time,
            "Type": candle.candle_type,
            "O": f"₹{candle.open:,.2f}",
            "H": f"₹{candle.high:,.2f}",
            "L": f"₹{candle.low:,.2f}",
            "C": f"₹{candle.close:,.2f}",
            "Chg%": f"{candle.change_pct:+.2f}%",
            "Bias": candle.bias.upper(),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("Full story for each candle", expanded=False):
        for candle in verdict.recent_candles:
            icon = SIGNAL_ICONS.get(candle.bias, "⚪")
            st.markdown(f"{icon} {candle.story}")
            st.divider()
