#!/usr/bin/env python3
"""Post-close Quick scan (~3:45 PM IST) — tomorrow's top 5."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.post_close_scan_scheduler import run_post_close_scan
from analyzer.zerodha import load_env_credentials


def main() -> int:
    load_env_credentials()
    load_app_env()

    parser = argparse.ArgumentParser(description="Post-close Quick scan")
    parser.add_argument("--force", action="store_true", help="Run even if already sent")
    parser.add_argument("--no-telegram", action="store_true")
    args = parser.parse_args()

    count, status = run_post_close_scan(
        force=args.force,
        send_telegram=not args.no_telegram,
        scheduled=not args.force,
    )
    print(status)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
