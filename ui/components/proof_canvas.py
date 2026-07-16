"""Proof Canvas — lazy Level-2 evidence surface (mapper/SVG/LWC on demand)."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ui.components.proof_state import (
    PROOF_ASK_QUERY,
    PROOF_ASK_WORD,
    PROOF_FOSSIL_DATE,
    PROOF_MISS_NOTE,
    PROOF_MODE,
    PROOF_ORIGIN,
    PROOF_SHOW_CANDLES,
    PROOF_SYMBOL,
    close_proof_overlay,
    close_proof_overlay_silent,
    is_proof_overlay_open,
    open_proof_overlay,
)

# Re-export session API for entry points that already import from proof_canvas.
__all__ = [
    "close_proof_overlay",
    "close_proof_overlay_silent",
    "is_proof_overlay_open",
    "open_proof_overlay",
    "render_proof_overlay",
]


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _load_proof_bundle_safe(market: str, period: str) -> dict[str, Any]:
    from ui.components.partner_data import clear_partner_caches_on_pickle_error, load_proof_bundle

    try:
        return load_proof_bundle(market, period)
    except Exception as exc:
        if clear_partner_caches_on_pickle_error(exc):
            return load_proof_bundle(market, period)
        raise


def _build_proof(market: str, cached: dict[str, Any]):
    from ui.components.proof_mapper import build_structure_proof

    return build_structure_proof(
        market=market,
        cached=cached,
        proof_mode=str(st.session_state.get(PROOF_MODE, "trade")),
        origin=str(st.session_state.get(PROOF_ORIGIN, "today")),
        symbol=str(st.session_state.get(PROOF_SYMBOL, "") or "") or None,
        fossil_date=str(st.session_state.get(PROOF_FOSSIL_DATE, "") or "") or None,
        ask_query=str(st.session_state.get(PROOF_ASK_QUERY, "") or "") or None,
        ask_answer_word=str(st.session_state.get(PROOF_ASK_WORD, "") or "") or None,
        miss_note=str(st.session_state.get(PROOF_MISS_NOTE, "") or "") or None,
    )


def _handle_primary(proof) -> None:
    from ui.components.proof_state import _close_proof_state

    origin = proof.origin
    _close_proof_state()
    if origin == "ask":
        from ui.components.answer_canvas import ASK_OVERLAY_OPEN

        st.session_state[ASK_OVERLAY_OPEN] = True
        st.rerun()
        return
    if origin == "trust":
        from ui.components.partner_shell import PARTNER_DEPTH_KEY, TRUST_DEPTH, set_partner_dock

        st.session_state[PARTNER_DEPTH_KEY] = TRUST_DEPTH
        set_partner_dock("you")
        return
    st.rerun()


def render_proof_overlay(*, market: str, period: str = "1y", cached: dict[str, Any] | None = None) -> None:
    """Render Proof Canvas — loads mapper, SVG, and charts only when this runs."""
    from ui.components.home_dashboard import _broker_snapshot, _sync_status
    from ui.components.proof_svg import render_proof_svg

    if cached is None:
        cached = _load_proof_bundle_safe(market, period)

    proof = _build_proof(market, cached)
    broker = _broker_snapshot()
    sync_cls, dot_cls, sync_label = _sync_status(broker)
    built_at = str(cached.get("built_at", ""))
    show_candles = bool(st.session_state.get(PROOF_SHOW_CANDLES))

    badge = ""
    if proof.fossil_badge:
        badge = f'<p class="proof-fossil-badge">{_esc(proof.fossil_badge)}</p>'

    st.markdown(
        f'<div class="verdict-canvas-root proof-canvas-root" data-proof-state="{_esc(proof.verdict_state)}">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f"{badge}"
        f'<p class="proof-echo">{_esc(proof.echo_line)}</p>'
        f'<p class="proof-mentor">{_esc(proof.mentor_line)}</p>'
        f"{render_proof_svg(proof)}"
        f'<p class="proof-action">{_esc(proof.action_line)}</p>',
        unsafe_allow_html=True,
    )

    if show_candles and proof.candles:
        from ui.components.proof_lwc import render_proof_lwc

        st.markdown('<div class="proof-lwc-wrap">', unsafe_allow_html=True)
        render_proof_lwc(proof, height=180)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-primary proof-primary">', unsafe_allow_html=True)
    if st.button(proof.primary_label, key="prf_primary", type="primary", use_container_width=True):
        _handle_primary(proof)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-ghost-row proof-ghost">', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        if st.button("Show raw candles", key="prf_candles", use_container_width=True):
            st.session_state[PROOF_SHOW_CANDLES] = not show_candles
            st.rerun()
    with g2:
        if proof.proof_mode == "fossil":
            st.markdown('<span class="proof-ghost-static">Fossil — not live</span>', unsafe_allow_html=True)
        elif proof.verdict_state == "trade":
            if st.button("What if wrong?", key="prf_alt", use_container_width=True):
                st.toast("Alternative path dashed on chart when sellers return.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-secondary">', unsafe_allow_html=True)
    if st.button("✕ Close", key="prf_close", use_container_width=True):
        close_proof_overlay()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<p class="vc-foot proof-foot">Annotations are AI-drawn evidence — not a charting workspace.</p></div>',
        unsafe_allow_html=True,
    )
