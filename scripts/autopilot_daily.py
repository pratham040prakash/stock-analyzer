#!/usr/bin/env python3
"""Unified Autopilot runner — post-close scan, EOD score, morning list."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.structured_log import log_event
from analyzer.zerodha import load_env_credentials


def _run_post_close() -> tuple[int, str]:
    from analyzer.post_close_scan_scheduler import run_post_close_scan

    n, msg = run_post_close_scan(scheduled=True)
    log_event("post_close_scan", ok=n > 0, message=msg)
    return n, msg


def _run_eod() -> tuple[int, str]:
    from analyzer.mis_eod_summary import run_mis_eod_summary

    summary, sent, msg = run_mis_eod_summary(send_telegram=True)
    log_event("eod_score", ok=sent, message=msg, picks=summary.equity_picks if summary else 0)
    return 1 if sent else 0, msg


def _run_morning() -> tuple[int, str]:
    from analyzer.morning_suggestions_scheduler import run_morning_suggestions

    n, msg = run_morning_suggestions()
    log_event("morning_list", ok=n > 0, message=msg)
    return n, msg


def _run_health() -> tuple[int, str]:
    from analyzer.autopilot_alerts import maybe_send_autopilot_failure_alert

    n, msg = maybe_send_autopilot_failure_alert()
    log_event("health_check", alerts=n, message=msg)
    return n, msg


def main() -> int:
    load_env_credentials()
    load_app_env()

    parser = argparse.ArgumentParser(description="Autopilot daily jobs")
    parser.add_argument(
        "phase",
        choices=["post_close", "eod", "morning", "health", "all"],
        nargs="?",
        default="all",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    runners = {
        "post_close": _run_post_close,
        "eod": _run_eod,
        "morning": _run_morning,
        "health": _run_health,
    }

    if args.phase == "all":
        order = ["post_close", "eod", "morning", "health"]
    else:
        order = [args.phase]

    for name in order:
        n, msg = runners[name]()
        print(f"[{name}] {msg}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
