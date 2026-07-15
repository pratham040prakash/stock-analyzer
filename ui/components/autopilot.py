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


def render_autopilot_loop_strip() -> None:
    """Compact today's loop progress — all 10 autopilot steps."""
    status = build_autopilot_status()
    done = sum(1 for s in status.steps if s.done_today)
    total = len(status.steps)
    st.caption(f"**Autopilot loop** — **{done}/{total}** steps done today")
    cols = st.columns(total)
    for col, step in zip(cols, status.steps):
        icon = "✅" if step.done_today else ("⏳" if step.installed else "○")
        short = {
            "post_close_scan": "Scan",
            "eod_score": "EOD",
            "autopilot_health": "Health",
            "nightly_prep": "Prep",
            "auto_star_2": "Stars",
            "prep_morning_nag": "Nag",
            "morning_list": "AM TG",
            "session_open": "9:15",
            "morning_options": "9:46",
            "live_alerts": "Live",
        }.get(step.key, step.label[:6])
        col.caption(f"{icon} {short}")


def render_autopilot_home_readonly() -> None:
    """Read-only autopilot loop status for Cloud / non-Mac viewers."""
    status = build_autopilot_status()
    with st.expander(
        f"🤖 Autopilot status ({status.schedules_installed}/{status.schedules_total} schedules on Mac)",
        expanded=False,
    ):
        st.caption(
            f"Session **{status.trade_date}** · picks for **{status.prep_for}** · view-only on Cloud"
        )
        for step in status.steps:
            icon = "✅" if step.done_today else ("⏳" if step.installed else "○")
            st.markdown(f"{icon} **{step.label}** · {step.schedule or 'manual'}")
            if step.detail:
                st.caption(step.detail)
        st.caption(status.timezone_hint)
        if not is_macos():
            st.info("Install schedules on your Mac (`scripts/install_all_schedules.sh`) for zero-touch runs.")


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
