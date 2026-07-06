"""Options expiry watchlist UI — Nifty / Bank Nifty CE/PE."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from analyzer.affordable_invest import (
    DEFAULT_MAX_OPTION_LOT_COST_INR,
    OPTION_LOT_BUDGET_OPTIONS,
)
from analyzer.intraday_data import INTERVAL_OPTIONS, fetch_intraday
from analyzer.intraday_pulse_source import (
    DEFAULT_INTRADAY_PULSE_PERIOD,
    load_pulse_for_watchlist,
)
from analyzer.market_session import market_session_status
from analyzer.nse_options import fetch_option_leg_ltp
from analyzer.nse_session import get_recent_nse_errors, nse_status_message, reset_nse_circuit
from analyzer.options_expiry_watchlist import OptionsExpiryWatchlist, build_options_expiry_watchlist
from analyzer.options_premium_chart import (
    _INDEX_YAHOO,
    fetch_option_premium_intraday,
    index_context_chart,
    ladder_for_pick,
    options_premium_chart,
)
from analyzer.prep_status import mark_prep_step
from analyzer.providers import is_kite_live
from analyzer.trade_ladder import format_stop_trail_guide
from analyzer.watchlist_plan_tracker import assess_options_live_plan
from analyzer.telegram_notify import telegram_configured
from analyzer.watchlist_profit import format_expected_profit, options_target_profit_one_lot
from ui.components.prep_all import send_combined_telegram_from_session
from ui.navigation import request_nav_tab
from ui.theme import OPTIONS_COLORS

_CACHE_KEY = "options_expiry_watchlist_cache"
_CACHE_BUDGET_KEY = "options_expiry_watchlist_budget"
_LOADED_KEY = "options_expiry_loaded"


def _render_options_live_status(p, market: str) -> None:
    prem = fetch_option_leg_ltp(
        p.fno_symbol, p.option_type, p.strike, expiry=p.expiry,
    )
    status = assess_options_live_plan(
        prem,
        entry=float(p.premium or 0),
        stop_loss=float(p.stop_premium or 0),
        target=float(p.target_premium or 0),
        label=f"{p.fno_symbol} {p.option_type}",
    )
    src = "NSE" if prem else "—"
    st.caption(f"{status.emoji} **{status.label}** — {status.detail} ({src})")
    if status.ladder_note:
        st.caption(f"Ladder: {status.ladder_note}")


def _render_options_plan_chart(p, market: str, interval: str) -> None:
    ladder = ladder_for_pick(p)
    title = f"{p.fno_symbol} {p.option_type} {p.strike:g} premium"
    key_base = f"{p.fno_symbol}_{p.option_type}_{p.strike:g}_{interval}"

    result = fetch_option_premium_intraday(
        fno_symbol=p.fno_symbol,
        strike=p.strike,
        expiry=p.expiry,
        option_type=p.option_type,
        interval=interval,
    )
    if result:
        df, meta = result
        st.plotly_chart(
            options_premium_chart(df, ladder, title=title),
            use_container_width=True,
            key=f"opt_prem_chart_{key_base}",
        )
        st.caption(
            f"**Premium chart** · Stop ₹{ladder.initial_stop:,.2f} · Entry ₹{ladder.entry:,.2f} · "
            f"T1 ₹{ladder.target:,.2f} · T2 ₹{ladder.target2:,.2f} · T3 ₹{ladder.target3:,.2f} · "
            f"{meta.source}"
        )
        st.caption(format_stop_trail_guide(ladder))
        return

    yahoo = _INDEX_YAHOO.get(p.fno_symbol.upper())
    if yahoo:
        try:
            idx_df, idx_meta = fetch_intraday(yahoo, interval=interval, market=market)
            if idx_df is not None and len(idx_df) >= 5:
                st.caption(
                    "Premium candles need **Kite + NFO data** — showing **index** chart with strike. "
                    "Premium plan lines are in the table above."
                )
                st.plotly_chart(
                    index_context_chart(
                        idx_df,
                        strike=p.strike,
                        spot=p.spot,
                        title=f"{p.name} spot vs strike",
                    ),
                    use_container_width=True,
                    key=f"opt_idx_chart_{key_base}",
                )
                st.caption(f"Index: {idx_meta.get('source', '—')}")
        except Exception as exc:
            st.caption(f"Index chart unavailable: {exc}")

    st.info(
        "Connect **ZERODHA_ACCESS_TOKEN** in `.env` for live **option premium** candles "
        f"with stop / T1 / T2 / T3 lines. Current prem plan: "
        f"entry ₹{ladder.entry:,.2f} · stop ₹{ladder.initial_stop:,.2f} · "
        f"T1 ₹{ladder.target:,.2f} · T2 ₹{ladder.target2:,.2f} · T3 ₹{ladder.target3:,.2f}."
    )
    st.caption(format_stop_trail_guide(ladder))


@st.fragment(run_every=timedelta(seconds=60))
def _options_plan_charts_panel(picks, market: str, interval: str) -> None:
    _render_options_plan_charts_body(picks, market, interval)


def _render_options_plan_charts_body(picks, market: str, interval: str) -> None:
    for p in picks:
        star = "★ " if p.recommended else ""
        with st.expander(
            f"{star}{p.fno_symbol} {p.option_type} {p.strike:g} — premium chart & levels",
            expanded=p.recommended,
        ):
            _render_options_live_status(p, market)
            _render_options_plan_chart(p, market, interval)


def _render_options_plan_charts(picks, market: str, *, auto_refresh: bool) -> None:
    if not picks:
        return
    st.markdown("##### 📈 Live charts — premium · stop · T1/T2/T3")
    kite = is_kite_live()
    st.caption(
        f"Premium candles: **{'Kite NFO' if kite else 'Kite not connected — index + strike fallback'}** · "
        "Yellow = entry · Red = stop · Green dashed = T1/T2/T3 (on premium chart)"
    )
    interval = INTERVAL_OPTIONS[
        st.selectbox(
            "Options chart interval",
            list(INTERVAL_OPTIONS.keys()),
            index=1,
            key="opt_plan_chart_interval",
        )
    ]
    if auto_refresh:
        _options_plan_charts_panel(picks, market, interval)
    else:
        _render_options_plan_charts_body(picks, market, interval)


def _render_pick_expander(p) -> None:
    with st.expander(f"Details — {p.fno_symbol} {p.option_type} {p.strike:g}", expanded=False):
        st.markdown(f"**Signal:** {p.signal}")
        st.caption(p.reason)
        t2 = getattr(p, "target2_premium", None)
        t3 = getattr(p, "target3_premium", None)
        if t2 and t3 and p.premium:
            from analyzer.trade_ladder import build_options_ladder

            ol = build_options_ladder(
                float(p.premium),
                stop_mult=(p.stop_premium or 0) / p.premium if p.stop_premium else 0.65,
                target_mults=(
                    (p.target_premium or 0) / p.premium,
                    t2 / p.premium,
                    t3 / p.premium,
                ),
            )
            st.caption(format_stop_trail_guide(ol))
            st.caption(
                f"T1 ₹{p.target_premium:,.2f} (40%) → T2 ₹{t2:,.2f} (30%) → T3 ₹{t3:,.2f} (30%)"
            )
        else:
            st.caption(
                "Stop = ~35% premium loss · T1 = ~50% premium gain (ladder extends to T2/T3). "
                "Also use underlying VWAP/OR for exit — not premium alone."
            )


def _fetch_watchlist(
    report,
    *,
    max_lot_cost: float,
    period: str,
    market: str,
) -> OptionsExpiryWatchlist:
    """Fetch once per budget; cache in session (~15s NSE call)."""
    cached = st.session_state.get(_CACHE_KEY)
    cached_budget = st.session_state.get(_CACHE_BUDGET_KEY)
    if cached is not None and cached_budget == max_lot_cost:
        return cached

    with st.spinner("Fetching Nifty & Bank Nifty option chains… ~15s"):
        wl = build_options_expiry_watchlist(
            report,
            max_lot_cost=max_lot_cost,
            period=period,
            market=market,
        )
    st.session_state[_CACHE_KEY] = wl
    st.session_state[_CACHE_BUDGET_KEY] = max_lot_cost
    if wl.picks:
        from analyzer.options_watchlist_history import save_options_watchlist_snapshot

        save_options_watchlist_snapshot(
            wl.picks,
            prep_date=market_session_status().get("date", ""),
        )
        mark_prep_step("options")
    return wl


def _render_telegram_export(wl: OptionsExpiryWatchlist, *, market_bias: str = "") -> None:
    if not wl.picks:
        return
    if telegram_configured():
        if st.button("Send MIS prep to Telegram", key="opt_wl_tg", type="secondary"):
            ok, err = send_combined_telegram_from_session(
                options_picks=wl.picks,
                market_bias=market_bias,
            )
            if ok:
                st.success("Equity + options sent to Telegram.")
            else:
                st.error(err)
    else:
        st.caption("Subscribe to Telegram in sidebar to export picks.")


def render_options_expiry_watchlist_section(wl: OptionsExpiryWatchlist, *, market: str = "india") -> None:
    st.markdown("#### 📅 Options expiry watchlist (Nifty & Bank Nifty)")
    st.caption(wl.routine_note)

    if not wl.nse_available:
        status = nse_status_message()
        st.warning(status or "Could not reach NSE options API.")
        for err in get_recent_nse_errors()[:3]:
            st.caption(f"· {err}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Retry NSE", key="opt_wl_retry_nse"):
                reset_nse_circuit()
                st.session_state.pop(_CACHE_KEY, None)
                st.rerun()
        with c2:
            if st.button("Open NSE Options tab", key="opt_wl_nse_tab"):
                request_nav_tab("NSE Options")
        return

    if wl.errors:
        for err in wl.errors:
            st.warning(err)

    if not wl.picks:
        st.info(
            "No CE/PE picks under your lot budget. "
            "Raise **Max 1-lot cost** or tap **Refresh CE/PE** during market hours."
        )
        return

    rec_count = sum(1 for p in wl.picks if p.recommended)
    st.success(
        f"**{len(wl.picks)}** CE/PE row(s) — **{rec_count}** signal-aligned (★)."
    )

    star_only = st.checkbox(
        "Show ★ signal side only",
        value=bool(st.session_state.get("options_star_only", False)),
        key="options_star_only",
        help="Hide reference CE/PE rows when you only trade the signal side.",
    )
    display_picks = [p for p in wl.picks if p.recommended] if star_only else wl.picks
    if star_only and not display_picks:
        st.info("No ★ rows — widen lot budget or refresh during market hours.")
        return

    table = []
    for p in display_picks:
        star = "★ " if p.recommended else ""
        table.append({
            "Rank": p.rank,
            "Index": p.fno_symbol,
            "Expiry": p.expiry,
            "Signal": p.signal,
            "Side": f"{star}{p.option_type}",
            "Strike": f"{p.strike:g}",
            "Entry (prem)": f"₹{p.premium:,.2f}" if p.premium else "—",
            "Stop (start)": f"₹{p.stop_premium:,.2f}" if p.stop_premium else "—",
            "Stop@T1": f"₹{p.stop_after_t1:,.2f}" if getattr(p, "stop_after_t1", None) else "—",
            "Stop@T2": f"₹{p.stop_after_t2:,.2f}" if getattr(p, "stop_after_t2", None) else "—",
            "Stop@T3": f"₹{p.stop_after_t3:,.2f}" if getattr(p, "stop_after_t3", None) else "—",
            "T1 (prem)": f"₹{p.target_premium:,.2f}" if p.target_premium else "—",
            "T2 (prem)": f"₹{p.target2_premium:,.2f}" if p.target2_premium else "—",
            "T3 (prem)": f"₹{p.target3_premium:,.2f}" if p.target3_premium else "—",
            "Exp. profit (1 lot)": format_expected_profit(
                options_target_profit_one_lot(p.premium, p.target_premium, p.lot_size)
            ),
            "Lot": p.lot_size,
            "1-lot ₹": f"₹{p.lot_cost:,.0f}" if p.lot_cost else "—",
            "IV%": f"{p.iv:.1f}" if p.iv else "—",
            "Spot": f"₹{p.spot:,.0f}",
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    show_live = market_session_status().get("is_open", False)
    _render_options_plan_charts(display_picks, market, auto_refresh=show_live)

    for p in wl.picks:
        if not p.recommended:
            continue
        color = OPTIONS_COLORS.get(p.signal, "#ffd600")
        st.markdown(
            f"**{p.rank}. {p.name}** — "
            f"<span style='color:{color};font-weight:700'>{p.signal}</span> · "
            f"**★ {p.option_type} {p.strike:g}** @ ₹{p.premium or 0:,.2f}",
            unsafe_allow_html=True,
        )
        _render_pick_expander(p)

    _render_telegram_export(wl, market_bias=wl.picks[0].signal if wl.picks else "")

    st.caption(
        "★ = signal-aligned side · **Entry (prem)** = buy price per CE/PE unit. "
        "Both CE and PE shown per index under your lot budget. "
        "Picks are **saved for track record** below."
    )


def render_options_expiry_watchlist_block(
    market: str,
    *,
    period: str = DEFAULT_INTRADAY_PULSE_PERIOD,
) -> None:
    """Options expiry section on Intraday tab — lazy-load on user action."""
    st.markdown("### 📅 Options expiry watchlist")
    st.caption(
        "Nifty & Bank Nifty **CE/PE** — strike, premium, stop & target for nearest expiry. "
        "Tap **Load CE/PE** when ready (~15s NSE fetch)."
    )

    budget_opts = [int(x) for x in OPTION_LOT_BUDGET_OPTIONS]
    default_budget = int(
        st.session_state.get("options_lot_budget", DEFAULT_MAX_OPTION_LOT_COST_INR)
    )
    if default_budget not in budget_opts:
        budget_opts = sorted(set(budget_opts + [default_budget]))

    loaded = bool(st.session_state.get(_LOADED_KEY))

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        max_lot_cost = st.selectbox(
            "Max 1-lot cost (₹)",
            options=budget_opts,
            index=budget_opts.index(default_budget)
            if default_budget in budget_opts
            else budget_opts.index(DEFAULT_MAX_OPTION_LOT_COST_INR),
            key="options_lot_budget",
            help="Premium × lot size must fit this budget.",
        )
    with c2:
        if not loaded:
            if st.button("Load CE/PE", type="primary", key="opt_wl_load"):
                st.session_state[_LOADED_KEY] = True
                st.session_state.pop(_CACHE_KEY, None)
                st.session_state.pop(_CACHE_BUDGET_KEY, None)
                reset_nse_circuit()
                st.rerun()
        else:
            if st.button("Refresh CE/PE", type="primary", key="opt_wl_fetch"):
                st.session_state.pop(_CACHE_KEY, None)
                st.session_state.pop(_CACHE_BUDGET_KEY, None)
                reset_nse_circuit()
                st.rerun()
    with c3:
        if loaded and st.button("Hide", key="opt_wl_hide"):
            st.session_state[_LOADED_KEY] = False
            st.session_state.pop(_CACHE_KEY, None)
            st.session_state.pop(_CACHE_BUDGET_KEY, None)
            st.rerun()

    if not loaded:
        st.info(
            "Options chains are **not loaded** — page stays fast until you tap **Load CE/PE**."
        )
        return

    session_report = st.session_state.get("market_pulse_full")
    report, _status = load_pulse_for_watchlist(market, period, session_report=session_report)

    try:
        wl = _fetch_watchlist(
            report if report and getattr(report, "stock_map", None) else None,
            max_lot_cost=float(max_lot_cost),
            period=period,
            market=market,
        )
    except Exception as exc:
        st.error(f"Options fetch failed: {exc}")
        for err in get_recent_nse_errors()[:3]:
            st.caption(err)
        if st.button("Retry", key="opt_wl_retry_exc"):
            reset_nse_circuit()
            st.session_state.pop(_CACHE_KEY, None)
            st.rerun()
        return

    render_options_expiry_watchlist_section(wl, market=market)
