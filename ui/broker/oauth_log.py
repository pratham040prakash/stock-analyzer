"""Structured OAuth callback logging for personal desktop broker flow."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "broker"
LOG_PATH = LOG_DIR / "oauth.log"
STARTUP_LOG_PATH = LOG_DIR / "startup.log"
_LOGGER: logging.Logger | None = None
_STARTUP_LOGGER: logging.Logger | None = None
_MAX_SESSION_LINES = 60

_SENSITIVE_QUERY_RE = re.compile(
    r"(request_token|access_token|api_secret|api_key|password|client_secret)=([^&\s\"']+)",
    re.IGNORECASE,
)


def sanitize_log_detail(detail: str) -> str:
    """Redact credential-like query params and tokens from log detail strings."""
    if not detail:
        return detail
    return _SENSITIVE_QUERY_RE.sub(r"\1=***", detail)


def mask_oauth_url(url: str, *, max_len: int = 120) -> str:
    """Return a log-safe OAuth redirect URL with sensitive query values redacted."""
    if not url:
        return "empty"
    masked = sanitize_log_detail(url)
    if len(masked) > max_len:
        return masked[:max_len] + "…"
    return masked


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


def _ensure_startup_logger() -> logging.Logger:
    global _STARTUP_LOGGER
    if _STARTUP_LOGGER is not None:
        return _STARTUP_LOGGER

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("broker.startup")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler(STARTUP_LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)
    _STARTUP_LOGGER = logger
    return logger


def oauth_log(step: str, detail: str = "") -> None:
    """Write `[OAuth] step — detail` to oauth.log and session debug buffer."""
    if detail:
        detail = sanitize_log_detail(detail)
    message = f"[OAuth] {step}"
    if detail:
        message = f"{message} — {detail}"
    _ensure_logger().info(message)
    _append_session_log(message)


def oauth_log_exception(step: str, exc: Exception) -> None:
    oauth_log(step, f"{type(exc).__name__}: {sanitize_log_detail(str(exc))}")


def fn_trace(function: str, phase: str, detail: str = "") -> None:
    """Instrument a function: ENTER, EXIT, RETURN, EXCEPTION."""
    oauth_log(f"{function} — {phase}", detail)


def startup_trace(step: int, function_name: str, detail: str = "") -> None:
    """Log exact startup execution order: `[Startup] 03 function_name`."""
    if detail:
        detail = sanitize_log_detail(detail)
    message = f"[Startup] {step:02d} {function_name}"
    if detail:
        message = f"{message} — {detail}"
    _ensure_startup_logger().info(message)
    _append_session_log(message)


def _append_session_log(message: str) -> None:
    try:
        import streamlit as st

        lines: list[str] = st.session_state.setdefault("_oauth_log_lines", [])
        stamp = datetime.now(IST).strftime("%H:%M:%S")
        lines.append(f"{stamp} {message}")
        if len(lines) > _MAX_SESSION_LINES:
            st.session_state["_oauth_log_lines"] = lines[-_MAX_SESSION_LINES:]
    except Exception:
        pass
