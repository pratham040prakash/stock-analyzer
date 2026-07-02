#!/usr/bin/env python3
"""Validate yesterday's suggestions against actual market moves."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyzer.eod_learning import run_eod_learning_cycle


def main() -> int:
    result = run_eod_learning_cycle(send_telegram_alert=True)
    report = result.report
    assert report is not None

    print("\nSuggestion validation")
    print("=" * 40)
    print(f"  Validated this run: {result.validated}")
    print(f"  Errors:             {result.errors}")
    print(f"  Total validated:    {report.validated_count}")
    print(f"  Pending:            {report.pending_count}")
    print(f"  Win rate:           {report.overall_win_rate_pct:.1f}%")
    if result.tuning and result.tuning.changes:
        print("\n  Threshold updates:")
        for ch in result.tuning.changes:
            print(f"    {ch.horizon}: {ch.old_value} → {ch.new_value} ({ch.reason})")
    if result.telegram_sent:
        print("\n  Telegram scorecard: sent")
    elif result.telegram_error:
        print(f"\n  Telegram: {result.telegram_error}")
    print()
    if result.insights:
        print("Insights:")
        for line in result.insights:
            print(f"  • {line.replace('**', '')}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
