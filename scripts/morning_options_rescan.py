#!/usr/bin/env python3
"""9:46 AM IST — refresh Nifty/Bank Nifty CE/PE after opening range."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.morning_options_rescan import run_morning_options_rescan_job


def main() -> int:
    load_app_env()
    count, status = run_morning_options_rescan_job()
    print(status)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
