#!/usr/bin/env python3
"""Morning pick list Telegram (~8:50 AM IST)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.morning_suggestions_scheduler import run_morning_suggestions
from analyzer.zerodha import load_env_credentials


def main() -> int:
    load_env_credentials()
    load_app_env()

    parser = argparse.ArgumentParser(description="Morning suggestions Telegram")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    count, status = run_morning_suggestions(force=args.force)
    print(status)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
