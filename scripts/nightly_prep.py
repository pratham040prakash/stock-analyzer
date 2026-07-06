#!/usr/bin/env python3
"""Scheduled nightly MIS prep at 9 PM IST — scan, CE/PE, Telegram."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.nightly_prep_scheduler import run_scheduled_nightly_prep
from analyzer.zerodha import load_env_credentials


def main() -> int:
    load_env_credentials()
    load_app_env()

    parser = argparse.ArgumentParser(description="Nightly MIS prep (9 PM IST)")
    parser.add_argument("--force", action="store_true", help="Run even outside 9 PM window")
    parser.add_argument("--no-telegram", action="store_true")
    args = parser.parse_args()

    count, status = run_scheduled_nightly_prep(
        send_telegram=not args.no_telegram,
        force=args.force,
    )
    print(status)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
