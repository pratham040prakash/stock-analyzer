"""Experimental options premium plan backtest (index-proxy, educational)."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.options_watchlist_learning import get_options_premium_strategy
from analyzer.watchlist_eod import score_session_plan


@dataclass
class OptionsBacktestRow:
    trade_date: str
    fno_symbol: str
    option_type: str
    entry_premium: float
    stop_premium: float
    target_premium: float
    session_high: float
    session_low: float
    session_close: float
    outcome: str
    note: str


@dataclass
class OptionsBacktestReport:
    rows: list[OptionsBacktestRow]
    wins: int
    losses: int
    win_rate_pct: float | None
    disclaimer: str


def premium_plan_from_entry(entry: float) -> tuple[float, float]:
    strat = get_options_premium_strategy()
    stop = round(entry * float(strat["stop_mult"]), 2)
    target = round(entry * float(strat["target_mult"]), 2)
    return stop, target


def run_options_premium_proxy_backtest(
  snapshots: list,
) -> OptionsBacktestReport:
    """
    Score saved option snapshots using recorded session premium OHLC.
    Requires outcomes table or re-fetch via Kite/NSE — uses existing DB outcomes
    when available, otherwise returns empty with disclaimer.
    """
    from analyzer.options_watchlist_history import (
        build_recent_options_picks,
        fetch_options_snapshots_for_date,
        maybe_score_options_watchlist,
    )

    rows: list[OptionsBacktestRow] = []
    dates = sorted({s.trade_date for s in snapshots}, reverse=True) if snapshots else []

    if not dates:
        for trade_date, _ in build_recent_options_picks(14):
            if trade_date not in dates:
                dates.append(trade_date)
        dates = sorted(set(dates), reverse=True)[:10]

    for trade_date in dates:
        maybe_score_options_watchlist(trade_date=trade_date)
        snaps = fetch_options_snapshots_for_date(trade_date)
        from analyzer.options_watchlist_history import fetch_options_outcomes_for_date

        outcomes = {
            (o.fno_symbol, o.option_type, o.strike): o
            for o in fetch_options_outcomes_for_date(trade_date)
        }
        for s in snaps:
            if not s.recommended:
                continue
            o = outcomes.get((s.fno_symbol, s.option_type, s.strike))
            if not o or o.outcome in ("no_data", "pending"):
                continue
            if o.session_high is None or o.session_low is None:
                continue
            rows.append(
                OptionsBacktestRow(
                    trade_date=trade_date,
                    fno_symbol=s.fno_symbol,
                    option_type=s.option_type,
                    entry_premium=s.entry,
                    stop_premium=s.stop_loss,
                    target_premium=s.target,
                    session_high=float(o.session_high),
                    session_low=float(o.session_low),
                    session_close=float(o.session_close or o.session_high),
                    outcome=o.outcome,
                    note=o.note or "",
                )
            )

    wins = sum(1 for r in rows if r.outcome == "target_hit")
    losses = sum(1 for r in rows if r.outcome in ("stop_hit", "mixed"))
    decided = wins + losses

    return OptionsBacktestReport(
        rows=rows,
        wins=wins,
        losses=losses,
        win_rate_pct=(100.0 * wins / decided) if decided else None,
        disclaimer=(
            "Uses **scored ★ options** from your watchlist history (Kite or NSE premium OHLC). "
            "Not a full options walk-forward — educational only."
        ),
    )


def simulate_premium_from_index_move(
    entry: float,
    index_move_pct: float,
    option_type: str,
) -> tuple[float, float, float]:
    """Rough delta proxy: ±2× index % move on premium (for demos)."""
    mult = 2.0 if option_type == "CE" else -2.0
    if option_type == "PE":
        delta = -index_move_pct * mult
    else:
        delta = index_move_pct * mult
    close = max(0.05, entry * (1 + delta / 100))
    high = max(entry, close) * 1.08
    low = min(entry, close) * 0.92
    return high, low, close


def proxy_score_row(
    entry: float,
    index_high_pct: float,
    index_low_pct: float,
    option_type: str,
) -> tuple[str, str]:
    """Demo scoring from index % range vs premium plan."""
    stop, target = premium_plan_from_entry(entry)
    if option_type == "CE":
        high, low, close = simulate_premium_from_index_move(entry, index_high_pct, "CE")
        _, low2, _ = simulate_premium_from_index_move(entry, index_low_pct, "CE")
        low = min(low, low2)
    else:
        high, low, close = simulate_premium_from_index_move(entry, -index_low_pct, "PE")
        _, low2, _ = simulate_premium_from_index_move(entry, -index_high_pct, "PE")
        low = min(low, low2)
    outcome, note = score_session_plan(
        entry=entry,
        stop_loss=stop,
        target=target,
        session_high=high,
        session_low=low,
        session_close=close,
    )
    return outcome, note
