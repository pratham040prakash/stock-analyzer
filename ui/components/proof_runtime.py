"""Proof Canvas runtime gate — diagnostic rollback without touching Proof implementation.

Set PROOF_CANVAS_ENABLED = True to restore all Proof integration points.
"""

from __future__ import annotations

import streamlit as st

# Re-enable after diagnostic rollback — Proof loads only when user opens it.
PROOF_CANVAS_ENABLED = True

_SESSION_KEYS = (
    "proof_overlay_open",
    "proof_origin",
    "proof_mode",
    "proof_symbol",
    "proof_fossil_date",
    "proof_ask_query",
    "proof_ask_word",
    "proof_miss_note",
    "proof_show_candles",
)


def proof_canvas_active() -> bool:
    return PROOF_CANVAS_ENABLED


def is_proof_ui_open() -> bool:
    if not PROOF_CANVAS_ENABLED:
        return False
    from ui.components.proof_state import is_proof_overlay_open

    return is_proof_overlay_open()


def close_proof_ui_silent() -> None:
    if not PROOF_CANVAS_ENABLED:
        for key in _SESSION_KEYS:
            st.session_state.pop(key, None)
        return
    from ui.components.proof_state import close_proof_overlay_silent

    close_proof_overlay_silent()
