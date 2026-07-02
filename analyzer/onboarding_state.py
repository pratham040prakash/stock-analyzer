"""Persist onboarding dismiss state."""

from __future__ import annotations

import json
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "app" / "onboarding.json"


def _ensure_dir() -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def is_onboarding_dismissed() -> bool:
    _ensure_dir()
    if not STATE_PATH.exists():
        return False
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return bool(data.get("dismissed", False))
    except (json.JSONDecodeError, OSError):
        return False


def dismiss_onboarding() -> None:
    _ensure_dir()
    STATE_PATH.write_text(json.dumps({"dismissed": True}, indent=2), encoding="utf-8")


def reset_onboarding() -> None:
    _ensure_dir()
    STATE_PATH.write_text(json.dumps({"dismissed": False}, indent=2), encoding="utf-8")
