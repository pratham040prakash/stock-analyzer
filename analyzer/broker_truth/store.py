"""SQLite persistence for broker truth."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.broker_truth.models import (
    BrokerHolding,
    BrokerOrder,
    BrokerPosition,
    BrokerTradeFill,
    ReconciliationResult,
    TradeRecord,
)

IST = ZoneInfo("Asia/Kolkata")
_STORE_LOCK = threading.RLock()
_STORE_READY_PATH: Path | None = None
_CONNECT_TIMEOUT_S = 30.0


def broker_truth_db_path() -> Path:
    d = Path(__file__).resolve().parent.parent.parent / "data" / "broker_truth"
    d.mkdir(parents=True, exist_ok=True)
    return d / "broker_truth.db"


def _ensure_store() -> None:
    global _STORE_READY_PATH
    path = broker_truth_db_path()
    if _STORE_READY_PATH == path:
        return
    with _STORE_LOCK:
        if _STORE_READY_PATH == path:
            return
        with _connect_unlocked() as conn:
            _create_tables(conn)
        _STORE_READY_PATH = path


def init_broker_truth_store() -> None:
    """Public init — idempotent."""
    _ensure_store()


def _connect_unlocked() -> sqlite3.Connection:
    conn = sqlite3.connect(broker_truth_db_path(), timeout=_CONNECT_TIMEOUT_S)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def _connect() -> sqlite3.Connection:
    _ensure_store()
    return _connect_unlocked()


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_orders (
            order_id TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            exchange TEXT,
            tradingsymbol TEXT,
            product TEXT,
            transaction_type TEXT,
            quantity REAL,
            filled_quantity REAL,
            average_price REAL,
            status TEXT,
            order_timestamp TEXT,
            exchange_timestamp TEXT,
            tag TEXT,
            charges REAL DEFAULT 0,
            raw_json TEXT,
            synced_at TEXT NOT NULL,
            PRIMARY KEY (order_id, trade_date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_trade_fills (
            trade_id TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            order_id TEXT,
            exchange TEXT,
            tradingsymbol TEXT,
            product TEXT,
            transaction_type TEXT,
            quantity REAL,
            average_price REAL,
            fill_timestamp TEXT,
            raw_json TEXT,
            synced_at TEXT NOT NULL,
            PRIMARY KEY (trade_id, trade_date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_trade_records (
            trade_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            exchange TEXT,
            strategy TEXT,
            entry_time TEXT,
            exit_time TEXT,
            entry_price REAL,
            exit_price REAL,
            quantity REAL,
            broker_charges REAL,
            realized_pnl REAL,
            holding_period_minutes REAL,
            order_ids TEXT,
            execution_status TEXT,
            tags TEXT,
            notes TEXT,
            product TEXT,
            side TEXT,
            trade_date TEXT NOT NULL,
            planned_id TEXT,
            source TEXT,
            synced_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_positions (
            id TEXT PRIMARY KEY,
            trade_date TEXT NOT NULL,
            tradingsymbol TEXT,
            exchange TEXT,
            product TEXT,
            quantity REAL,
            average_price REAL,
            last_price REAL,
            pnl REAL,
            realised REAL,
            synced_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_holdings (
            id TEXT PRIMARY KEY,
            trade_date TEXT NOT NULL,
            tradingsymbol TEXT,
            exchange TEXT,
            quantity REAL,
            average_price REAL,
            last_price REAL,
            pnl REAL,
            synced_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_reconciliation (
            id TEXT PRIMARY KEY,
            planned_id TEXT NOT NULL,
            trade_id TEXT,
            symbol TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            matched INTEGER,
            slippage_entry REAL,
            slippage_exit REAL,
            execution_quality TEXT,
            missed_entry INTEGER,
            partial_fill INTEGER,
            stop_adherence TEXT,
            planned_entry REAL,
            actual_entry REAL,
            planned_stop REAL,
            actual_exit REAL,
            planned_target REAL,
            realized_pnl REAL,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS broker_sync_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT NOT NULL,
            orders_count INTEGER,
            fills_count INTEGER,
            records_count INTEGER,
            status TEXT,
            error TEXT,
            synced_at TEXT NOT NULL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_btr_date ON broker_trade_records(trade_date)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_btr_symbol ON broker_trade_records(symbol, trade_date)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_recon_date ON broker_reconciliation(trade_date)"
    )


def _now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %z")


def upsert_orders(orders: list[BrokerOrder]) -> int:
    if not orders:
        return 0
    synced_at = _now()
    with _STORE_LOCK:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT INTO broker_orders (
                    order_id, trade_date, exchange, tradingsymbol, product,
                    transaction_type, quantity, filled_quantity, average_price,
                    status, order_timestamp, exchange_timestamp, tag, charges,
                    raw_json, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_id, trade_date) DO UPDATE SET
                    filled_quantity=excluded.filled_quantity,
                    average_price=excluded.average_price,
                    status=excluded.status,
                    charges=excluded.charges,
                    synced_at=excluded.synced_at
                """,
                [
                    (
                        o.order_id,
                        o.trade_date,
                        o.exchange,
                        o.tradingsymbol,
                        o.product,
                        o.transaction_type,
                        o.quantity,
                        o.filled_quantity,
                        o.average_price,
                        o.status,
                        o.order_timestamp,
                        o.exchange_timestamp,
                        o.tag,
                        o.charges,
                        "{}",
                        synced_at,
                    )
                    for o in orders
                ],
            )
    return len(orders)


def upsert_fills(fills: list[BrokerTradeFill]) -> int:
    if not fills:
        return 0
    synced_at = _now()
    with _STORE_LOCK:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT INTO broker_trade_fills (
                    trade_id, trade_date, order_id, exchange, tradingsymbol,
                    product, transaction_type, quantity, average_price,
                    fill_timestamp, raw_json, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trade_id, trade_date) DO UPDATE SET
                    quantity=excluded.quantity,
                    average_price=excluded.average_price,
                    fill_timestamp=excluded.fill_timestamp,
                    synced_at=excluded.synced_at
                """,
                [
                    (
                        f.trade_id,
                        f.trade_date,
                        f.order_id,
                        f.exchange,
                        f.tradingsymbol,
                        f.product,
                        f.transaction_type,
                        f.quantity,
                        f.average_price,
                        f.fill_timestamp,
                        "{}",
                        synced_at,
                    )
                    for f in fills
                ],
            )
    return len(fills)


def replace_trade_records_for_date(trade_date: str, records: list[TradeRecord]) -> int:
    """Replace all canonical records for a session — avoids stale rows on re-sync."""
    with _STORE_LOCK:
        with _connect() as conn:
            conn.execute(
                "DELETE FROM broker_trade_records WHERE trade_date = ?",
                (trade_date,),
            )
            if not records:
                return 0
            conn.executemany(
                """
                INSERT INTO broker_trade_records (
                    trade_id, symbol, exchange, strategy, entry_time, exit_time,
                    entry_price, exit_price, quantity, broker_charges, realized_pnl,
                    holding_period_minutes, order_ids, execution_status, tags, notes,
                    product, side, trade_date, planned_id, source, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.trade_id,
                        r.symbol,
                        r.exchange,
                        r.strategy,
                        r.entry_time,
                        r.exit_time,
                        r.entry_price,
                        r.exit_price,
                        r.quantity,
                        r.broker_charges,
                        r.realized_pnl,
                        r.holding_period_minutes,
                        json.dumps(r.order_ids),
                        r.execution_status,
                        json.dumps(r.tags),
                        r.notes,
                        r.product,
                        r.side,
                        r.trade_date,
                        r.planned_id,
                        r.source,
                        r.synced_at,
                    )
                    for r in records
                ],
            )
    return len(records)


def upsert_trade_records(records: list[TradeRecord]) -> int:
    """Upsert by trade_id — prefer replace_trade_records_for_date on full rebuild."""
    if not records:
        return 0
    with _STORE_LOCK:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT INTO broker_trade_records (
                    trade_id, symbol, exchange, strategy, entry_time, exit_time,
                    entry_price, exit_price, quantity, broker_charges, realized_pnl,
                    holding_period_minutes, order_ids, execution_status, tags, notes,
                    product, side, trade_date, planned_id, source, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trade_id) DO UPDATE SET
                    exit_time=excluded.exit_time,
                    exit_price=excluded.exit_price,
                    broker_charges=excluded.broker_charges,
                    realized_pnl=excluded.realized_pnl,
                    execution_status=excluded.execution_status,
                    planned_id=excluded.planned_id,
                    synced_at=excluded.synced_at
                """,
                [
                    (
                        r.trade_id,
                        r.symbol,
                        r.exchange,
                        r.strategy,
                        r.entry_time,
                        r.exit_time,
                        r.entry_price,
                        r.exit_price,
                        r.quantity,
                        r.broker_charges,
                        r.realized_pnl,
                        r.holding_period_minutes,
                        json.dumps(r.order_ids),
                        r.execution_status,
                        json.dumps(r.tags),
                        r.notes,
                        r.product,
                        r.side,
                        r.trade_date,
                        r.planned_id,
                        r.source,
                        r.synced_at,
                    )
                    for r in records
                ],
            )
    return len(records)


def upsert_positions(positions: list[BrokerPosition]) -> int:
    if not positions:
        return 0
    synced_at = _now()
    with _STORE_LOCK:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT INTO broker_positions (
                    id, trade_date, tradingsymbol, exchange, product,
                    quantity, average_price, last_price, pnl, realised, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    quantity=excluded.quantity,
                    average_price=excluded.average_price,
                    last_price=excluded.last_price,
                    pnl=excluded.pnl,
                    realised=excluded.realised,
                    synced_at=excluded.synced_at
                """,
                [
                    (
                        f"{p.trade_date}:{p.exchange}:{p.tradingsymbol}:{p.product}",
                        p.trade_date,
                        p.tradingsymbol,
                        p.exchange,
                        p.product,
                        p.quantity,
                        p.average_price,
                        p.last_price,
                        p.pnl,
                        p.realised,
                        synced_at,
                    )
                    for p in positions
                ],
            )
    return len(positions)


def upsert_holdings(holdings: list[BrokerHolding]) -> int:
    if not holdings:
        return 0
    synced_at = _now()
    with _STORE_LOCK:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT INTO broker_holdings (
                    id, trade_date, tradingsymbol, exchange,
                    quantity, average_price, last_price, pnl, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    quantity=excluded.quantity,
                    average_price=excluded.average_price,
                    last_price=excluded.last_price,
                    pnl=excluded.pnl,
                    synced_at=excluded.synced_at
                """,
                [
                    (
                        f"{h.trade_date}:{h.exchange}:{h.tradingsymbol}",
                        h.trade_date,
                        h.tradingsymbol,
                        h.exchange,
                        h.quantity,
                        h.average_price,
                        h.last_price,
                        h.pnl,
                        synced_at,
                    )
                    for h in holdings
                ],
            )
    return len(holdings)


def save_reconciliation_results(results: list[ReconciliationResult]) -> int:
    if not results:
        return 0
    created_at = _now()
    with _STORE_LOCK:
        with _connect() as conn:
            conn.executemany(
                """
                INSERT INTO broker_reconciliation (
                    id, planned_id, trade_id, symbol, trade_date, matched,
                    slippage_entry, slippage_exit, execution_quality, missed_entry,
                    partial_fill, stop_adherence, planned_entry, actual_entry,
                    planned_stop, actual_exit, planned_target, realized_pnl, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    trade_id=excluded.trade_id,
                    matched=excluded.matched,
                    slippage_entry=excluded.slippage_entry,
                    slippage_exit=excluded.slippage_exit,
                    execution_quality=excluded.execution_quality,
                    missed_entry=excluded.missed_entry,
                    partial_fill=excluded.partial_fill,
                    stop_adherence=excluded.stop_adherence,
                    actual_entry=excluded.actual_entry,
                    actual_exit=excluded.actual_exit,
                    realized_pnl=excluded.realized_pnl,
                    notes=excluded.notes,
                    created_at=excluded.created_at
                """,
                [
                    (
                        f"{r.trade_date}:{r.planned_id}",
                        r.planned_id,
                        r.trade_id,
                        r.symbol,
                        r.trade_date,
                        1 if r.matched else 0,
                        r.slippage_entry,
                        r.slippage_exit,
                        r.execution_quality,
                        1 if r.missed_entry else 0,
                        1 if r.partial_fill else 0,
                        r.stop_adherence,
                        r.planned_entry,
                        r.actual_entry,
                        r.planned_stop,
                        r.actual_exit,
                        r.planned_target,
                        r.realized_pnl,
                        r.notes,
                        created_at,
                    )
                    for r in results
                ],
            )
    return len(results)


def log_sync_run(
    *,
    trade_date: str,
    orders_count: int,
    fills_count: int,
    records_count: int,
    status: str,
    error: str = "",
) -> None:
    with _STORE_LOCK:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO broker_sync_runs (
                    trade_date, orders_count, fills_count, records_count, status, error, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (trade_date, orders_count, fills_count, records_count, status, error, _now()),
            )


def fetch_trade_records(
    *,
    trade_date: str | None = None,
    symbol: str | None = None,
    since_date: str | None = None,
    limit: int = 200,
) -> list[TradeRecord]:
    clauses: list[str] = []
    params: list[object] = []
    if trade_date:
        clauses.append("trade_date = ?")
        params.append(trade_date)
    if since_date:
        clauses.append("trade_date >= ?")
        params.append(since_date)
    if symbol:
        from analyzer.broker_truth.symbols import normalize_equity_symbol

        clauses.append("symbol = ?")
        params.append(normalize_equity_symbol(symbol))
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM broker_trade_records
            {where}
            ORDER BY exit_time DESC, entry_time DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [_row_to_trade_record(r) for r in rows]


def fetch_order_charges_for_date(trade_date: str) -> dict[str, float]:
    """Order ID → charges for P&L adjustment."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT order_id, charges FROM broker_orders WHERE trade_date = ?",
            (trade_date,),
        ).fetchall()
    return {str(r["order_id"]): float(r["charges"] or 0) for r in rows}


def fetch_fills_for_date(trade_date: str) -> list[BrokerTradeFill]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM broker_trade_fills WHERE trade_date = ? ORDER BY fill_timestamp",
            (trade_date,),
        ).fetchall()
    return [
        BrokerTradeFill(
            trade_id=r["trade_id"],
            order_id=r["order_id"],
            exchange=r["exchange"],
            tradingsymbol=r["tradingsymbol"],
            product=r["product"],
            transaction_type=r["transaction_type"],
            quantity=float(r["quantity"]),
            average_price=float(r["average_price"]),
            fill_timestamp=r["fill_timestamp"],
            trade_date=r["trade_date"],
        )
        for r in rows
    ]


def fetch_reconciliation_for_date(trade_date: str) -> list[ReconciliationResult]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM broker_reconciliation WHERE trade_date = ? ORDER BY symbol",
            (trade_date,),
        ).fetchall()
    return [
        ReconciliationResult(
            planned_id=r["planned_id"],
            trade_id=r["trade_id"],
            symbol=r["symbol"],
            trade_date=r["trade_date"],
            matched=bool(r["matched"]),
            slippage_entry=r["slippage_entry"],
            slippage_exit=r["slippage_exit"],
            execution_quality=r["execution_quality"],
            missed_entry=bool(r["missed_entry"]),
            partial_fill=bool(r["partial_fill"]),
            stop_adherence=r["stop_adherence"],
            planned_entry=float(r["planned_entry"]),
            actual_entry=r["actual_entry"],
            planned_stop=float(r["planned_stop"]),
            actual_exit=r["actual_exit"],
            planned_target=float(r["planned_target"]),
            realized_pnl=r["realized_pnl"],
            notes=r["notes"] or "",
        )
        for r in rows
    ]


def _row_to_trade_record(row: sqlite3.Row) -> TradeRecord:
    try:
        order_ids = json.loads(row["order_ids"] or "[]")
    except json.JSONDecodeError:
        order_ids = []
    try:
        tags = json.loads(row["tags"] or "[]")
    except json.JSONDecodeError:
        tags = []
    return TradeRecord(
        trade_id=row["trade_id"],
        symbol=row["symbol"],
        exchange=row["exchange"],
        strategy=row["strategy"] or "",
        entry_time=row["entry_time"],
        exit_time=row["exit_time"],
        entry_price=float(row["entry_price"]),
        exit_price=float(row["exit_price"]),
        quantity=float(row["quantity"]),
        broker_charges=float(row["broker_charges"] or 0),
        realized_pnl=float(row["realized_pnl"]),
        holding_period_minutes=row["holding_period_minutes"],
        order_ids=order_ids,
        execution_status=row["execution_status"],
        tags=tags,
        notes=row["notes"] or "",
        product=row["product"] or "",
        side=row["side"] or "LONG",
        trade_date=row["trade_date"],
        planned_id=row["planned_id"],
        source=row["source"] or "kite_api",
        synced_at=row["synced_at"],
    )
