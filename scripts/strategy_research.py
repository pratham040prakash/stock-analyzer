#!/usr/bin/env python3
"""Run 6-month Nifty 50 pattern research and update suggestion weights."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyzer.strategy_research import run_strategy_research


def main() -> int:
    parser = argparse.ArgumentParser(description="Mine MIS patterns and tune suggestion weights.")
    parser.add_argument("--period", default="6mo", help="History window (default 6mo)")
    parser.add_argument("--market", default="india")
    parser.add_argument("--max-symbols", type=int, default=None, help="Limit universe size")
    parser.add_argument("--dry-run", action="store_true", help="Do not write strategy file")
    args = parser.parse_args()

    report = run_strategy_research(
        period=args.period,
        market=args.market,
        max_symbols=args.max_symbols,
        apply=not args.dry_run,
    )
    print(f"Symbols: {report.symbols_scanned} · samples: {report.samples}")
    if report.win_rate_pct is not None:
        print(f"Simulated hit rate: {report.win_rate_pct:.1f}%")
        if report.test_win_rate_pct is not None:
            print(f"Holdout: {report.test_win_rate_pct:.1f}%")
    for line in report.insights:
        print(f"  - {line.replace('**', '')}")
    print(f"Applied: {report.applied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
