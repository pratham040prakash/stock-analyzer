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
from analyzer.options_trade_selection import load_selected_option
from analyzer.options_watchlist_history import (
    MIN_RETENTION_DAYS as OPT_MIN_DAYS,
    build_recent_options_picks,
    maybe_score_options_watchlist,
)


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


def build_options_csv(
    days: int = 30,
    *,
    market: str = "india",
) -> str:
    """All options CE/PE suggestions with premium hit/miss for spreadsheets."""
    days = max(days, OPT_MIN_DAYS)
    picks = build_recent_options_picks(days)
    for trade_date in {d for d, _ in picks}:
        maybe_score_options_watchlist(trade_date=trade_date)

    from analyzer.options_watchlist_history import fetch_options_snapshots_for_date

    rec_map: dict[tuple[str, str, str, float], bool] = {}
    for trade_date in {d for d, _ in picks}:
        for s in fetch_options_snapshots_for_date(trade_date):
            rec_map[(trade_date, s.fno_symbol, s.option_type, s.strike)] = s.recommended

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "trade_date",
            "rank",
            "fno_symbol",
            "option_type",
            "strike",
            "expiry",
            "starred",
            "entry_premium",
            "stop_premium",
            "target_premium",
            "session_high",
            "session_low",
            "session_close",
            "outcome",
            "hit_target",
            "result_label",
            "recommended",
            "note",
        ]
    )
    for trade_date, row in picks:
        starred_pick = load_selected_option(trade_date)
        starred = False
        if starred_pick:
            starred = (
                starred_pick["fno_symbol"].upper() == row.fno_symbol.upper()
                and starred_pick["option_type"].upper() == row.option_type.upper()
                and abs(float(starred_pick["strike"]) - row.strike) < 0.01
            )
        hit = row.outcome == "target_hit"
        writer.writerow(
            [
                trade_date,
                row.rank,
                row.fno_symbol,
                row.option_type,
                f"{row.strike:g}",
                row.expiry,
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
                "yes"
                if rec_map.get((trade_date, row.fno_symbol, row.option_type, row.strike))
                else "no",
                row.note or "",
            ]
        )
    return buf.getvalue()


def build_combined_suggestions_csv(
    days: int = 30,
    *,
    market: str = "india",
) -> str:
    """Equity + options rows in one CSV (asset_type column)."""
    eq = build_suggestions_csv(days=days, market=market)
    opt = build_options_csv(days=days, market=market)
    eq_lines = eq.strip().splitlines()
    opt_lines = opt.strip().splitlines()
    if len(eq_lines) <= 1 and len(opt_lines) <= 1:
        return ""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "asset_type",
            "trade_date",
            "rank",
            "symbol_or_contract",
            "option_type",
            "strike",
            "expiry",
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
            "recommended",
            "note",
        ]
    )
    if len(eq_lines) > 1:
        eq_reader = csv.reader(eq_lines[1:])
        for row in eq_reader:
            writer.writerow(
                [
                    "equity",
                    row[0],
                    row[1],
                    row[2],
                    "",
                    "",
                    "",
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    row[11],
                    row[12],
                    "",
                    row[13] if len(row) > 13 else "",
                ]
            )
    if len(opt_lines) > 1:
        opt_reader = csv.reader(opt_lines[1:])
        for row in opt_reader:
            contract = f"{row[2]} {row[3]} {row[4]}"
            writer.writerow(
                [
                    "options",
                    row[0],
                    row[1],
                    contract,
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    row[11],
                    row[12],
                    row[13],
                    row[14],
                    row[15],
                    row[16],
                    row[17] if len(row) > 17 else "",
                ]
            )
    return buf.getvalue()
