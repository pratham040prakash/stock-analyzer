"""Start here — first-run daily MIS workflow."""

from __future__ import annotations

import streamlit as st

from analyzer.intraday_pulse_source import load_pulse_for_watchlist
from analyzer.onboarding_state import dismiss_onboarding, is_onboarding_dismissed
from analyzer.providers import data_source_status
from analyzer.watchlist_pins import load_pinned_plans
from ui.navigation import request_nav_tab


def _step_done(done: bool) -> str:
    return "✅" if done else "⬜"


def render_start_here_onboarding(market: str, *, force_show: bool = False) -> None:
    """4-step guide: Kite → Quick scan → Pick 3 → Morning checklist."""
    if not force_show and is_onboarding_dismissed():
        return

    ds = data_source_status()
    kite_ok = bool(ds.get("kite_configured"))
    report, scan_status = load_pulse_for_watchlist(
        market,
        session_report=st.session_state.get("market_pulse_full"),
    )
    scan_ok = report is not None and scan_status in ("session", "cache_fresh", "cache_stale")
    picks_ok = len(load_pinned_plans()) > 0

    with st.expander("🚀 Start here — daily MIS workflow", expanded=not is_onboarding_dismissed()):
        st.markdown(
            "Your best edge is **tonight's watchlist** with **Entry · Stop · Target** already written. "
            "Follow these four steps every trading day."
        )

        st.markdown(
            f"{_step_done(kite_ok)} **1. Connect Kite (optional but best)** — "
            "Add `ZERODHA_ACCESS_TOKEN` in `.env` for live 5m candles and LTP."
        )
        if not kite_ok:
            st.caption(ds.get("upgrade_hint", "See sidebar → Data feeds."))
            if st.button("Open My Portfolio (Kite login)", key="onboard_kite"):
                request_nav_tab("My Portfolio")

        st.markdown(
            f"{_step_done(scan_ok)} **2. Quick scan watchlist** — "
            "After market close, scan Nifty 50 (1–2 min) on **Intraday**."
        )
        if not scan_ok:
            if st.button("Go to Intraday → Quick scan", key="onboard_scan", type="primary"):
                request_nav_tab("Intraday", intraday_focus_watchlist=True)

        st.markdown(
            f"{_step_done(picks_ok)} **3. Pin 2–3 names** — "
            "Tap **Pin ⭐** on watchlist cards — locks Entry · Stop · Target for tomorrow."
        )
        if scan_ok:
            if st.button("Open watchlist", key="onboard_watchlist"):
                request_nav_tab("Intraday", intraday_focus_watchlist=True)

        st.markdown(
            f"{_step_done(False)} **4. Morning checklist** — "
            "9:15 IST: open **Intraday**, tick the **Daily MIS checklist**, trade only your picks."
        )
        if st.button("Open Intraday checklist", key="onboard_checklist"):
            request_nav_tab("Intraday")

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
    """Re-open the start guide from the sidebar."""
    if st.button("🚀 Start here guide", key="sidebar_start_here"):
        st.session_state["_onboarding_force_show"] = True
        st.rerun()
