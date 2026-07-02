#!/usr/bin/env python3
"""Send monthly SIP reminders via Telegram. Schedule on days 1–28 via cron."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.sip_reminders import run_sip_reminders
from analyzer.zerodha import load_env_credentials


def main() -> int:
    load_env_credentials()
    parser = argparse.ArgumentParser(description="Stock Analyzer SIP reminders")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Send all reminder-enabled goals (ignore day-of-month)",
    )
    args = parser.parse_args()

    n, msg = run_sip_reminders(force=args.force)
    print(msg)
    return 0 if n or "Not a reminder" in msg or "No goals due" in msg else 1


if __name__ == "__main__":
    raise SystemExit(main())
