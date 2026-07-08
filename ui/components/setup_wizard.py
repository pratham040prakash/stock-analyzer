"""Sidebar setup wizard — .env, Telegram, Kite, Autopilot."""

from __future__ import annotations

import streamlit as st

from analyzer.setup_status import build_setup_status, setup_complete


def render_setup_wizard_sidebar() -> None:
    steps = build_setup_status()
    done_count = sum(1 for s in steps if s.done)
    expanded = not setup_complete()

    with st.expander(f"⚙️ Setup ({done_count}/{len(steps)})", expanded=expanded):
        for step in steps:
            icon = "✅" if step.done else "⬜"
            st.markdown(f"{icon} **{step.label}**")
            st.caption(step.detail)

        if setup_complete():
            st.success("Core setup complete — Autopilot will fill data daily.")
        else:
            st.caption("Copy `.env.example` → `.env` and add your Kite API key. Telegram is optional.")
