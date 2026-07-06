"""Load and update `.env` for the Streamlit app and CLI."""

from __future__ import annotations

import os
import re
from pathlib import Path

import requests

_ENV_LOADED = False


def reload_app_env() -> None:
    """Re-read `.env` into os.environ (after UI saves credentials)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path(), override=True)
    except ImportError:
        pass


def env_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


def load_app_env() -> None:
    """Load `.env` into os.environ once per process."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path())
    except ImportError:
        pass
    _ENV_LOADED = True


def save_env_key(key: str, value: str) -> None:
    """Create or update one key in `.env` and refresh os.environ."""
    load_app_env()
    key = key.strip()
    value = value.strip()
    path = env_path()
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    prefix = f"{key}="
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"{key}={value}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[key] = value


def validate_telegram_bot_token(token: str) -> tuple[bool, str, str | None]:
    """
    Verify token with Telegram getMe.
    Returns (ok, message, bot_username).
    """
    token = token.strip()
    if not token:
        return False, "Paste the bot token from @BotFather", None
    if not re.match(r"^\d+:[A-Za-z0-9_-]{20,}$", token):
        return False, "Token format looks wrong — copy the full token from BotFather", None
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if r.status_code != 200:
            return False, "Telegram rejected this token — create a new bot or recopy", None
        data = r.json()
        if not data.get("ok"):
            return False, data.get("description", "Invalid token"), None
        username = data.get("result", {}).get("username")
        return True, f"Bot @{username} connected", username
    except Exception as exc:
        return False, f"Could not reach Telegram: {exc}", None
