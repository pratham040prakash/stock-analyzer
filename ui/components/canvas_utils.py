"""Shared presentation helpers for partner canvases (no investment reasoning)."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any

import streamlit as st

from analyzer.context_engine.models import ContextSnapshot
from analyzer.use_cases.snapshot_cache import snapshot_from_cache, snapshot_to_cache
from ui.broker.state import BrokerSnapshot, load_broker_snapshot

_MENTOR_MAX_WORDS = 18


@dataclass(frozen=True)
class VerdictCanvasState:
    key: str
    word: str
    cta_label: str
    cta_action: str  # done | plan | week | connect


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _strip_md(text: str) -> str:
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", str(text or ""))
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    return cleaned.strip()


def _trim_words(text: str, *, max_words: int = _MENTOR_MAX_WORDS) -> str:
    words = _strip_md(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    clipped = " ".join(words[:max_words]).rstrip(".,;:")
    return f"{clipped}…"


def _broker_snapshot() -> BrokerSnapshot:
    raw = st.session_state.get("broker_snapshot")
    if raw:
        return BrokerSnapshot.from_dict(raw)
    return load_broker_snapshot()


def _sync_status(broker: BrokerSnapshot) -> tuple[str, str, str]:
    """Return (css_class, dot_class, label)."""
    if broker.connected():
        if broker.state == "limited":
            return "vc-sync-warn", "vc-sync-warn", "Stale"
        return "vc-sync-ok", "vc-sync-ok", "Synced"
    return "vc-sync-off", "vc-sync-off", "Offline"


def _snapshot_to_cache(snapshot: ContextSnapshot) -> dict[str, Any]:
    return snapshot_to_cache(snapshot)


def _snapshot_from_cache(data: dict[str, Any]) -> ContextSnapshot:
    return snapshot_from_cache(data)
