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


def get_tour_step() -> int:
    _ensure_dir()
    if not STATE_PATH.exists():
        return 0
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return int(data.get("tour_step", 0))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 0


def set_tour_step(step: int) -> None:
    _ensure_dir()
    data: dict = {}
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["tour_step"] = max(0, step)
    STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def is_tour_complete() -> bool:
    return get_tour_step() >= 5


def dismiss_onboarding() -> None:
    _ensure_dir()
    data: dict = {}
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["dismissed"] = True
    data["tour_step"] = 5
    STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def reset_onboarding() -> None:
    _ensure_dir()
    STATE_PATH.write_text(json.dumps({"dismissed": False, "tour_step": 0}, indent=2), encoding="utf-8")
