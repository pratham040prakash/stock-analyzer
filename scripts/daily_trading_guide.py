#!/usr/bin/env python3
"""Print today's step-by-step MIS guide (terminal)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.daily_playbook import build_daily_playbook, format_playbook_text
from analyzer.env_loader import load_app_env


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily trading playbook")
    parser.add_argument("--market", default="india")
    args = parser.parse_args()
    load_app_env()
    pb = build_daily_playbook(market=args.market)
    print(format_playbook_text(pb))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
