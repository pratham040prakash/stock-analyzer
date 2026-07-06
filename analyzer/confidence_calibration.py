"""Backtest confidence % vs realized target-hit rate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from analyzer.suggestion_journal import journal_db_path
from analyzer.watchlist_history import MIN_RETENTION_DAYS, init_watchlist_history

IST = ZoneInfo("Asia/Kolkata")

BUCKETS = (
    (0, 50, "<50%"),
    (50, 60, "50–59%"),
    (60, 70, "60–69%"),
    (70, 80, "70–79%"),
    (80, 101, "80%+"),
)


@dataclass
class ConfidenceBucket:
    label: str
    picks: int
    targets: int
    stops: int
    actual_hit_pct: float | None
    avg_confidence: float | None


def build_confidence_calibration(days: int = 90) -> list[ConfidenceBucket]:
    """Join saved confidence with EOD outcomes by bucket."""
    days = max(days, MIN_RETENTION_DAYS)
    cutoff = (datetime.now(IST).date() - timedelta(days=max(days - 1, 0))).isoformat()
    init_watchlist_history()

    import sqlite3

    conn = sqlite3.connect(journal_db_path())
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT s.confidence_pct, o.outcome
            FROM watchlist_daily_snapshots s
            JOIN watchlist_outcomes o
              ON s.trade_date = o.trade_date AND s.symbol = o.symbol
            WHERE s.trade_date >= ?
              AND s.confidence_pct IS NOT NULL
              AND o.outcome NOT IN ('no_data', 'pending')
            """,
            (cutoff,),
        ).fetchall()
    finally:
        conn.close()

    results: list[ConfidenceBucket] = []
    for lo, hi, label in BUCKETS:
        bucket = [r for r in rows if lo <= float(r["confidence_pct"]) < hi]
        if not bucket:
            results.append(ConfidenceBucket(label, 0, 0, 0, None, None))
            continue
        targets = sum(1 for r in bucket if r["outcome"] == "target_hit")
        stops = sum(1 for r in bucket if r["outcome"] in ("stop_hit", "mixed"))
        decided = targets + stops
        avg_conf = sum(float(r["confidence_pct"]) for r in bucket) / len(bucket)
        hit = (100.0 * targets / decided) if decided else None
        results.append(
            ConfidenceBucket(label, len(bucket), targets, stops, hit, round(avg_conf, 1))
        )
    return results
