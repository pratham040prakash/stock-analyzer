"""Compact morning strip: Gift Nifty · 2 stars · OR · ladder · Kite."""

from __future__ import annotations

from datetime import timedelta

import streamlit as st

from analyzer.data_health import build_data_health
from analyzer.gift_nifty import fetch_gift_nifty_cue
from analyzer.kite_status import kite_connection_status
from analyzer.market_session import market_session_status
from analyzer.opening_range_confirm import confirm_or_entry, fetch_symbol_opening_range
from analyzer.options_trade_selection import load_selected_option, option_selection_status_line
from analyzer.providers import get_live_ltp
from analyzer.trade_selection import effective_trade_plans, load_selected_symbols, selection_status_line
from analyzer.watchlist_pins import load_pinned_plans
from analyzer.watchlist_plan_tracker import assess_live_plan
from analyzer.zerodha import get_kite_login_url, load_env_credentials

_LADDER_STAGE_LABEL = {
    0: "→ T1",
    1: "T1 ✓",
    2: "T2 ✓",
    3: "T3 ✓",
}


def _gift_nifty_text() -> tuple[str, str]:
    cue = fetch_gift_nifty_cue()
    if not cue:
        return "—", "Gap cue unavailable"
    chg = f"{cue.change_1d_pct:+.2f}%" if cue.change_1d_pct is not None else "—"
    return chg, f"₹{cue.price:,.0f}"


def _or_summary(symbol: str, market: str) -> str:
    ltp, _ = get_live_ltp(symbol, market=market)
    or_rng = fetch_symbol_opening_range(symbol, market=market)
    if not or_rng or ltp is None:
        return "—"
    or_high, or_low = or_rng
    pins = {p.symbol.upper(): p for p in load_pinned_plans()}
    plan = pins.get(symbol.upper())
    entry = float(plan.entry) if plan else ltp
    side = plan.side if plan else "LONG"
    status = confirm_or_entry(
        ltp, entry=entry, or_high=or_high, or_low=or_low, side=side,
    )
    return f"{status.emoji} {status.label}"


def _ladder_summary(symbol: str, market: str) -> str:
    pins = {p.symbol.upper(): p for p in load_pinned_plans()}
    plan = pins.get(symbol.upper())
    if not plan:
        return "—"
    ltp, _ = get_live_ltp(symbol, market=market)
    status = assess_live_plan(
        ltp,
        entry=plan.entry,
        stop_loss=plan.stop_loss,
        target=plan.target,
        symbol=symbol,
        side=plan.side,
    )
    stage = _LADDER_STAGE_LABEL.get(status.ladder_stage, "—")
    ltp_s = f"₹{ltp:,.0f}" if ltp else "—"
    return f"{stage} · {ltp_s}"


def _kite_summary() -> tuple[str, str]:
    status = kite_connection_status(probe=True)
    level = status.get("level", "ok")
    if level == "ok":
        nfo = " · NFO ✓" if status.get("nfo_ok") else ""
        return "✅ OK", f"Live{nfo}"
    if level == "expired":
        return "❌ Expired", "Refresh token"
    if level == "no_token":
        return "⚠️ Login", "Token missing"
    return "⚠️ Setup", "Add API key"


def _render_cockpit_body(market: str, *, key_prefix: str = "cockpit") -> None:
    session = market_session_status()
    health = build_data_health()
    stars = load_selected_symbols()
    gift_chg, gift_px = _gift_nifty_text()
    kite_main, kite_sub = _kite_summary()

    st.markdown(
        f"##### ☀️ {'Live session — your picks' if session.get('is_open') else 'Morning cockpit'}"
    )
    if session.get("is_open") and health.warning:
        st.warning(health.warning)
    st.caption(
        f"{session.get('status', '—')} · {session.get('time_ist', '')} · "
        f"{selection_status_line()} · {option_selection_status_line()}"
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Gift Nifty", gift_chg, delta=gift_px)
    c2.metric("Your 2", stars[0] if stars else "—")
    if len(stars) > 1:
        c2.caption(stars[1])
    elif not stars:
        c2.caption("Star below")

    if stars:
        or_line = " · ".join(f"{s} {_or_summary(s, market)}" for s in stars[:2])
        lad_line = " · ".join(f"{s} {_ladder_summary(s, market)}" for s in stars[:2])
        lad_head = _ladder_summary(stars[0], market).split(" · ")[0]
    else:
        or_line = "Star picks first"
        lad_line = "—"
        lad_head = "—"

    c3.metric("OR", stars[0] if stars else "—")
    c3.caption(_or_summary(stars[0], market) if stars else or_line)

    c4.metric("Ladder", lad_head)
    c4.caption(lad_line if stars else lad_line)

    c5.metric("Kite", kite_main.replace("✅ ", "").replace("❌ ", "").replace("⚠️ ", ""))
    c5.caption(kite_sub)
    if kite_main != "✅ OK":
        creds = load_env_credentials()
        if creds.get("api_key"):
            st.link_button(
                "Login with Zerodha",
                get_kite_login_url(creds["api_key"]),
                key=f"{key_prefix}_kite_login",
                use_container_width=True,
            )
        else:
            if st.button("Setup Kite", key=f"{key_prefix}_kite_fix", use_container_width=True):
                from ui.navigation import request_nav_tab
                request_nav_tab("My Portfolio")

    opt = load_selected_option()
    if opt:
        st.caption(
            f"Option leg: **{opt['fno_symbol']} {opt['option_type']} {opt['strike']:g}**"
        )
    elif not stars:
        plans = effective_trade_plans()
        if plans:
            st.caption("Ready: " + ", ".join(p.symbol for p in plans[:2]))


@st.fragment(run_every=timedelta(seconds=60))
def _cockpit_fragment(market: str, *, key_prefix: str = "cockpit") -> None:
    _render_cockpit_body(market, key_prefix=key_prefix)


def render_morning_cockpit(market: str, *, key_prefix: str = "cockpit") -> None:
    """One-strip status for pre-open and live session."""
    if market_session_status().get("is_open"):
        _cockpit_fragment(market, key_prefix=key_prefix)
    else:
        _render_cockpit_body(market, key_prefix=key_prefix)
