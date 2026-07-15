"""Load planned trades from watchlist snapshots and pins — never broker-overwritten."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.broker_truth.models import PlannedTrade
from analyzer.broker_truth.symbols import normalize_equity_symbol
from analyzer.suggestion_journal import journal_db_path
from analyzer.watchlist_pins import PinnedPlan, infer_trade_side, load_pinned_plans

IST = ZoneInfo("Asia/Kolkata")


def _planned_from_pin(plan: PinnedPlan, trade_date: str) -> PlannedTrade:
    side = infer_trade_side(plan.entry, plan.stop_loss, explicit=plan.side)
    pid = f"plan:{trade_date}:{normalize_equity_symbol(plan.symbol)}"
    return PlannedTrade(
        planned_id=pid,
        symbol=normalize_equity_symbol(plan.symbol),
        exchange="NSE",
        strategy="MIS",
        trade_date=trade_date,
        planned_entry=float(plan.entry),
        planned_stop=float(plan.stop_loss),
        planned_target=float(plan.target),
        planned_quantity=None,
        side=side,
        source="pinned_watchlist",
        created_at=plan.pinned_at or datetime.now(IST).isoformat(),
        notes=f"sector={plan.sector}" if plan.sector else "",
        tags=["equity", "mis"],
    )


def _planned_from_snapshot_row(row: sqlite3.Row) -> PlannedTrade:
    trade_date = row["trade_date"]
    symbol = normalize_equity_symbol(row["symbol"])
    entry = float(row["entry"])
    stop = float(row["stop_loss"])
    side = infer_trade_side(entry, stop, explicit=row["side"] if "side" in row.keys() else None)
    pid = f"plan:{trade_date}:{symbol}"
    return PlannedTrade(
        planned_id=pid,
        symbol=symbol,
        exchange="NSE",
        strategy="MIS",
        trade_date=trade_date,
        planned_entry=entry,
        planned_stop=stop,
        planned_target=float(row["target"]),
        planned_quantity=None,
        side=side,
        source="watchlist_snapshot",
        created_at=row["saved_at"],
        prep_score=float(row["prep_score"]) if row["prep_score"] is not None else None,
        confidence_pct=float(row["confidence_pct"])
        if "confidence_pct" in row.keys() and row["confidence_pct"] is not None
        else None,
        tags=["equity", "mis"],
    )


def load_planned_trades(trade_date: str | None = None) -> list[PlannedTrade]:
    """Planned trades for a session from snapshots (preferred) or pins."""
    if trade_date:
        return _load_planned_for_date(trade_date)

    pins = load_pinned_plans()
    if not pins:
        return []
    td = pins[0].prep_date or datetime.now(IST).strftime("%Y-%m-%d")
    from analyzer.market_session import market_session_status

    session_date = market_session_status().get("date", td)
    return _load_planned_for_date(session_date)


def _load_planned_for_date(trade_date: str) -> list[PlannedTrade]:
    from analyzer.watchlist_history import init_watchlist_history

    init_watchlist_history()
    plans: list[PlannedTrade] = []
    seen: set[str] = set()

    with sqlite3.connect(journal_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM watchlist_daily_snapshots
            WHERE trade_date = ?
            ORDER BY rank ASC
            """,
            (trade_date,),
        ).fetchall()

    for row in rows:
        plan = _planned_from_snapshot_row(row)
        if plan.planned_id not in seen:
            seen.add(plan.planned_id)
            plans.append(plan)

    if plans:
        return plans

    for pin in load_pinned_plans():
        if pin.prep_date == trade_date or not pin.prep_date:
            plan = _planned_from_pin(pin, trade_date)
            if plan.planned_id not in seen:
                seen.add(plan.planned_id)
                plans.append(plan)

    return plans
