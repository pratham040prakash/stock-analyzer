"""Proof Canvas session flags only — no mapper, SVG, or chart imports."""

from __future__ import annotations

import streamlit as st

PROOF_OVERLAY_OPEN = "proof_overlay_open"
PROOF_ORIGIN = "proof_origin"
PROOF_MODE = "proof_mode"
PROOF_SYMBOL = "proof_symbol"
PROOF_FOSSIL_DATE = "proof_fossil_date"
PROOF_ASK_QUERY = "proof_ask_query"
PROOF_ASK_WORD = "proof_ask_word"
PROOF_MISS_NOTE = "proof_miss_note"
PROOF_SHOW_CANDLES = "proof_show_candles"


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
