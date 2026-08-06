"""My Portfolio tab — manual entry, CSV, or Zerodha Kite."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from analyzer.advisor import generate_portfolio_advice
from analyzer.earnings_calendar import fetch_corporate_events
from analyzer.portfolio_live import (
    ensure_kite_stream_for_tracked,
    load_tracked_portfolio,
    refresh_holdings_ltp,
    sync_holdings_from_kite,
    sync_watchlist_from_kite_activity,
)
from analyzer.kite_watchlist_store import (
    load_kite_watchlist,
    parse_watchlist_text,
    save_kite_watchlist,
)
from analyzer.providers.router import is_kite_live
from analyzer.market_session import market_session_status
from analyzer.markets import format_price
from analyzer.portfolio import analyze_portfolio
from analyzer.portfolio_risk import compute_portfolio_risk
from analyzer.portfolio_store import (
    clear_saved_portfolio,
    load_saved_portfolio,
    make_manual_holding,
    portfolio_profile_key,
    save_portfolio,
)
from analyzer.zerodha import (
    ZerodhaHolding,
    ZerodhaImportResult,
    kite_to_yahoo,
    load_env_credentials,
    parse_holdings_csv,
    parse_kite_symbol_list,
)
from analyzer.intraday_prefs import load_intraday_prefs
from ui.components.broker_connect import render_portfolio_broker_gate
from ui.components.empty_states import empty_portfolio
from ui.components.partner_data import read_broker_snapshot
from ui.components.holdings_experience import render_holdings_surface
from ui.components.portfolio_command_center import (
    PORTFOLIO_HOLDINGS,
    PORTFOLIO_OVERVIEW,
    PORTFOLIO_REVIEW,
    get_portfolio_subtab,
    render_portfolio_overview_surface,
    render_portfolio_subnav,
)
from ui.components.portfolio_review_experience import render_portfolio_review_surface
from ui.navigation import request_nav_tab
from ui.theme import APEX_PARTNER_EXPERIENCE_CSS, PARTNER_PAGE_ACTIVATE_JS


def _persist_import(import_result: ZerodhaImportResult) -> None:
    st.session_state["zd_import"] = import_result
    if import_result.holdings:
        save_portfolio(import_result, profile=portfolio_profile_key())
    ensure_kite_stream_for_tracked(import_result, profile=portfolio_profile_key())


@st.fragment(run_every=timedelta(seconds=15))
def _render_live_portfolio_panel(profile: str) -> None:
    """Refresh Kite LTP every 15s during market hours."""
    session = market_session_status()
    if not session.get("is_open"):
        st.caption("Market closed — live prices resume at 9:15 AM IST.")
        return
    if not is_kite_live():
        st.caption("Live Kite quotes unavailable — using last synced prices.")
        return

    imp = st.session_state.get("zd_import")
    tracked = load_tracked_portfolio(imp, profile=profile, refresh_ltp=True)
    if not tracked.holdings:
        return

    st.session_state["zd_import"] = refresh_holdings_ltp(
        ZerodhaImportResult(
            holdings=[h for h in tracked.holdings if h.quantity > 0],
            errors=tracked.errors,
            source=tracked.source,
        )
    )

    rows = []
    for h in tracked.holdings:
        kind = "Holding" if h.quantity > 0 else "Watchlist"
        pnl = h.pnl
        pnl_pct = None
        if pnl is not None and h.average_price and h.quantity:
            cost = h.average_price * h.quantity
            pnl_pct = (pnl / cost * 100) if cost else None
        rows.append({
            "Type": kind,
            "Symbol": h.tradingsymbol,
            "Qty": int(h.quantity) if h.quantity else "—",
            "Avg": f"₹{h.average_price:,.2f}" if h.average_price else "—",
            "LTP": f"₹{h.last_price:,.2f}" if h.last_price else "—",
            "P&L": f"₹{pnl:,.0f}" if pnl is not None else "—",
            "P&L %": f"{pnl_pct:+.1f}%" if pnl_pct is not None else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(f"Live refresh · {session.get('time_ist', '')} · Kite WebSocket + REST")


def _render_kite_watchlist_panel(profile: str) -> None:
    st.markdown("#### Kite watchlist mirror")
    st.caption(
        "Kite **marketwatch has no API**. We auto-sync symbols from your **open positions "
        "and recent orders** after login. Paste any extra symbols from Kite marketwatch below."
    )
    existing = load_kite_watchlist(profile)
    creds = load_env_credentials()
    if creds.get("access_token"):
        if st.button("Sync watchlist from Kite activity", key="kite_wl_sync", use_container_width=True):
            with st.spinner("Reading positions & orders from Kite…"):
                added, total, errs = sync_watchlist_from_kite_activity(profile=profile)
                ensure_kite_stream_for_tracked(st.session_state.get("zd_import"), profile=profile)
                if added:
                    st.success(f"Added **{added}** symbols — **{total}** total in watchlist")
                elif total:
                    st.info(f"Watchlist up to date — **{total}** symbols")
                else:
                    st.warning("No symbols from Kite positions/orders yet.")
                for err in errs:
                    st.caption(err)
                st.rerun()
    if existing:
        st.caption(f"**{len(existing)}** watchlist symbols saved: {', '.join(s.replace('NSE:', '').replace('-EQ', '') for s in existing[:8])}"
                   + ("…" if len(existing) > 8 else ""))

    text = st.text_area(
        "Paste from Kite marketwatch",
        value="\n".join(existing) if existing else "",
        placeholder="NSE:RELIANCE-EQ\nNSE:TCS-EQ\nSBIN",
        height=100,
        key="kite_watchlist_paste",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save watchlist", key="kite_wl_save", use_container_width=True):
            syms = parse_watchlist_text(text)
            if not syms:
                st.error("No symbols found.")
            else:
                save_kite_watchlist(syms, profile=profile)
                ensure_kite_stream_for_tracked(st.session_state.get("zd_import"), profile=profile)
                st.success(f"Saved {len(syms)} watchlist symbols")
                st.rerun()
    with c2:
        if st.button("Clear watchlist", key="kite_wl_clear", use_container_width=True):
            save_kite_watchlist([], profile=profile)
            st.rerun()


def _maybe_sync_portfolio_from_kite() -> None:
    if not st.session_state.pop("_portfolio_sync_requested", False):
        return
    creds = load_env_credentials()
    if not creds.get("access_token"):
        return
    with st.spinner("Synchronizing portfolio…"):
        synced, err = sync_holdings_from_kite()
        if err:
            st.warning("Unable to sync holdings right now. Try again shortly.")
        elif synced:
            _persist_import(synced)
            from ui.broker.bootstrap import reset_broker_bootstrap

            reset_broker_bootstrap()
            st.success(f"Synced {len(synced.holdings)} holdings with live prices")
            st.rerun()


def _render_portfolio_overview_tab(*, period: str, prof: str) -> None:
    st.markdown(APEX_PARTNER_EXPERIENCE_CSS, unsafe_allow_html=True)
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)
    _maybe_sync_portfolio_from_kite()

    broker = read_broker_snapshot()
    import_result = st.session_state.get("zd_import")
    prefs = load_intraday_prefs()
    portfolio_section = None
    try:
        from analyzer.use_cases.decision_context_bundle import DecisionContextBundle
        from ui.components.partner_data import load_today_core

        bundle = load_today_core("india", period)
        portfolio_section = DecisionContextBundle.from_cache_dict(bundle).assemble_view_model(
            record_snapshot=False
        ).portfolio
    except Exception:
        portfolio_section = None

    render_portfolio_overview_surface(
        broker=broker,
        portfolio=import_result,
        prefs=prefs,
        portfolio_section=portfolio_section,
    )
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)


def _render_portfolio_holdings_tab(*, period: str, prof: str) -> None:
    st.markdown(APEX_PARTNER_EXPERIENCE_CSS, unsafe_allow_html=True)
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)
    _maybe_sync_portfolio_from_kite()

    broker = read_broker_snapshot()
    import_result = st.session_state.get("zd_import")
    if not import_result:
        saved = load_saved_portfolio(profile=prof)
        if saved:
            st.session_state["zd_import"] = saved
            import_result = saved
    prefs = load_intraday_prefs()
    portfolio_section = None
    try:
        from analyzer.use_cases.decision_context_bundle import DecisionContextBundle
        from ui.components.partner_data import load_today_core

        bundle = load_today_core("india", period)
        portfolio_section = DecisionContextBundle.from_cache_dict(bundle).assemble_view_model(
            record_snapshot=False
        ).portfolio
    except Exception:
        portfolio_section = None

    render_holdings_surface(
        broker=broker,
        portfolio=import_result,
        prefs=prefs,
        portfolio_section=portfolio_section,
    )
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)


def _render_portfolio_review_tab(*, period: str, prof: str) -> None:
    st.markdown(APEX_PARTNER_EXPERIENCE_CSS, unsafe_allow_html=True)
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)
    _maybe_sync_portfolio_from_kite()

    broker = read_broker_snapshot()
    import_result = st.session_state.get("zd_import")
    if not import_result:
        saved = load_saved_portfolio(profile=prof)
        if saved:
            st.session_state["zd_import"] = saved
            import_result = saved
    prefs = load_intraday_prefs()
    portfolio_section = None
    try:
        from analyzer.use_cases.decision_context_bundle import DecisionContextBundle
        from ui.components.partner_data import load_today_core

        bundle = load_today_core("india", period)
        portfolio_section = DecisionContextBundle.from_cache_dict(bundle).assemble_view_model(
            record_snapshot=False
        ).portfolio
    except Exception:
        portfolio_section = None

    render_portfolio_review_surface(
        broker=broker,
        portfolio=import_result,
        prefs=prefs,
        portfolio_section=portfolio_section,
    )
    st.markdown(PARTNER_PAGE_ACTIVATE_JS, unsafe_allow_html=True)


def render_zerodha(period: str) -> None:
    if msg := st.session_state.pop("_portfolio_auto_sync_msg", None):
        st.success(msg)

    prof = portfolio_profile_key()
    saved = load_saved_portfolio(profile=prof)
    if saved and not st.session_state.get("zd_import"):
        st.session_state["zd_import"] = saved

    st.subheader("Portfolio")
    active = get_portfolio_subtab()
    render_portfolio_subnav(active=active)
    if active == PORTFOLIO_HOLDINGS:
        _render_portfolio_holdings_tab(period=period, prof=prof)
    elif active == PORTFOLIO_REVIEW:
        _render_portfolio_review_tab(period=period, prof=prof)
    else:
        _render_portfolio_overview_tab(period=period, prof=prof)
