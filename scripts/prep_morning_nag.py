#!/usr/bin/env python3
"""Cron-friendly 8:45 AM prep incomplete nag."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer.env_loader import load_app_env
from analyzer.prep_morning_nag import run_prep_morning_nag


def main() -> int:
    load_app_env()
    force = "--force" in sys.argv
    count, status = run_prep_morning_nag(force=force)
    print(status)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
