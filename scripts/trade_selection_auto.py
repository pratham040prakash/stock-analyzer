#!/usr/bin/env python3
"""Cron-friendly auto-pick top 2 trades at 9:10 PM IST."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.trade_selection_scheduler import run_auto_trade_selection


def main() -> int:
    load_app_env()
    force = "--force" in sys.argv
    count, status = run_auto_trade_selection(force=force)
    print(status)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
