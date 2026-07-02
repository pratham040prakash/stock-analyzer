"""Market Pulse tab — Nifty 50 multi-horizon scan."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from analyzer.intraday_chart import intraday_chart
from analyzer.intraday_data import market_session_status
from analyzer.pulse_cache import load_pulse_cache_with_stale
from analyzer.market_pulse_scan import (
    CACHE_TTL as PULSE_CACHE_TTL,
    load_index_options_for_report,
    run_market_pulse_scan,
)
from analyzer.markets import format_price, is_india_market
from analyzer.nse_options import chain_summary_markdown
from analyzer.session_advisory import PulseLiveSnapshot, fetch_pulse_live_update
from analyzer.telegram_notify import format_pulse_alert, send_telegram_broadcast, telegram_configured
from ui.charts import price_chart
from ui.components.india_macro import pulse_buy_color, render_india_macro_strip
from analyzer.intraday_stock_picker import investopedia_screen_summary
from analyzer.intraday_trade_plan import build_intraday_trade_plan
from ui.components.delivery_quality import render_delivery_banner, render_delivery_table
from ui.components.earnings_calendar import render_earnings_week_strip
from ui.components.intraday import render_entry_exit_plan, render_nse_chain_table
from ui.components.affordable_invest import render_affordable_invest_section
from ui.components.iv_rank import render_iv_banner, render_iv_market_strip, render_iv_table
from ui.theme import GLOBAL_BIAS_COLORS, OPTIONS_COLORS, REC_COLORS


def render_pulse_pick_card(pick, stock_map: dict) -> None:
    """Buy suggestion + chart for one horizon pick."""
    color = pulse_buy_color(pick.action)
    st.markdown(
        f"<span style='color:{color};font-weight:700;font-size:1.1rem'>{pick.nse_symbol}</span> "
        f"**{pick.action}** · ₹{pick.price:,.0f} · score **{pick.score:+.0f}**",
        unsafe_allow_html=True,
    )
    st.caption(pick.summary)
    if pick.regime_note:
        st.warning(pick.regime_note)
    if getattr(pick, "screen_notes", None):
        for note in pick.screen_notes[:3]:
            st.caption(f"📋 {note}")
    if getattr(pick, "screen_score", 0) > 0:
        st.caption(f"Investopedia screen score: **{pick.screen_score:.0f}/100**")
    st.caption(f"Trade type: **{pick.trade_type}**")
    st.markdown(
        f"**Entry:** {pick.entry_hint} · **Stop:** {pick.stop_hint} · **Target:** {pick.target_hint}"
    )
    for sig in pick.chart_signals[:4]:
        st.markdown(f"- {sig}")

    entry = stock_map.get(pick.nse_symbol)
    if pick.horizon == "intraday" and entry and entry.intraday_verdict:
        v = entry.intraday_verdict
        plan = build_intraday_trade_plan(
            v.action,
            v.entry,
            v.stop_loss,
            v.target,
            entry_reasons=v.reasons,
        )
        with st.expander("Entry & exit plan", expanded=True):
            render_entry_exit_plan(plan, show_capital_hint=False)

    if not entry:
        return

    if pick.horizon == "intraday" and entry.intraday_df is not None and entry.intraday_verdict:
        analysis = entry.intraday_verdict.intraday
        if analysis:
            st.plotly_chart(
                intraday_chart(entry.intraday_df, analysis),
                use_container_width=True,
                key=f"pulse_intra_{pick.nse_symbol}_{pick.horizon}",
            )
    elif pick.horizon == "short" and entry.short_chart_df is not None:
        st.plotly_chart(
            price_chart(entry.short_chart_df, entry.symbol),
            use_container_width=True,
            key=f"pulse_short_{pick.nse_symbol}",
        )
    elif pick.horizon == "long" and entry.long_chart_df is not None:
        st.plotly_chart(
            price_chart(entry.long_chart_df, entry.symbol),
            use_container_width=True,
            key=f"pulse_long_{pick.nse_symbol}",
        )


def display_pulse_live_strip(live: PulseLiveSnapshot, report) -> None:
    """Session status + closed-market guidance + live indices/macro (30s refresh)."""
    session = live.session
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NSE session", session["status"])
    c2.metric("IST time", session["time_ist"])
    c3.caption(session.get("next_session", ""))
    c4.caption(f"Live update: **{live.updated_at}**")

    if session.get("is_open"):
        st.success(live.advisory_markdown)
    else:
        st.info(live.advisory_markdown)

    if live.global_impact:
        bias_color = GLOBAL_BIAS_COLORS.get(live.global_impact.predicted_nifty_bias, "#ffd600")
        g1, g2, g3 = st.columns(3)
        label = "Global → Nifty bias" if session.get("is_open") else "Global → next session"
        g1.markdown(
            f"<div style='padding:10px;border-radius:8px;background:#1e1e1e;text-align:center'>"
            f"<p style='margin:0;color:#aaa;font-size:0.75rem'>{label}</p>"
            f"<p style='margin:0;font-size:1.2rem;font-weight:700;color:{bias_color}'>"
            f"{live.global_impact.predicted_nifty_bias}</p></div>",
            unsafe_allow_html=True,
        )
        g2.metric("Spillover", f"{live.global_impact.spillover_score:+.0f}")
        g3.metric("Implied Nifty move", f"{live.global_impact.predicted_move_pct:+.2f}%")

    regime = live.regime or (getattr(report, "regime", None) if report else None)
    if regime:
        st.markdown(regime.banner)
        st.caption(regime.message)

    st.markdown(live.market_verdict)

    indices = live.indices or (getattr(report, "indices", None) if report else None) or []
    if indices:
        ncol = min(len(indices), 4)
        cols = st.columns(ncol)
        for col, point in zip(cols, indices[:ncol]):
            color = REC_COLORS.get(point.recommendation, "#ffd600")
            with col:
                st.metric(point.name, format_price(point.price, point.symbol))
                st.markdown(
                    f"<span style='color:{color};font-weight:600'>{point.recommendation}</span> "
                    f"({point.score:+.0f}) · {point.regime}",
                    unsafe_allow_html=True,
                )
                if point.change_1m_pct is not None:
                    st.caption(f"1M: {point.change_1m_pct:+.1f}%")
    elif report and getattr(report, "indices", None):
        st.caption("Refreshing index data…")
    else:
        st.warning("Index data unavailable — check network.")

    macro = live.macro or (getattr(report, "macro", None) if report else None)
    if macro:
        render_india_macro_strip(macro)


@st.fragment(run_every=timedelta(seconds=30))
def market_pulse_live_panel(period: str) -> None:
    report = st.session_state.get("market_pulse_full")
    live = fetch_pulse_live_update(period, pulse_report=report)
    display_pulse_live_strip(live, report)


def render_market_pulse(market: str, period: str) -> None:
    st.subheader("Market Pulse")
    st.caption(
        "**Intraday** (5m, MIS) · **Short-term** swing (2–8 weeks, daily) · **Long-term** (6mo–3yr, daily) — "
        "each with **chart + BUY suggestion**. Varsity TA."
    )

    if not is_india_market(market):
        st.info("Market Pulse is optimized for India. Switch sidebar to **India (Auto)**.")
        return

    pulse_auto = st.checkbox(
        "Auto-refresh live data (30 sec)",
        value=True,
        key="pulse_auto_refresh",
        help="Updates session status, global bias, indices, VIX, FII/DII every 30s. "
        "Full Nifty 50 scan uses the button below.",
    )

    skip_earnings = st.checkbox(
        "Skip intraday/swing picks with earnings this week",
        value=True,
        key="pulse_skip_earnings",
        help="Hides MIS and swing BUYs when results are within 3–5 days.",
    )
    filter_delivery = st.checkbox(
        "Skip speculative low-delivery picks (swing/MIS)",
        value=True,
        key="pulse_filter_delivery",
        help="Hides picks with delivery <25% and high volume churn.",
    )

    if st.button("Refresh full market pulse", type="primary", key="pulse_refresh"):
        st.session_state.pop("market_pulse_full", None)
        st.session_state.pop("market_pulse", None)
        st.session_state["pulse_force_refresh"] = True

    report_for_tg = st.session_state.get("market_pulse_full")
    if telegram_configured() and report_for_tg:
        if st.button("Send pulse to Telegram", key="pulse_telegram"):
            ok, msg = send_telegram_broadcast(format_pulse_alert(report_for_tg))
            if ok:
                st.success("Sent to Telegram")
            else:
                st.error(msg)

    force = st.session_state.pop("pulse_force_refresh", False)

    if force:
        st.session_state.pop("market_pulse_full", None)
        st.session_state.pop("pulse_cache_stale", None)

    if "market_pulse_full" not in st.session_state:
        cached, fresh = load_pulse_cache_with_stale(f"pulse_{period}_{market}", PULSE_CACHE_TTL)
        if cached is not None and getattr(cached, "indices", None):
            st.session_state["market_pulse_full"] = cached
            if not fresh:
                st.session_state["pulse_cache_stale"] = True

    needs_fresh_scan = force or "market_pulse_full" not in st.session_state

    if needs_fresh_scan:
        st.caption("Loading live indices & session status while the full Nifty 50 scan runs…")
        if pulse_auto:
            live = fetch_pulse_live_update(period, pulse_report=None)
            display_pulse_live_strip(live, None)
            st.divider()
        with st.spinner(
            "Scanning Nifty 50 — parallel daily charts… "
            "Usually **1–2 min** (instant on next visit from cache)."
        ):
            st.session_state["market_pulse_full"] = run_market_pulse_scan(
                period, market, use_cache=not force,
                skip_earnings_week=skip_earnings,
                filter_weak_delivery=filter_delivery,
            )
        st.session_state.pop("pulse_cache_stale", None)

    report = st.session_state.get("market_pulse_full")
    if not report:
        st.warning("Could not build market pulse. Try refresh.")
        return

    if getattr(report, "from_cache", False):
        st.caption("📦 Full scan from cache (15 min TTL) — click Refresh for new Nifty 50 scan")
    elif st.session_state.get("pulse_cache_stale"):
        st.info("Showing **cached** scan (older than 15 min). Tap **Refresh full market pulse** for a new run.")

    if pulse_auto:
        market_pulse_live_panel(period)
    else:
        live = fetch_pulse_live_update(period, pulse_report=report)
        display_pulse_live_strip(live, report)

    st.divider()

    stock_map = getattr(report, "stock_map", {}) or {s.nse_symbol: s for s in report.top_stocks}
    session = market_session_status()

    earnings_events = getattr(report, "earnings_events", None) or []
    if not earnings_events and is_india_market(market):
        from analyzer.earnings_calendar import fetch_nifty50_earnings
        earnings_events = fetch_nifty50_earnings()
    if earnings_events:
        render_earnings_week_strip(earnings_events)

    delivery_snapshots = getattr(report, "delivery_snapshots", None) or []
    if not delivery_snapshots and is_india_market(market):
        from analyzer.delivery_quality import fetch_delivery_batch
        delivery_snapshots = fetch_delivery_batch(list(stock_map.keys()))
    if delivery_snapshots:
        render_delivery_table(delivery_snapshots)

    index_iv = [
        io.options_analytics for io in getattr(report, "index_options", [])
        if getattr(io, "options_analytics", None)
    ]
    if index_iv or getattr(report, "macro", None):
        render_iv_market_strip(getattr(report, "macro", None), index_iv)
    if index_iv:
        render_iv_table(index_iv)

    if earnings_events or delivery_snapshots or index_iv:
        st.divider()

    render_affordable_invest_section(report, period)

    st.divider()
    st.subheader("🎯 BUY suggestions — all timeframes")
    if not session.get("is_open"):
        st.caption(
            "Market closed — **intraday MIS** is inactive. Focus on **short-term swing** "
            "and **long-term delivery** picks; charts show the last session."
        )

    col_i, col_s, col_l = st.columns(3)
    with col_i:
        st.markdown("#### ⏱️ Intraday (5m)")
        if session.get("is_open"):
            st.caption("Today / MIS · square off before **3:20 PM IST**")
        else:
            st.caption("Inactive while closed — last session levels only")
        st.caption(investopedia_screen_summary())
        if report.intraday_picks:
            for pick in report.intraday_picks[:4]:
                with st.expander(f"{pick.nse_symbol} — {pick.action}", expanded=len(report.intraday_picks) <= 2):
                    render_pulse_pick_card(pick, stock_map)
        else:
            st.caption("No intraday BUY setups right now.")

    with col_s:
        st.markdown("#### 📅 Short-term (daily)")
        st.caption("Swing **2–8 weeks** — SMA, MACD, patterns")
        if report.short_term_picks:
            for pick in report.short_term_picks[:4]:
                with st.expander(f"{pick.nse_symbol} — {pick.action}", expanded=False):
                    render_pulse_pick_card(pick, stock_map)
        else:
            st.caption("No swing BUY setups on daily chart.")

    with col_l:
        st.markdown("#### 📆 Long-term (daily)")
        st.caption("Position **6mo–3yr** — SMA-50/200 structure")
        if report.long_term_picks:
            for pick in report.long_term_picks[:4]:
                with st.expander(f"{pick.nse_symbol} — {pick.action}", expanded=False):
                    render_pulse_pick_card(pick, stock_map)
        else:
            st.caption("No long-term BUY structures right now.")

    st.divider()
    with st.expander("📡 Index option chains (NSE)", expanded=False):
        if getattr(report, "_index_options_deferred", False) or not report.index_options:
            if st.button("Load NSE option chains", key="pulse_load_options"):
                with st.spinner("Fetching Nifty & Bank Nifty option chains…"):
                    load_index_options_for_report(report, period)
                st.rerun()
            st.caption("Option chains load on demand (~15–30s) to keep Market Pulse fast.")
        for io in report.index_options:
            action_color = OPTIONS_COLORS.get(io.options_action, "#ffd600")
            st.markdown(f"**{io.name}** — {io.options_action}")
            st.markdown(
                f"<span style='font-weight:700;color:{action_color}'>{io.options_action}</span>",
                unsafe_allow_html=True,
            )
            if io.error:
                st.warning(io.error)
            elif io.chain:
                st.markdown(chain_summary_markdown(io.chain))
                if io.options_analytics:
                    render_iv_banner(io.options_analytics, horizon="options", symbol=io.name)
                if io.picks:
                    for pick in io.picks[:3]:
                        leg = pick.leg
                        st.success(
                            f"**{leg.option_type} {leg.strike:g}** · LTP ₹{leg.ltp or 0:,.2f} · {pick.reason}"
                        )
                render_nse_chain_table(io.chain, io.options_action)

    st.divider()
    st.subheader("Top 10 Nifty — all horizons")

    table = []
    for stock in report.top_stocks:
        it = stock.intraday.action if stock.intraday else "—"
        st_hor = stock.short_term.action if stock.short_term else "—"
        lt_hor = stock.long_term.action if stock.long_term else "—"
        table.append({
            "Stock": stock.nse_symbol,
            "Price": f"₹{stock.price:,.2f}",
            "Intraday": it,
            "Short-term": st_hor,
            "Long-term": lt_hor,
            "Combined": stock.combined_rec,
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    st.markdown("#### What to do")
    for stock in report.top_stocks:
        if stock.error:
            continue
        st.markdown(f"**{stock.nse_symbol}** — {stock.what_to_do}")

    st.divider()
    st.subheader("📈 Charts — Intraday · Short · Long (Top 10)")
    for stock in report.top_stocks:
        if stock.error:
            st.warning(f"{stock.nse_symbol}: {stock.error}")
            continue
        it_a = stock.intraday.action if stock.intraday else "—"
        st_a = stock.short_term.action if stock.short_term else "—"
        lt_a = stock.long_term.action if stock.long_term else "—"
        with st.expander(
            f"{stock.nse_symbol} — Intraday: {it_a} | Short: {st_a} | Long: {lt_a}",
            expanded=False,
        ):
            t1, t2, t3 = st.tabs(["Intraday (5m)", "Short-term (daily)", "Long-term (daily)"])
            with t1:
                if stock.intraday:
                    st.metric("Suggestion", stock.intraday.action)
                    st.caption(stock.intraday.summary)
                    for sig in (stock.intraday.chart_signals or [])[:5]:
                        st.markdown(f"- {sig}")
                    if stock.intraday_df is not None and stock.intraday_verdict and stock.intraday_verdict.intraday:
                        st.plotly_chart(
                            intraday_chart(stock.intraday_df, stock.intraday_verdict.intraday),
                            use_container_width=True,
                            key=f"top_intra_{stock.nse_symbol}",
                        )
                    else:
                        st.caption("5m chart unavailable — refresh during market hours.")
                if stock.intraday and stock.intraday.action in ("STRONG BUY", "BUY") and stock.intraday_verdict:
                    if stock.intraday_verdict.entry:
                        st.success(
                            f"**BUY plan:** Entry ₹{stock.intraday_verdict.entry:,.2f} · "
                            f"Stop ₹{stock.intraday_verdict.stop_loss:,.2f} · "
                            f"Target ₹{stock.intraday_verdict.target:,.2f}"
                        )
            with t2:
                if stock.short_term:
                    st.metric("Suggestion", stock.short_term.action)
                    st.caption(stock.short_term.summary)
                    for sig in (stock.short_term.chart_signals or [])[:5]:
                        st.markdown(f"- {sig}")
                    if stock.short_chart_df is not None:
                        st.plotly_chart(
                            price_chart(stock.short_chart_df, stock.symbol),
                            use_container_width=True,
                            key=f"top_short_{stock.nse_symbol}",
                        )
                    if stock.short_term.action in ("STRONG BUY", "BUY"):
                        st.success(
                            f"**BUY plan:** {stock.short_term.entry_hint} · "
                            f"Stop: {stock.short_term.stop_hint} · Target: {stock.short_term.target_hint}"
                        )
            with t3:
                if stock.long_term:
                    st.metric("Suggestion", stock.long_term.action)
                    st.caption(stock.long_term.summary)
                    for sig in (stock.long_term.chart_signals or [])[:5]:
                        st.markdown(f"- {sig}")
                    if stock.long_chart_df is not None:
                        st.plotly_chart(
                            price_chart(stock.long_chart_df, stock.symbol),
                            use_container_width=True,
                            key=f"top_long_{stock.nse_symbol}",
                        )
                    if stock.long_term.action in ("CORE BUY", "ACCUMULATE"):
                        st.success(
                            f"**BUY plan:** {stock.long_term.entry_hint} · "
                            f"Stop: {stock.long_term.stop_hint} · Target: {stock.long_term.target_hint}"
                        )
