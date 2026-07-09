"""One-tap daily MIS cheat sheet on Suggestions."""

from __future__ import annotations

import streamlit as st

from analyzer.session_phase import suggestions_ui_phase

_CHEATSHEET = """
**Night** — Prep · star 2 stocks + 1 option · print checklist · set capital  
**8:45** — Telegram prep · Kite logged in · confirm stars  
**9:15–9:45** — **OBSERVE ONLY** — note OR high/low (no entries)  
**9:46+** — Re-scan CE/PE · check **Gate** column (🔴 = skip)  
**Options** — PE only if spot ≤ OR low · CE only if spot ≥ OR high · skip >3.5% OTM  
**Chop** — Sideways advisor (iron condor / credit spread), not buying CE/PE  
**Every entry** — stop on Kite **first** · only starred names  
**T1** — book 40–50% · trail stop to breakeven  
**3:20 PM** — square off **all** MIS + options  
**After close** — trade journal: mistake + fix · review Track Record  
**Rule** — 2 stops hit → done for the day
"""


def render_daily_cheat_sheet(*, key_prefix: str = "cheat") -> None:
    phase = suggestions_ui_phase()
    expanded = phase in ("live", "pre_market")
    with st.expander("📋 Daily cheat sheet (tap when rushed)", expanded=expanded):
        st.markdown(_CHEATSHEET.strip())
        st.caption(
            "Full checklist also in **Printable MIS checklist** (Prep section) "
            "and **Daily MIS checklist** expander."
        )
