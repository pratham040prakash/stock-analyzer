"""First-run setup checklist for sidebar wizard."""

from __future__ import annotations

import os
from dataclasses import dataclass

from analyzer.autopilot_status import count_installed_schedules, is_macos
from analyzer.kite_status import kite_connection_status
from analyzer.telegram_notify import telegram_configured
from analyzer.zerodha import load_env_credentials


@dataclass
class SetupStep:
    key: str
    label: str
    done: bool
    detail: str


def build_setup_status() -> list[SetupStep]:
    creds = load_env_credentials()
    kite = kite_connection_status(probe=bool(creds.get("access_token")))
    installed, total = count_installed_schedules()

    env_ok = bool(creds.get("api_key") or os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
    tg_ok = telegram_configured()
    kite_live = kite.get("level") == "ok"
    kite_logged = kite.get("level") in ("ok", "limited")
    autopilot_ok = installed >= 4 if is_macos() else False

    if kite_live:
        kite_detail = "Live quotes active"
    elif kite.get("market_data") == "personal_app":
        kite_detail = "Personal app — create **Connect** app for live LTP"
    elif kite_logged:
        kite_detail = kite.get("headline", "Logged in — quotes not active")
    else:
        kite_detail = "Sidebar → Zerodha Kite → Connect app + login"

    return [
        SetupStep(
            key="env",
            label="Environment (.env)",
            done=env_ok,
            detail="API key or Telegram token in `.env`" if env_ok else "Copy `.env.example` → `.env`",
        ),
        SetupStep(
            key="telegram",
            label="Telegram alerts",
            done=tg_ok,
            detail="Subscribed in sidebar" if tg_ok else "Sidebar → Telegram → Start bot",
        ),
        SetupStep(
            key="kite",
            label="Zerodha Kite (optional)",
            done=kite_live,
            detail=kite_detail,
        ),
        SetupStep(
            key="autopilot",
            label="Autopilot (Mac)",
            done=autopilot_ok,
            detail=f"{installed}/{total} schedules" if is_macos() else "Run locally on macOS",
        ),
    ]


def setup_complete() -> bool:
    steps = build_setup_status()
    required = [s for s in steps if s.key == "env"]
    return all(s.done for s in required)
