#!/usr/bin/env python3
"""MIS EOD Telegram summary after market close (~3:35 PM IST)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.mis_eod_summary import format_mis_eod_telegram, run_mis_eod_summary
from analyzer.zerodha import load_env_credentials


def main() -> int:
    load_env_credentials()
    load_app_env()

    parser = argparse.ArgumentParser(description="MIS EOD summary Telegram")
    parser.add_argument("--force", action="store_true", help="Resend even if already sent today")
    parser.add_argument("--no-telegram", action="store_true", help="Print summary only")
    parser.add_argument("--date", default=None, help="Trade date YYYY-MM-DD")
    args = parser.parse_args()

    summary, sent, status = run_mis_eod_summary(
        trade_date=args.date,
        send_telegram=not args.no_telegram,
        force=args.force,
    )
    if summary:
        print(format_mis_eod_telegram(summary))
    print(f"\n{status}")
    return 0 if (sent or args.no_telegram or summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
