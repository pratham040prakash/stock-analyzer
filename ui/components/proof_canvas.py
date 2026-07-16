"""Proof Canvas — AI-native evidence overlay (Phase 6)."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ui.components.proof_lwc import render_proof_lwc
from ui.components.proof_mapper import build_structure_proof
from ui.components.proof_models import StructureProof
from ui.components.proof_svg import render_proof_svg

PROOF_OVERLAY_OPEN = "proof_overlay_open"
PROOF_ORIGIN = "proof_origin"
PROOF_MODE = "proof_mode"
PROOF_SYMBOL = "proof_symbol"
PROOF_FOSSIL_DATE = "proof_fossil_date"
PROOF_ASK_QUERY = "proof_ask_query"
PROOF_ASK_WORD = "proof_ask_word"
PROOF_MISS_NOTE = "proof_miss_note"
PROOF_SHOW_CANDLES = "proof_show_candles"


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def is_proof_overlay_open() -> bool:
    return bool(st.session_state.get(PROOF_OVERLAY_OPEN))


def _close_proof_state() -> None:
    st.session_state[PROOF_OVERLAY_OPEN] = False
    st.session_state.pop(PROOF_ORIGIN, None)
    st.session_state.pop(PROOF_MODE, None)
    st.session_state.pop(PROOF_SYMBOL, None)
    st.session_state.pop(PROOF_FOSSIL_DATE, None)
    st.session_state.pop(PROOF_ASK_QUERY, None)
    st.session_state.pop(PROOF_ASK_WORD, None)
    st.session_state.pop(PROOF_MISS_NOTE, None)
    st.session_state.pop(PROOF_SHOW_CANDLES, None)


def close_proof_overlay_silent() -> None:
    _close_proof_state()


def close_proof_overlay() -> None:
    _close_proof_state()
    st.rerun()


def open_proof_overlay(
    *,
    origin: str,
    proof_mode: str,
    symbol: str | None = None,
    fossil_date: str | None = None,
    ask_query: str | None = None,
    ask_answer_word: str | None = None,
    miss_note: str | None = None,
) -> None:
    st.session_state[PROOF_OVERLAY_OPEN] = True
    st.session_state[PROOF_ORIGIN] = origin
    st.session_state[PROOF_MODE] = proof_mode
    st.session_state[PROOF_SYMBOL] = symbol or ""
    st.session_state[PROOF_FOSSIL_DATE] = fossil_date or ""
    st.session_state[PROOF_ASK_QUERY] = ask_query or ""
    st.session_state[PROOF_ASK_WORD] = ask_answer_word or ""
    st.session_state[PROOF_MISS_NOTE] = miss_note or ""
    st.session_state[PROOF_SHOW_CANDLES] = False
    st.rerun()


def _load_proof(market: str, cached: dict[str, Any]) -> StructureProof:
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


def _handle_primary(proof: StructureProof) -> None:
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


def render_proof_overlay(*, market: str, cached: dict[str, Any]) -> None:
    from ui.components.home_dashboard import _broker_snapshot, _sync_status

    proof = _load_proof(market, cached)
    broker = _broker_snapshot()
    sync_cls, dot_cls, sync_label = _sync_status(broker)
    built_at = str(cached.get("built_at", ""))
    show_candles = bool(st.session_state.get(PROOF_SHOW_CANDLES))

    st.markdown('<div class="proof-canvas-overlay" data-proof-open="1">', unsafe_allow_html=True)

    close_col, _ = st.columns([1, 5])
    with close_col:
        st.markdown('<div class="pc-close-wrap">', unsafe_allow_html=True)
        if st.button("✕", key="pc_close"):
            close_proof_overlay()
        st.markdown("</div>", unsafe_allow_html=True)

    badge = ""
    if proof.fossil_badge:
        badge = f'<p class="proof-fossil-badge">{_esc(proof.fossil_badge)}</p>'

    st.markdown(
        f'<div class="proof-canvas-root" data-proof-state="{_esc(proof.verdict_state)}">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f"{badge}"
        f'<p class="proof-echo">{_esc(proof.echo_line)}</p>'
        f'<p class="proof-mentor">{_esc(proof.mentor_line)}</p>'
        f"{render_proof_svg(proof)}"
        f'<p class="proof-action">{_esc(proof.action_line)}</p></div>',
        unsafe_allow_html=True,
    )

    if show_candles and proof.candles:
        st.markdown('<div class="proof-lwc-wrap">', unsafe_allow_html=True)
        render_proof_lwc(proof, height=180)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-primary proof-primary">', unsafe_allow_html=True)
    if st.button(proof.primary_label, key="pc_primary", type="primary", use_container_width=True):
        _handle_primary(proof)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-ghost-row proof-ghost">', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        if st.button("Show raw candles", key="pc_candles", use_container_width=True):
            st.session_state[PROOF_SHOW_CANDLES] = not show_candles
            st.rerun()
    with g2:
        if proof.proof_mode == "fossil":
            st.markdown('<span class="proof-ghost-static">Fossil — not live</span>', unsafe_allow_html=True)
        elif proof.verdict_state == "trade":
            if st.button("What if wrong?", key="pc_alt", use_container_width=True):
                st.toast("Alternative path dashed on chart when sellers return.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<p class="vc-foot proof-foot">Annotations are AI-drawn evidence — not a charting workspace.</p>'
        "</div>",
        unsafe_allow_html=True,
    )
