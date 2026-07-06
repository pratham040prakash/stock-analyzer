#!/usr/bin/env python3
"""Cron-friendly MIS session reminders (9:15 open, 3:20 square-off)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.session_reminders import run_session_reminders


def main() -> int:
    load_app_env()
    force = sys.argv[1] if len(sys.argv) > 1 else None
    if force not in (None, "open", "early_square_off", "square_off"):
        print("Usage: session_reminders.py [open|early_square_off|square_off]")
        return 1
    count, status = run_session_reminders(force=force)
    print(status)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
