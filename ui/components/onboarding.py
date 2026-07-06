"""Start here — suggestions + hit tracking workflow."""

from __future__ import annotations

import streamlit as st

from analyzer.intraday_pulse_source import load_pulse_for_watchlist
from analyzer.onboarding_state import dismiss_onboarding, is_onboarding_dismissed
from analyzer.watchlist_history import build_watchlist_success_report
from analyzer.watchlist_pins import load_pinned_plans
from ui.navigation import request_nav_tab


def _step_done(done: bool) -> str:
    return "✅" if done else "⬜"


def render_start_here_onboarding(market: str, *, force_show: bool = False) -> None:
    """3-step guide: Quick scan → trade → check hit rate."""
    if not force_show and is_onboarding_dismissed():
        return

    report, scan_status = load_pulse_for_watchlist(
        market,
        session_report=st.session_state.get("market_pulse_full"),
    )
    scan_ok = report is not None and scan_status in ("session", "cache_fresh", "cache_stale")
    picks_ok = len(load_pinned_plans()) > 0
    scored_ok = build_watchlist_success_report(7).scored_picks > 0

    with st.expander("🚀 Start here — suggestions workflow", expanded=not is_onboarding_dismissed()):
        st.markdown(
            "This app suggests stocks with **Entry · Stop · Target**, then checks "
            "whether the **target was hit** after market close."
        )

        st.markdown(
            f"{_step_done(scan_ok)} **1. Quick scan (after close)** — "
            "**Suggestions** tab → **Quick scan** saves top 5 for tomorrow."
        )
        if not scan_ok:
            if st.button("Go to Suggestions → Quick scan", key="onboard_scan", type="primary"):
                request_nav_tab("Suggestions", intraday_focus_watchlist=True)

        st.markdown(
            f"{_step_done(picks_ok)} **2. Trade tomorrow** — "
            "Use the list (star your top 2 if you want). Place stop on Kite first."
        )
        if scan_ok:
            if st.button("Open suggestions list", key="onboard_watchlist"):
                request_nav_tab("Suggestions", intraday_focus_watchlist=True)

        st.markdown(
            f"{_step_done(scored_ok)} **3. Check hit rate (after 3:30 PM)** — "
            "**Track Record** or **Suggestions** → see **Hit target?** column."
        )
        if st.button("Open Track Record", key="onboard_track"):
            request_nav_tab("Track Record")

        st.caption(
            "Kite login, options CE/PE, and Telegram are **optional** — "
            "see sidebar **Zerodha Kite** and **Advanced** expanders on Suggestions."
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Don't show again", key="onboard_dismiss"):
                dismiss_onboarding()
                st.rerun()
        with c2:
            if st.button("Hide for now", key="onboard_hide"):
                st.session_state["_onboarding_hidden_session"] = True
                st.rerun()


def render_sidebar_onboarding_button() -> None:
    if st.button("🚀 Start here guide", key="sidebar_start_here"):
        st.session_state["_onboarding_force_show"] = True
        st.rerun()
