#!/usr/bin/env python3
"""Run morning briefing and optionally send to Telegram. Schedule at 8:30 AM IST."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.morning_briefing import build_morning_briefing, format_morning_markdown
from analyzer.telegram_notify import (
    format_morning_telegram,
    send_telegram_broadcast,
    telegram_configured,
)


def main() -> int:
    load_app_env()

    parser = argparse.ArgumentParser(description="Stock Analyzer morning briefing")
    parser.add_argument("--period", default="6mo")
    parser.add_argument("--holdings-csv", default=None, help="Path to Zerodha holdings CSV")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh pulse scan")
    parser.add_argument("--no-holdings", action="store_true")
    parser.add_argument(
        "--send-telegram",
        action="store_true",
        help="Send briefing to Telegram (optional; requires TELEGRAM_BOT_TOKEN)",
    )
    parser.add_argument("--save", metavar="FILE", help="Save markdown to file")
    args = parser.parse_args()

    briefing = build_morning_briefing(
        period=args.period,
        holdings_csv=args.holdings_csv,
        use_pulse_cache=not args.no_cache,
        include_holdings=not args.no_holdings,
    )
    text = format_morning_markdown(briefing)
    print(text)

    if args.save:
        Path(args.save).write_text(text, encoding="utf-8")
        print(f"\nSaved: {args.save}")

    if args.send_telegram:
        if not telegram_configured():
            print(
                "\nTelegram skipped — set TELEGRAM_BOT_TOKEN in .env and subscribe in the app sidebar.",
                file=sys.stderr,
            )
            return 0
        ok, msg = send_telegram_broadcast(
            format_morning_telegram(briefing),
            alert_type="morning",
        )
        print(f"\nTelegram: {msg}")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
