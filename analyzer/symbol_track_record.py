"""Per-symbol rolling hit rate from watchlist outcomes."""

from __future__ import annotations

from analyzer.watchlist_history import MIN_RETENTION_DAYS, fetch_outcomes_since


def symbol_rolling_stats(symbol: str, days: int = 30) -> dict:
    """Returns {total, targets, stops, win_rate_pct, label} for UI."""
    days = max(days, MIN_RETENTION_DAYS)
    sym = symbol.upper().replace(".NS", "")
    outcomes = [
        o for o in fetch_outcomes_since(days)
        if o.symbol.upper().replace(".NS", "") == sym
    ]
    decided = [o for o in outcomes if o.outcome in ("target_hit", "stop_hit", "mixed")]
    targets = sum(1 for o in decided if o.outcome == "target_hit")
    stops = sum(1 for o in decided if o.outcome in ("stop_hit", "mixed"))
    wr = (100.0 * targets / len(decided)) if decided else None
    if not decided:
        label = "—"
    else:
        wr_s = f"{wr:.0f}%" if wr is not None else "—"
        label = f"{targets}/{len(decided)} ({wr_s})"
    return {
        "total": len(outcomes),
        "decided": len(decided),
        "targets": targets,
        "stops": stops,
        "win_rate_pct": wr,
        "label": label,
    }
