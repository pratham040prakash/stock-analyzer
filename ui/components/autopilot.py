"""Sidebar Autopilot — schedule status and one-click Mac install."""

from __future__ import annotations

import streamlit as st

from analyzer.autopilot_status import (
    build_autopilot_status,
    install_autopilot_schedules,
    is_macos,
)
from analyzer.post_close_scan_scheduler import run_post_close_scan
from analyzer.morning_suggestions_scheduler import run_morning_suggestions
from analyzer.mis_eod_summary import run_mis_eod_summary


def render_autopilot_sidebar() -> None:
    status = build_autopilot_status()

    with st.expander(
        f"🤖 Autopilot ({status.schedules_installed}/{status.schedules_total} schedules)",
        expanded=status.schedules_installed == 0 and is_macos(),
    ):
        st.caption(
            f"Session **{status.trade_date}** · picks for **{status.prep_for}**"
        )
        for step in status.steps:
            icon = "✅" if step.done_today else ("⏳" if step.installed else "○")
            sched = f" · {step.schedule}" if step.schedule else ""
            install = " · scheduled" if step.installed else ""
            st.markdown(f"{icon} **{step.label}**{sched}{install}")
            if step.detail:
                st.caption(step.detail)

        st.caption(status.timezone_hint)

        if is_macos():
            if st.button("Enable autopilot on this Mac", key="autopilot_install", type="primary"):
                with st.spinner("Installing launchd schedules…"):
                    ok, msg = install_autopilot_schedules()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
        else:
            st.info("Run `streamlit run app.py` on your Mac to enable autopilot schedules.")

        with st.expander("Run step now (test)", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Quick scan now", key="autopilot_scan_now"):
                    with st.spinner("Scanning…"):
                        n, msg = run_post_close_scan(force=True, send_telegram=False)
                    st.toast(msg)
                    st.rerun()
                if st.button("Morning list now", key="autopilot_morning_now"):
                    n, msg = run_morning_suggestions(force=True)
                    st.toast(msg)
                    st.rerun()
            with c2:
                if st.button("EOD score now", key="autopilot_eod_now"):
                    with st.spinner("Scoring…"):
                        _, _, msg = run_mis_eod_summary(force=True)
                    st.toast(msg)
                    st.rerun()
