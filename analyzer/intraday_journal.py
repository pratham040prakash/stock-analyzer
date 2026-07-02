"""Manual intraday trade log — entry/stop/target captured at trade time."""

from __future__ import annotations

import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.suggestion_journal import journal_db_path

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class IntradayTradeLog:
    id: str
    trade_date: str
    symbol: str
    action: str
    entry: float | None
    stop_loss: float | None
    target: float | None
    price_at_log: float | None
    shares: int | None
    notes: str
    created_at: str


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(journal_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_intraday_journal() -> None:
    from analyzer.suggestion_journal import init_journal

    init_journal()
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS intraday_trades (
                id TEXT PRIMARY KEY,
                trade_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                entry REAL,
                stop_loss REAL,
                target REAL,
                price_at_log REAL,
                shares INTEGER,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_intraday_trades_date ON intraday_trades(trade_date)"
        )


def log_intraday_trade(
    *,
    symbol: str,
    action: str,
    entry: float | None = None,
    stop_loss: float | None = None,
    target: float | None = None,
    price_at_log: float | None = None,
    shares: int | None = None,
    notes: str = "",
    trade_date: str | None = None,
) -> str:
    init_intraday_journal()
    now = datetime.now(IST)
    trade_date = trade_date or now.strftime("%Y-%m-%d")
    tid = f"it_{trade_date}_{symbol.upper()}_{secrets.token_hex(4)}"
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO intraday_trades (
                id, trade_date, symbol, action, entry, stop_loss, target,
                price_at_log, shares, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tid,
                trade_date,
                symbol.upper().replace(".NS", ""),
                action.upper(),
                entry,
                stop_loss,
                target,
                price_at_log,
                shares,
                notes[:500],
                now.strftime("%Y-%m-%d %H:%M IST"),
            ),
        )
    return tid


def fetch_intraday_trades(
    *,
    trade_date: str | None = None,
    limit: int = 50,
) -> list[IntradayTradeLog]:
    init_intraday_journal()
    clauses: list[str] = []
    params: list = []
    if trade_date:
        clauses.append("trade_date = ?")
        params.append(trade_date)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM intraday_trades {where}
            ORDER BY created_at DESC LIMIT ?
            """,
            params,
        ).fetchall()
    return [_row_to_log(r) for r in rows]


def count_trades_on_date(trade_date: str | None = None) -> int:
    init_intraday_journal()
    d = trade_date or datetime.now(IST).strftime("%Y-%m-%d")
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM intraday_trades WHERE trade_date = ?",
            (d,),
        ).fetchone()
    return int(row["c"]) if row else 0


def _row_to_log(row: sqlite3.Row) -> IntradayTradeLog:
    return IntradayTradeLog(
        id=row["id"],
        trade_date=row["trade_date"],
        symbol=row["symbol"],
        action=row["action"],
        entry=row["entry"],
        stop_loss=row["stop_loss"],
        target=row["target"],
        price_at_log=row["price_at_log"],
        shares=row["shares"],
        notes=row["notes"] or "",
        created_at=row["created_at"],
    )
