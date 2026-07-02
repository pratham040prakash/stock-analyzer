"""Pre-market intraday watchlist UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.intraday_beginner_tips import too_many_watchlist_warning
from analyzer.intraday_pulse_source import (
    DEFAULT_INTRADAY_PULSE_PERIOD,
    load_pulse_for_watchlist,
    run_quick_watchlist_scan,
)
from analyzer.intraday_watchlist import build_intraday_watchlist


def render_intraday_watchlist_section(report, *, max_concurrent_trades: int = 2) -> None:
    """Tonight's lean MIS shortlist — entry/stop/target pre-written."""
    wl = build_intraday_watchlist(report)

    st.markdown("#### 🌙 Pre-market intraday watchlist (prepare tonight)")
    st.caption(wl.routine_note)
    c1, c2, c3 = st.columns(3)
    c1.metric("Market bias", wl.market_bias)
    c2.metric("Leading sector", wl.sector_leader)
    c3.metric("Lagging sector", wl.sector_laggard)

    if not wl.picks:
        st.info(
            "No names passed the **5-point checklist** yet (volume, ATR ≥1.5%, RSI/MACD, "
            "pivots, news). Run **Quick scan** above or refresh **Market Pulse** after close."
        )
        st.markdown(
            "**Nightly routine**\n"
            "1. Nifty trend · 2. Sector leaders · 3. Volume shockers · "
            "4. Chart patterns · 5. Liquidity · 6. Earnings/news"
        )
        return

    st.success(f"**{len(wl.picks)}** stocks ready — entry, stop, and target defined for each.")
    over = too_many_watchlist_warning(len(wl.picks), max_concurrent_trades)
    if over:
        st.warning(over)

    table = []
    for p in wl.picks:
        checks = f"{p.checklist.passed}/{p.checklist.total}"
        table.append({
            "Rank": p.rank,
            "Stock": p.nse_symbol,
            "Sector": p.sector[:12],
            "Price": f"₹{p.price:,.0f}",
            "ATR%": f"{p.atr_pct:.1f}" if p.atr_pct else "—",
            "Vol×": f"{p.volume_ratio:.1f}" if p.volume_ratio else "—",
            "RSI": f"{p.rsi:.0f}" if p.rsi else "—",
            "Checks": checks,
            "Entry": f"₹{p.entry:,.0f}",
            "Stop": f"₹{p.stop_loss:,.0f}",
            "Target": f"₹{p.target:,.0f}",
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    for p in wl.picks:
        with st.expander(
            f"#{p.rank} {p.nse_symbol} — prep score {p.prep_score:.0f}",
            expanded=p.rank <= 3,
        ):
            st.caption(p.breakout_note)
            if p.pivot:
                st.caption(
                    f"Pivots: P **₹{p.pivot.pivot:,.0f}** · R1 **₹{p.pivot.r1:,.0f}** · "
                    f"R2 **₹{p.pivot.r2:,.0f}** · S1 **₹{p.pivot.s1:,.0f}** · S2 **₹{p.pivot.s2:,.0f}**"
                )
            st.caption(
                f"20d range: support **₹{p.support:,.0f}** · resistance **₹{p.resistance:,.0f}**"
            )
            st.markdown(f"**Plan:** {p.plan_summary}")
            st.markdown("**Pro checklist**")
            for note in p.checklist.notes:
                st.markdown(f"- {note}")
            if st.button(f"Open {p.nse_symbol} intraday chart", key=f"wl_intra_{p.nse_symbol}"):
                st.session_state["intraday_ticker"] = p.nse_symbol
                st.session_state["intraday_focus_chart"] = True
                st.rerun()

    st.caption(
        "Avoid: tip-chasing, illiquid names, too many stocks, no stop-loss. "
        "**Fewer stocks, better prepared.**"
    )


def render_intraday_watchlist_block(
    market: str,
    *,
    period: str = DEFAULT_INTRADAY_PULSE_PERIOD,
    max_concurrent_trades: int = 2,
) -> None:
    """Watchlist with cache/session load + Quick scan — no Market Pulse tab required."""
    expand = st.session_state.pop("intraday_focus_watchlist", False)
    with st.expander("🌙 Pre-market watchlist", expanded=expand):
        session_report = st.session_state.get("market_pulse_full")
        report, status = load_pulse_for_watchlist(market, period, session_report=session_report)
        if report is not None and status in ("cache_fresh", "cache_stale"):
            st.session_state.setdefault("market_pulse_full", report)

        status_msgs = {
            "session": "Using **current session** Market Pulse data.",
            "cache_fresh": "Loaded from **fresh cache** (no Pulse tab visit needed).",
            "cache_stale": "Loaded from **cached scan** (>15 min old) — Quick scan for latest.",
            "missing": "No scan data yet — tap **Quick scan** (1–2 min).",
        }
        st.caption(status_msgs.get(status, ""))

        c1, c2 = st.columns([3, 1])
        with c2:
            if st.button("Quick scan", type="primary", key="intra_quick_scan"):
                with st.spinner("Scanning Nifty 50 for watchlist… usually **1–2 min**."):
                    report = run_quick_watchlist_scan(market, period, use_cache=False)
                    st.session_state["market_pulse_full"] = report
                st.rerun()

        if report and getattr(report, "stock_map", None):
            render_intraday_watchlist_section(report, max_concurrent_trades=max_concurrent_trades)
        else:
            st.info(
                "Tap **Quick scan** to build tonight's watchlist without opening Market Pulse. "
                "Uses the same Nifty 50 scan (cached 15 min)."
            )
