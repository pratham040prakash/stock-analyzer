"""Always-visible live strip: stars · OR · option entry gate."""

from __future__ import annotations

import streamlit as st

from analyzer.market_session import market_session_status
from analyzer.opening_range_confirm import fetch_symbol_opening_range
from analyzer.options_entry_gate import assess_pick_entry_gate, gate_label_short
from analyzer.options_reversal_alerts import INDEX_LABEL, INDEX_YAHOO
from analyzer.options_trade_selection import load_selected_option
from analyzer.providers import get_live_ltp
from analyzer.session_phase import suggestions_ui_phase
from analyzer.trade_selection import load_selected_symbols, selection_status_line


def _index_or_line(fno: str, market: str) -> str:
    yahoo = INDEX_YAHOO.get(fno.upper())
    if not yahoo:
        return "—"
    spot, _ = get_live_ltp(yahoo, market=market)
    rng = fetch_symbol_opening_range(yahoo, market=market)
    label = INDEX_LABEL.get(fno.upper(), fno)
    if not rng or spot is None:
        return f"{label}: OR loading…"
    hi, lo = rng
    inside = lo <= spot <= hi
    pos = "inside" if inside else ("above" if spot > hi else "below")
    return f"{label} ₹{spot:,.0f} · OR {lo:,.0f}–{hi:,.0f} · **{pos}**"


def render_live_session_strip(*, market: str = "india") -> None:
    """Top-of-Suggestions strip during live and pre-market open."""
    phase = suggestions_ui_phase()
    session = market_session_status()
    if phase not in ("live", "pre_market") and not session.get("is_open"):
        return

    st.markdown("#### ⚡ Live session")

    stars = load_selected_symbols()
    opt = load_selected_option()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.caption("**Stocks (star 2)**")
        if stars:
            st.markdown(", ".join(f"⭐ {s}" for s in stars))
        else:
            st.markdown(selection_status_line() or "— none starred —")
    with c2:
        st.caption("**Nifty OR**")
        st.markdown(_index_or_line("NIFTY", market))
    with c3:
        st.caption("**Bank Nifty OR**")
        st.markdown(_index_or_line("BANKNIFTY", market))
    with c4:
        st.caption("**Option leg gate**")
        if opt:
            class _P:
                fno_symbol = opt["fno_symbol"]
                option_type = opt["option_type"]
                strike = opt["strike"]

            gate = assess_pick_entry_gate(_P(), market=market)
            if gate:
                st.markdown(f"{gate.emoji} **{opt['fno_symbol']} {opt['option_type']} {opt['strike']:g}**")
                st.caption(gate_label_short(gate))
            else:
                st.markdown(f"⭐ {opt['fno_symbol']} {opt['option_type']} {opt['strike']:g}")
        else:
            st.caption("Star one CE/PE in Options section")

    if phase == "pre_market":
        st.info("**9:15–9:45** — observe OR only. No stock or option entries yet.")
    elif session.get("is_open"):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        if now.hour == 9 and now.minute < 45:
            st.info("**9:15–9:45** — observe OR only. No stock or option entries yet.")
