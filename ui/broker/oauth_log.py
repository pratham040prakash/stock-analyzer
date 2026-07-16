"""Structured OAuth callback logging for personal desktop broker flow."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "broker"
LOG_PATH = LOG_DIR / "oauth.log"
_LOGGER: logging.Logger | None = None
_MAX_SESSION_LINES = 40


def _ensure_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("broker.oauth")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)
    _LOGGER = logger
    return logger


def oauth_log(step: str, detail: str = "") -> None:
    """Write `[OAuth] step — detail` to oauth.log and session debug buffer."""
    message = f"[OAuth] {step}"
    if detail:
        message = f"{message} — {detail}"
    _ensure_logger().info(message)

    try:
        import streamlit as st

        lines: list[str] = st.session_state.setdefault("_oauth_log_lines", [])
        stamp = datetime.now(IST).strftime("%H:%M:%S")
        lines.append(f"{stamp} {message}")
        if len(lines) > _MAX_SESSION_LINES:
            st.session_state["_oauth_log_lines"] = lines[-_MAX_SESSION_LINES:]
    except Exception:
        pass


def oauth_log_exception(step: str, exc: Exception) -> None:
    oauth_log(step, f"{type(exc).__name__}: {exc}")
