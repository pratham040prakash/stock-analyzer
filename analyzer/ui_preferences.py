"""Persist UI preferences (theme, compact nav)."""

from __future__ import annotations

import json
from pathlib import Path

PREFS_PATH = Path(__file__).resolve().parent.parent / "data" / "app" / "ui_prefs.json"


def _ensure_dir() -> None:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_ui_prefs() -> dict:
    _ensure_dir()
    if not PREFS_PATH.exists():
        return {}
    try:
        return json.loads(PREFS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_ui_prefs(prefs: dict) -> None:
    _ensure_dir()
    PREFS_PATH.write_text(json.dumps(prefs, indent=2), encoding="utf-8")


def get_theme() -> str:
    return load_ui_prefs().get("theme", "dark")


def set_theme(theme: str) -> None:
    prefs = load_ui_prefs()
    prefs["theme"] = theme
    save_ui_prefs(prefs)
