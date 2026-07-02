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
from analyzer.intraday_watchlist import IntradayWatchlistPick, build_intraday_watchlist
from analyzer.market_session import market_session_status
from analyzer.providers import get_live_ltp
from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured
from analyzer.watchlist_eod import fetch_watchlist_outcomes, outcome_label, score_pinned_plans
from analyzer.watchlist_pins import (
    clear_pins,
    is_pinned,
    load_pinned_plans,
    toggle_pin,
)
from analyzer.watchlist_plan_tracker import assess_live_plan
from analyzer.watchlist_telegram import format_pinned_watchlist_telegram


def _render_live_status(p: IntradayWatchlistPick | object, market: str) -> None:
    sym = getattr(p, "nse_symbol", None) or getattr(p, "symbol", "")
    entry = float(getattr(p, "entry"))
    stop = float(getattr(p, "stop_loss"))
    target = float(getattr(p, "target"))
    ltp, src = get_live_ltp(sym, market=market)
    status = assess_live_plan(ltp, entry=entry, stop_loss=stop, target=target, symbol=sym)
    st.caption(f"{status.emoji} **{status.label}** — {status.detail} ({src})")


def _render_pick_card(
    p: IntradayWatchlistPick,
    *,
    market: str,
    max_pins: int,
    show_live: bool,
) -> None:
    """Compact mobile-friendly card — Entry · Stop · Target + pin + chart."""
    checks = f"{p.checklist.passed}/{p.checklist.total}"
    pinned = is_pinned(p.nse_symbol)
    pin_badge = " ⭐" if pinned else ""

    st.markdown(
        f"""
<div class="watchlist-card">
  <h4>#{p.rank} {p.nse_symbol}{pin_badge} · {p.sector[:14]}</h4>
  <div class="watchlist-levels">
    <b>Entry</b> ₹{p.entry:,.0f} &nbsp;·&nbsp;
    <b>Stop</b> ₹{p.stop_loss:,.0f} &nbsp;·&nbsp;
    <b>Target</b> ₹{p.target:,.0f}
  </div>
  <div class="watchlist-meta">
    Price ₹{p.price:,.0f} · Checks {checks} · Score {p.prep_score:.0f}
    · ATR {f"{p.atr_pct:.1f}%" if p.atr_pct else "—"}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    if show_live and pinned:
        _render_live_status(p, market)

    c1, c2 = st.columns([1, 2])
    with c1:
        pin_label = "Unpin" if pinned else "Pin ⭐"
        if st.button(pin_label, key=f"wl_pin_{p.nse_symbol}", use_container_width=True):
            now_pinned, msg = toggle_pin(
                p.nse_symbol,
                entry=p.entry,
                stop_loss=p.stop_loss,
                target=p.target,
                max_pins=max_pins,
            )
            if now_pinned:
                st.success(msg)
            else:
                st.info(msg)
            st.rerun()
    with c2:
        if st.button(f"Open {p.nse_symbol} chart", key=f"wl_card_{p.nse_symbol}", use_container_width=True):
            st.session_state["intraday_ticker"] = p.nse_symbol
            st.session_state["intraday_focus_chart"] = True
            st.rerun()


def _render_pinned_section(
    *,
    market: str,
    market_bias: str,
    prep_date: str,
    max_pins: int,
) -> None:
    pins = load_pinned_plans()
    if not pins:
        return

    session = market_session_status()
    show_live = session.get("is_open", False)

    st.markdown(f"#### ⭐ My picks tonight ({len(pins)}/{max_pins})")
    st.caption("Trade **only** these tomorrow — levels are locked when you pin.")

    for pin in pins:
        st.markdown(
            f"**{pin.symbol}** — Entry ₹{pin.entry:,.0f} · "
            f"Stop ₹{pin.stop_loss:,.0f} · Target ₹{pin.target:,.0f}"
        )
        if show_live:
            _render_live_status(pin, market)

    t1, t2, t3 = st.columns(3)
    with t1:
        if telegram_configured():
            if st.button("Send picks to Telegram", key="wl_tg_pins", type="primary"):
                msg = format_pinned_watchlist_telegram(
                    pins, market_bias=market_bias, prep_date=prep_date
                )
                ok, err = send_telegram_broadcast(msg, alert_type="pulse")
                if ok:
                    st.success("Watchlist sent to Telegram.")
                else:
                    st.error(err)
        else:
            st.caption("Subscribe to Telegram in sidebar to export picks.")
    with t2:
        if not session.get("is_open") and st.button("Score today's picks", key="wl_score_eod"):
            with st.spinner("Scoring vs session high/low…"):
                scored = score_pinned_plans(market=market)
            if scored:
                st.success(f"Scored **{len(scored)}** pick(s). See **Track Record**.")
            else:
                st.info("Already scored or no session data.")
            st.rerun()
    with t3:
        if st.button("Clear pins", key="wl_clear_pins"):
            clear_pins()
            st.rerun()

    st.divider()


def _render_pick_detail_expander(p: IntradayWatchlistPick) -> None:
    with st.expander(
        f"Details — #{p.rank} {p.nse_symbol}",
        expanded=False,
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


def render_intraday_watchlist_section(
    report,
    *,
    market: str = "india",
    max_concurrent_trades: int = 2,
) -> None:
    """Tonight's lean MIS shortlist — entry/stop/target pre-written."""
    wl = build_intraday_watchlist(report)
    max_pins = min(3, max(1, max_concurrent_trades))
    prep_date = market_session_status().get("date", "")
    show_live = market_session_status().get("is_open", False)

    st.markdown("#### 🌙 Pre-market intraday watchlist (prepare tonight)")
    st.caption(wl.routine_note)
    c1, c2, c3 = st.columns(3)
    c1.metric("Market bias", wl.market_bias)
    c2.metric("Leading sector", wl.sector_leader)
    c3.metric("Lagging sector", wl.sector_laggard)

    _render_pinned_section(
        market=market,
        market_bias=wl.market_bias,
        prep_date=prep_date,
        max_pins=max_pins,
    )

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

    st.caption(f"**Pin up to {max_pins}** for tomorrow — live LTP vs plan when market is open.")
    view = st.radio(
        "Watchlist view",
        ["Cards", "Table"],
        horizontal=True,
        key="watchlist_view_mode",
        label_visibility="collapsed",
    )

    if view == "Cards":
        for p in wl.picks:
            _render_pick_card(p, market=market, max_pins=max_pins, show_live=show_live)
            _render_pick_detail_expander(p)
    else:
        table = []
        for p in wl.picks:
            checks = f"{p.checklist.passed}/{p.checklist.total}"
            pin_mark = "⭐" if is_pinned(p.nse_symbol) else ""
            table.append({
                "Rank": p.rank,
                "Stock": f"{p.nse_symbol}{pin_mark}",
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
            c1, c2 = st.columns([1, 3])
            with c1:
                if st.button(
                    "Unpin" if is_pinned(p.nse_symbol) else "Pin ⭐",
                    key=f"wl_tbl_pin_{p.nse_symbol}",
                ):
                    toggle_pin(
                        p.nse_symbol,
                        entry=p.entry,
                        stop_loss=p.stop_loss,
                        target=p.target,
                        max_pins=max_pins,
                    )
                    st.rerun()
            with c2:
                if show_live and is_pinned(p.nse_symbol):
                    _render_live_status(p, market)
            _render_pick_detail_expander(p)

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

        _, c2 = st.columns([3, 1])
        with c2:
            if st.button("Quick scan", type="primary", key="intra_quick_scan"):
                with st.spinner("Scanning Nifty 50 for watchlist… usually **1–2 min**."):
                    report = run_quick_watchlist_scan(market, period, use_cache=False)
                    st.session_state["market_pulse_full"] = report
                st.rerun()

        if report and getattr(report, "stock_map", None):
            render_intraday_watchlist_section(
                report,
                market=market,
                max_concurrent_trades=max_concurrent_trades,
            )
        else:
            pins = load_pinned_plans()
            if pins:
                _render_pinned_section(
                    market=market,
                    market_bias="—",
                    prep_date=market_session_status().get("date", ""),
                    max_pins=min(3, max_concurrent_trades),
                )
            st.info(
                "Tap **Quick scan** to build tonight's watchlist without opening Market Pulse. "
                "Uses the same Nifty 50 scan (cached 15 min)."
            )
