"""Pre-market intraday watchlist UI — auto top 5 for tomorrow."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from analyzer.intraday_beginner_tips import build_capital_budget, too_many_watchlist_warning
from analyzer.intraday_chart import intraday_chart
from analyzer.intraday_data import INTERVAL_OPTIONS, fetch_intraday
from analyzer.intraday_prefs import load_intraday_prefs
from analyzer.intraday_signals import add_intraday_indicators, analyze_intraday
from analyzer.intraday_pulse_source import (
    DEFAULT_INTRADAY_PULSE_PERIOD,
    load_pulse_for_watchlist,
    run_quick_watchlist_scan,
)
from analyzer.intraday_watchlist import IntradayWatchlistPick, build_intraday_watchlist
from analyzer.market_session import market_session_status
from analyzer.opening_range_confirm import confirm_or_entry, fetch_symbol_opening_range
from analyzer.providers import data_source_status, get_live_ltp
from analyzer.telegram_notify import telegram_configured
from analyzer.watchlist_profit import (
    equity_target_profit_one_share,
    format_expected_profit,
    options_target_profit_one_lot,
)
from analyzer.watchlist_persist import persist_watchlist_state
from analyzer.watchlist_pins import TOP_TOMORROW_PICKS
from analyzer.trade_ladder import build_equity_ladder, format_stop_trail_guide
from analyzer.watchlist_plan_tracker import assess_live_plan
from analyzer.watchlist_position_size import (
    equity_position_hint,
    format_entry_status,
    format_risk_cell,
    format_shares_cell,
)
from analyzer.trade_selection import (
    is_selected,
    load_selected_symbols,
    selection_status_line,
    toggle_selected,
)
from analyzer.prep_status import sync_selection_prep_step
from analyzer.watchlist_pick_display import format_pick_history, format_pick_why
from analyzer.watchlist_sector import sector_concentration_warning
from analyzer.whatsapp_export import mis_prep_whatsapp_url
from ui.components.prep_all import send_combined_telegram_from_session
from ui.components.empty_states import empty_quick_scan
from ui.navigation import request_nav_tab


def _watchlist_ticker(nse_symbol: str, market: str) -> str:
    sym = nse_symbol.upper().replace(".NS", "").replace(".BO", "")
    return f"{sym}.NS" if market == "india" else sym


def _chart_legend_caption(side: str) -> str:
    if side == "SHORT":
        return (
            "Yellow = entry · Red = stop (above) · "
            "Green dashed = T1/T2/T3 (below, profit direction)"
        )
    return "Yellow = entry · Red = stop · Green dashed = T1/T2/T3"


def _render_watchlist_plan_chart(p: IntradayWatchlistPick, market: str, interval: str) -> None:
    """Intraday candle chart with entry, stop, T1/T2/T3 lines."""
    ticker = _watchlist_ticker(p.nse_symbol, market)
    side = _pick_side(p)
    ladder = build_equity_ladder(
        side, p.entry, p.stop_loss, p.target,
        pivot_r2=p.pivot.r2 if p.pivot else None,
    )
    try:
        df, meta = fetch_intraday(ticker, interval=interval, market=market)
        if df is None or df.empty or len(df) < 5:
            st.caption("Not enough intraday bars yet — try again after open.")
            return
        df = add_intraday_indicators(df)
        analysis = analyze_intraday(df, ticker, interval)
        st.plotly_chart(
            intraday_chart(df, analysis, ladder=ladder),
            use_container_width=True,
            key=f"wl_plan_chart_{p.nse_symbol}_{interval}",
        )
        src = meta.get("source", "—")
        lag = meta.get("lag_note", "")
        st.caption(
            f"Lines: **Stop** ₹{ladder.initial_stop:,.0f} · **Entry** ₹{ladder.entry:,.0f} · "
            f"**T1** ₹{ladder.target:,.0f} · **T2** ₹{ladder.target2:,.0f} · "
            f"**T3** ₹{ladder.target3:,.0f} · {src}{(' · ' + lag) if lag else ''}"
        )
        st.caption(format_stop_trail_guide(ladder))
    except Exception as exc:
        st.warning(f"Chart unavailable for {p.nse_symbol}: {exc}")


@st.fragment(run_every=timedelta(seconds=60))
def _watchlist_plan_charts_panel(
    picks: list[IntradayWatchlistPick],
    market: str,
    interval: str,
) -> None:
    """Auto-refreshing plan charts during the session."""
    _render_watchlist_plan_charts_body(picks, market, interval)


def _render_watchlist_plan_charts_body(
    picks: list[IntradayWatchlistPick],
    market: str,
    interval: str,
) -> None:
    for p in picks:
        star = "⭐ " if is_selected(p.nse_symbol) else ""
        expanded = is_selected(p.nse_symbol) or p.rank <= 2
        with st.expander(
            f"#{p.rank} {star}{p.nse_symbol} — live chart & plan levels",
            expanded=expanded,
        ):
            _render_live_status(p, market)
            _render_watchlist_plan_chart(p, market, interval)
            if is_selected(p.nse_symbol):
                from ui.components.strategy_synthesis import render_equity_synthesis_for_symbol

                render_equity_synthesis_for_symbol(
                    p.nse_symbol,
                    market=market,
                    key_prefix=f"eq_syn_{p.nse_symbol}",
                )


def _render_watchlist_plan_charts(
    picks: list[IntradayWatchlistPick],
    market: str,
    *,
    auto_refresh: bool = False,
) -> None:
    if not picks:
        return
    st.markdown("##### 📈 Live charts — entry · stop · T1/T2/T3")
    ds = data_source_status()
    sides = {_pick_side(p) for p in picks}
    if sides == {"SHORT"}:
        legend = _chart_legend_caption("SHORT")
    elif sides == {"LONG"}:
        legend = _chart_legend_caption("LONG")
    else:
        legend = "Yellow = entry · Red = stop · Green dashed = T1/T2/T3 (LONG & SHORT picks)"
    st.caption(f"Candles: **{ds['primary_intraday']}** · {legend}")
    interval_label = st.selectbox(
        "Chart interval",
        list(INTERVAL_OPTIONS.keys()),
        index=1,
        key="wl_plan_chart_interval",
    )
    interval = INTERVAL_OPTIONS[interval_label]
    if auto_refresh:
        _watchlist_plan_charts_panel(picks, market, interval)
    else:
        _render_watchlist_plan_charts_body(picks, market, interval)


def _pick_side(p: IntradayWatchlistPick) -> str:
    return getattr(p, "side", "LONG") or "LONG"


def _render_live_status(p: IntradayWatchlistPick | object, market: str) -> None:
    sym = getattr(p, "nse_symbol", None) or getattr(p, "symbol", "")
    entry = float(getattr(p, "entry"))
    stop = float(getattr(p, "stop_loss"))
    target = float(getattr(p, "target"))
    ltp, src = get_live_ltp(sym, market=market)
    pivot_r2 = getattr(getattr(p, "pivot", None), "r2", None)
    side = _pick_side(p) if hasattr(p, "nse_symbol") else "LONG"
    status = assess_live_plan(
        ltp, entry=entry, stop_loss=stop, target=target, symbol=sym, pivot_r2=pivot_r2,
        side=side,
    )
    st.caption(f"{status.emoji} **{status.label}** — {status.detail} ({src})")
    if status.ladder_note:
        st.caption(f"Ladder: {status.ladder_note}")
    or_rng = fetch_symbol_opening_range(sym, market=market)
    if or_rng and ltp:
        or_high, or_low = or_rng
        or_status = confirm_or_entry(
            ltp, entry=entry, or_high=or_high, or_low=or_low, side=side,
        )
        st.caption(f"{or_status.emoji} **OR:** {or_status.label} — {or_status.detail}")


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
        ladder = build_equity_ladder(
            _pick_side(p), p.entry, p.stop_loss, p.target,
            pivot_r2=p.pivot.r2 if p.pivot else None,
        )
        st.caption(format_stop_trail_guide(ladder))
        prefs = load_intraday_prefs()
        budget = build_capital_budget(
            prefs.capital,
            allocation_pct=prefs.allocation_pct,
            max_risk_pct=prefs.max_risk_pct,
            max_concurrent_trades=prefs.max_trades,
        )
        hint = equity_position_hint(
            p.nse_symbol,
            p.entry,
            p.stop_loss,
            p.target,
            allocated_inr=budget.allocated_inr,
            max_risk_pct=prefs.max_risk_pct,
            max_concurrent_trades=prefs.max_trades,
            per_trade_budget_inr=budget.per_trade_budget_inr,
            side=_pick_side(p),
        )
        if hint.suggested_shares:
            st.caption(
                f"**Size:** {hint.suggested_shares} shares · max loss **₹{hint.max_loss_inr:,.0f}** "
                f"({prefs.max_risk_pct:.1f}% of MIS pool ₹{budget.allocated_inr:,.0f})"
            )
        elif hint.skip_reason:
            st.caption(f"**Size:** skip — {hint.skip_reason}")
        st.markdown("**Pro checklist**")
        for note in p.checklist.notes:
            st.markdown(f"- {note}")


def _render_top_picks_actions(
    *,
    market_bias: str,
    prep_date: str,
    picks: list[IntradayWatchlistPick],
    options_picks: list | None = None,
) -> None:
    if not picks:
        return

    t1, t2, t3 = st.columns(3)
    with t1:
        if telegram_configured():
            if st.button("Send MIS prep to Telegram", key="wl_tg_top5", type="primary"):
                ok, err = send_combined_telegram_from_session(
                    options_picks=options_picks or [],
                    market_bias=market_bias,
                )
                if ok:
                    st.success("Equity + options sent to Telegram.")
                else:
                    st.error(err)
        else:
            st.caption("Subscribe to Telegram in sidebar to export picks.")
    with t2:
        wa_url = mis_prep_whatsapp_url(
            options_picks=options_picks or [],
            market_bias=market_bias,
        )
        st.link_button(
            "Share via WhatsApp",
            wa_url,
            use_container_width=True,
            help="Opens WhatsApp with MIS prep text — tap Send on your phone.",
        )
    with t3:
        st.caption(
            f"Auto-selected **{len(picks)}** names ranked by prep score — "
            "trade only these tomorrow."
        )


def render_intraday_watchlist_section(
    report,
    *,
    market: str = "india",
    max_concurrent_trades: int = 2,
) -> None:
    """Tonight's top 5 MIS picks — entry/stop/target pre-written."""
    wl = build_intraday_watchlist(report, limit=TOP_TOMORROW_PICKS)
    prep_date = market_session_status().get("date", "")
    show_live = market_session_status().get("is_open", False)

    st.markdown(f"#### 🌙 Top {TOP_TOMORROW_PICKS} for tomorrow")
    st.caption(
        f"{wl.routine_note} · Today's results are in **Intraday track record** below."
    )

    if wl.picks:
        persist_watchlist_state(
            wl,
            prep_date=prep_date,
            session_store=st.session_state,
        )

    c1, c2, c3 = st.columns(3)
    c1.metric("Market bias", wl.market_bias)
    c2.metric("Leading sector", wl.sector_leader)
    c3.metric("Lagging sector", wl.sector_laggard)

    if not wl.picks:
        empty_quick_scan(key="wl_empty_scan")
        st.markdown(
            "**Nightly routine**\n"
            "1. Nifty trend · 2. Sector leaders · 3. Volume shockers · "
            "4. Chart patterns · 5. Liquidity · 6. Earnings/news"
        )
        return

    st.success(
        f"**{len(wl.picks)}** stocks auto-selected — entry, stop, and target defined for each."
    )
    over = too_many_watchlist_warning(len(wl.picks), max_concurrent_trades)
    if over:
        st.warning(over)

    sector_warn = sector_concentration_warning(wl.picks)
    if sector_warn:
        st.warning(sector_warn)

    st.markdown("##### Pick your 2 trades")
    st.caption(selection_status_line(max_selected=max_concurrent_trades))
    sel_cols = st.columns(min(len(wl.picks), 5))
    for i, p in enumerate(wl.picks):
        with sel_cols[i]:
            star = "⭐" if is_selected(p.nse_symbol) else "☆"
            if st.button(
                f"{star} {p.nse_symbol}",
                key=f"trade_sel_{p.nse_symbol}",
                use_container_width=True,
            ):
                _, msg = toggle_selected(
                    p.nse_symbol,
                    max_selected=max_concurrent_trades,
                    sector=p.sector,
                )
                sync_selection_prep_step()
                st.toast(msg.replace("**", ""))
                st.rerun()
    if load_selected_symbols():
        st.caption(
            "Reminders & EOD summary focus on your **2 starred** names only."
        )

    prefs = load_intraday_prefs()
    budget = build_capital_budget(
        float(st.session_state.get("intraday_capital", prefs.capital)),
        allocation_pct=float(st.session_state.get("intraday_allocation_pct", prefs.allocation_pct)),
        max_risk_pct=float(st.session_state.get("intraday_max_risk_pct", prefs.max_risk_pct)),
        max_concurrent_trades=int(st.session_state.get("intraday_max_trades", prefs.max_trades)),
    )
    st.caption(
        f"Position size uses **₹{budget.per_trade_budget_inr:,.0f}**/trade "
        f"(**₹{budget.allocated_inr:,.0f}** MIS pool ÷ {prefs.max_trades}) · "
        f"**{prefs.max_risk_pct:.1f}%** max risk/trade ≈ **₹{budget.max_risk_per_trade_inr:,.0f}**"
    )

    table = []
    for p in wl.picks:
        checks = f"{p.checklist.passed}/{p.checklist.total}"
        hint = equity_position_hint(
            p.nse_symbol,
            p.entry,
            p.stop_loss,
            p.target,
            allocated_inr=budget.allocated_inr,
            max_risk_pct=prefs.max_risk_pct,
            max_concurrent_trades=prefs.max_trades,
            per_trade_budget_inr=budget.per_trade_budget_inr,
            side=_pick_side(p),
        )
        ladder = build_equity_ladder(
            _pick_side(p), p.entry, p.stop_loss, p.target,
            pivot_r2=p.pivot.r2 if p.pivot else None,
        )
        table.append({
            "Rank": p.rank,
            "Stock": p.nse_symbol,
            "Side": _pick_side(p),
            "Trade": "⭐" if is_selected(p.nse_symbol) else "",
            "Sector": p.sector[:12],
            "Price": f"₹{p.price:,.0f}",
            "ATR%": f"{p.atr_pct:.1f}" if p.atr_pct else "—",
            "Vol×": f"{p.volume_ratio:.1f}" if p.volume_ratio else "—",
            "RSI": f"{p.rsi:.0f}" if p.rsi else "—",
            "Checks": checks,
            "Why": format_pick_why(p),
            "Conf.": f"{p.confidence_pct:.0f}%" if p.confidence_pct is not None else "—",
            "30d hit rate": format_pick_history(p),
            "Entry": f"₹{p.entry:,.0f}",
            "Stop (start)": f"₹{ladder.initial_stop:,.0f}",
            "Stop@T1": f"₹{ladder.stops_after[0]:,.0f}",
            "Stop@T2": f"₹{ladder.stops_after[1]:,.0f}",
            "Stop@T3": f"₹{ladder.stops_after[2]:,.0f}",
            "T1": f"₹{ladder.target:,.0f}",
            "T2": f"₹{ladder.target2:,.0f}",
            "T3": f"₹{ladder.target3:,.0f}",
            "Shares": format_shares_cell(hint),
            "Status": format_entry_status(p, hint),
            "Risk ₹": format_risk_cell(hint),
            "Exp. profit (1 sh)": format_expected_profit(
                equity_target_profit_one_share(
                    p.entry, p.target, side=_pick_side(p),
                )
            ),
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    st.markdown("##### Open in Alpha AI")
    alpha_cols = st.columns(min(len(wl.picks), 5))
    for i, p in enumerate(wl.picks):
        with alpha_cols[i]:
            if st.button(
                f"Alpha · {p.nse_symbol}",
                key=f"wl_alpha_{p.nse_symbol}",
                use_container_width=True,
            ):
                sym = p.nse_symbol.replace(".NS", "").replace(".BO", "")
                request_nav_tab("Alpha AI", alpha_ai_ticker=sym)
                st.stop()

    _render_top_picks_actions(
        market_bias=wl.market_bias,
        prep_date=prep_date,
        picks=wl.picks,
        options_picks=st.session_state.get("options_expiry_watchlist_cache", type(None))
        and getattr(st.session_state.get("options_expiry_watchlist_cache"), "picks", None),
    )

    _render_watchlist_plan_charts(wl.picks, market, auto_refresh=show_live)

    if show_live:
        st.markdown("##### Live vs plan (summary)")
        for p in wl.picks:
            if is_selected(p.nse_symbol):
                st.markdown(f"**#{p.rank} {p.nse_symbol}** ⭐")
                _render_live_status(p, market)

    for p in wl.picks:
        _render_pick_detail_expander(p)

    st.caption(
        "Avoid: tip-chasing, illiquid names, trading more than your max trades, no stop-loss. "
        "**Stick to the top 5 — better prepared beats more names.**"
    )


def _render_watchlist_body(
    market: str,
    *,
    period: str,
    max_concurrent_trades: int,
) -> None:
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
    st.caption(
        f"Scan history: **{period}** · {status_msgs.get(status, '')}"
        if status_msgs.get(status) else f"Scan history: **{period}**"
    )

    _, c2 = st.columns([3, 1])
    with c2:
        if st.button("Quick scan", type="primary", key="intra_quick_scan"):
            with st.spinner("Scanning Nifty 50 for watchlist… usually **1–2 min**."):
                report = run_quick_watchlist_scan(market, period, use_cache=False)
                st.session_state["market_pulse_full"] = report
                if report and getattr(report, "stock_map", None):
                    wl = build_intraday_watchlist(report, limit=TOP_TOMORROW_PICKS)
                    persist_watchlist_state(
                        wl,
                        prep_date=market_session_status().get("date", ""),
                        force=True,
                        session_store=st.session_state,
                    )
            st.rerun()

    if report and getattr(report, "stock_map", None):
        render_intraday_watchlist_section(
            report,
            market=market,
            max_concurrent_trades=max_concurrent_trades,
        )
    else:
        st.info(
            "Tap **Quick scan** to build tonight's **top 5** without opening Market Pulse. "
            "Uses the same Nifty 50 scan (cached 15 min)."
        )


def render_intraday_watchlist_block(
    market: str,
    *,
    period: str = DEFAULT_INTRADAY_PULSE_PERIOD,
    max_concurrent_trades: int = 2,
    as_top_section: bool = False,
) -> None:
    """Watchlist with cache/session load + Quick scan — no Market Pulse tab required."""
    expand = st.session_state.pop("intraday_focus_watchlist", False)
    if as_top_section:
        st.markdown("### 🌙 Top MIS picks for tomorrow")
        _render_watchlist_body(
            market, period=period, max_concurrent_trades=max_concurrent_trades,
        )
        return

    with st.expander("🌙 Top MIS picks for tomorrow", expanded=expand):
        _render_watchlist_body(
            market, period=period, max_concurrent_trades=max_concurrent_trades,
        )
