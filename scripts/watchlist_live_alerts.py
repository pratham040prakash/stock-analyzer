#!/usr/bin/env python3
"""Background poll for live entry/stop/target Telegram alerts (every 5 min)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.watchlist_live_alerts import run_watchlist_live_alerts


def main() -> int:
    load_app_env()
    count, status = run_watchlist_live_alerts()
    print(status)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
