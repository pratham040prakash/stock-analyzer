#!/usr/bin/env python3
"""
Live trade signals — PURCHASE / HOLD / SELL every N seconds.

Uses full strategy synthesis (OR gate, MTF, flow, regime, IV, macro) + 1-lot rules:
  - PURCHASE when flat + gate green + synthesis BUY
  - HOLD while in trade below targets
  - SELL at min +20%; lock +25% on trend; stretch to +35%

  # 15–20% min, up to 35% stretch
  python3 scripts/live_trade_signals.py --fno NIFTY --type CE --strike 24100 \\
      --entry 80 --lots 1 --profit-mode aggressive

Examples:
  # Flat — watch when to buy
  python3 scripts/live_trade_signals.py --auto --budget 5000

  # In trade — tell when to sell
  python3 scripts/live_trade_signals.py --fno NIFTY --type CE --strike 24100 \\
      --entry 80 --lots 1 --peak-premium 92.75
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COACH = ROOT / "scripts" / "live_options_coach_watch.py"


def main() -> int:
    args = sys.argv[1:]
    if "--focus-only" not in args:
        args = ["--focus-only", *args]
    if "--interval" not in args:
        args = [*args, "--interval", "5"]
    cmd = [sys.executable, str(COACH), *args]
    print(
        "⚡ Live trade signals · PURCHASE / HOLD / SELL every 5s\n"
        "   Ctrl+C to stop\n",
        flush=True,
    )
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
