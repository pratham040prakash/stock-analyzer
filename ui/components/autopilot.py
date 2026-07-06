"""Sidebar Autopilot — schedule status, Kite health, logs, one-click install."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from analyzer.autopilot_alerts import collect_autopilot_gaps
from analyzer.autopilot_status import (
    ROOT,
    build_autopilot_status,
    install_autopilot_schedules,
    is_macos,
)
from analyzer.data_health import build_data_health
from analyzer.mis_eod_summary import run_mis_eod_summary
from analyzer.morning_suggestions_scheduler import run_morning_suggestions
from analyzer.post_close_scan_scheduler import run_post_close_scan
from analyzer.structured_log import tail_log_lines


def render_autopilot_sidebar() -> None:
    status = build_autopilot_status()
    gaps = collect_autopilot_gaps()
    health = build_data_health()

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

        if gaps:
            for g in gaps:
                st.warning(g.replace("**", ""))

        if not health.ok_for_live_cockpit and health.warning:
            st.caption(f"Data: {health.warning}")

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

        log_paths = [
            ("Post-close", ROOT / "logs" / "post_close_scan.log"),
            ("EOD", ROOT / "logs" / "mis_eod_summary.log"),
            ("Morning", ROOT / "logs" / "morning_suggestions.log"),
        ]
        with st.expander("Recent logs", expanded=False):
            for label, path in log_paths:
                lines = tail_log_lines(path, 4)
                if lines:
                    st.caption(f"**{label}**")
                    st.code("\n".join(lines), language=None)

        with st.expander("Run step now (test)", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Quick scan now", key="autopilot_scan_now"):
                    with st.spinner("Scanning…"):
                        _, msg = run_post_close_scan(force=True, send_telegram=False)
                    st.toast(msg)
                    st.rerun()
                if st.button("Morning list now", key="autopilot_morning_now"):
                    _, msg = run_morning_suggestions(force=True)
                    st.toast(msg)
                    st.rerun()
            with c2:
                if st.button("EOD score now", key="autopilot_eod_now"):
                    with st.spinner("Scoring…"):
                        _, _, msg = run_mis_eod_summary(force=True)
                    st.toast(msg)
                    st.rerun()
