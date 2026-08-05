"""Render Investment OS modules on Home."""
# APEX-012-LIFECYCLE: QUARANTINED

from __future__ import annotations

import html

import streamlit as st

from analyzer.investment_os import InvestmentOS, OSModule


_STATUS_CLASS = {
    "ok": "os-module-ok",
    "wait": "os-module-wait",
    "warn": "os-module-warn",
    "info": "os-module-info",
    "off": "os-module-off",
}

_VERDICT_CLASS = {
    "TRADE OK": "home-hero-ok",
    "WAIT": "home-hero-wait",
    "NO TRADE": "home-hero-wait",
    "PREP": "os-hero-prep",
    "CLOSED": "os-hero-closed",
}


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def render_os_module(mod: OSModule, *, index: int) -> None:
    cls = _STATUS_CLASS.get(mod.status, "os-module-info")
    conf = ""
    if mod.confidence_pct is not None:
        conf = f'<span class="os-conf">{mod.confidence_pct}%</span>'
    st.markdown(
        f'<div class="os-module {cls}">'
        f'<div class="os-module-head">'
        f'<span class="os-module-label">{index}. {_esc(mod.label)}</span>'
        f"{conf}"
        f"</div>"
        f'<p class="os-module-q">{_esc(mod.question)}</p>'
        f'<p class="os-module-answer">{_esc(mod.headline)}</p>'
        f'<p class="os-module-detail">{_esc(mod.detail)}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_os_header(os_report: InvestmentOS) -> None:
    hero_cls = _VERDICT_CLASS.get(os_report.verdict, "home-hero-wait")
    deep_note = " · live synthesis" if os_report.deep else ""
    st.markdown(
        f'<p class="os-brand">Investment Operating System{deep_note}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="home-hero {hero_cls}">'
        f"<h2>{_esc(os_report.verdict)}</h2>"
        f"<p>{_esc(os_report.session_status)} · goal <b>+₹{os_report.goal_inr:,}</b> · "
        f"max loss <b>₹{os_report.max_loss_inr:,}</b></p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="home-now"><b>Now:</b> {_esc(os_report.next_step)}</div>',
        unsafe_allow_html=True,
    )


def render_investment_os(os_report: InvestmentOS) -> None:
    render_os_header(os_report)
    for i, mod in enumerate(os_report.modules, start=1):
        render_os_module(mod, index=i)
