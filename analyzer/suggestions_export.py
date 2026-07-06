"""Export suggestion snapshots + hit/miss outcomes as CSV."""

from __future__ import annotations

import csv
import io

from analyzer.watchlist_eod import outcome_label
from analyzer.watchlist_history import (
    MIN_RETENTION_DAYS,
    build_recent_suggested_picks,
    maybe_score_session_watchlist,
)
from analyzer.trade_selection import load_selected_symbols


def build_suggestions_csv(
    days: int = 30,
    *,
    market: str = "india",
) -> str:
    """All equity suggestions with raw numbers and hit/miss for spreadsheets."""
    days = max(days, MIN_RETENTION_DAYS)
    picks = build_recent_suggested_picks(days, market=market)
    for trade_date in {d for d, _ in picks}:
        maybe_score_session_watchlist(trade_date=trade_date, market=market)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "trade_date",
            "rank",
            "symbol",
            "starred",
            "entry",
            "stop",
            "target",
            "session_high",
            "session_low",
            "session_close",
            "outcome",
            "hit_target",
            "result_label",
            "note",
        ]
    )
    for trade_date, row in picks:
        selected = {s.upper() for s in load_selected_symbols(trade_date)}
        starred = row.symbol.upper() in selected
        hit = row.outcome == "target_hit"
        writer.writerow(
            [
                trade_date,
                row.rank,
                row.symbol,
                "yes" if starred else "no",
                f"{row.entry:.2f}",
                f"{row.stop_loss:.2f}",
                f"{row.target:.2f}",
                f"{row.session_high:.2f}" if row.session_high is not None else "",
                f"{row.session_low:.2f}" if row.session_low is not None else "",
                f"{row.session_close:.2f}" if row.session_close is not None else "",
                row.outcome if row.scored else "pending",
                "yes" if hit else ("no" if row.scored else ""),
                outcome_label(row.outcome) if row.scored else "Pending",
                row.note or "",
            ]
        )
    return buf.getvalue()
