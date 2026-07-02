"""EOD scoring for pinned watchlist plans."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.suggestion_journal import journal_db_path
from analyzer.watchlist_pins import PinnedPlan, load_pinned_plans

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class WatchlistOutcome:
    trade_date: str
    symbol: str
    entry: float
    stop_loss: float
    target: float
    session_high: float | None
    session_low: float | None
    session_close: float | None
    outcome: str
    note: str
    scored_at: str


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(journal_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_watchlist_outcomes() -> None:
    from analyzer.suggestion_journal import init_journal

    init_journal()
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_outcomes (
                id TEXT PRIMARY KEY,
                trade_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                entry REAL,
                stop_loss REAL,
                target REAL,
                session_high REAL,
                session_low REAL,
                session_close REAL,
                outcome TEXT,
                note TEXT,
                scored_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_wl_outcomes_date ON watchlist_outcomes(trade_date)"
        )


def _session_ohlc(symbol: str, market: str = "india") -> tuple[float, float, float] | None:
    from analyzer.providers import fetch_intraday_bars

    try:
        df, _ = fetch_intraday_bars(symbol, interval="5m", market=market)
        if df is None or df.empty:
            return None
        return (
            float(df["High"].max()),
            float(df["Low"].min()),
            float(df["Close"].iloc[-1]),
        )
    except Exception:
        return None


def score_session_plan(
    *,
    entry: float,
    stop_loss: float,
    target: float,
    session_high: float,
    session_low: float,
    session_close: float,
) -> tuple[str, str]:
    """Conservative long plan: stop checked before target if both touched."""
    stop_hit = session_low <= stop_loss
    target_hit = session_high >= target

    if stop_hit and not target_hit:
        return "stop_hit", f"Low ₹{session_low:,.2f} ≤ stop ₹{stop_loss:,.2f}."
    if target_hit and not stop_hit:
        return "target_hit", f"High ₹{session_high:,.2f} ≥ target ₹{target:,.2f}."
    if stop_hit and target_hit:
        return "mixed", "Both stop and target touched — assume stop first (conservative)."
    if session_close >= entry:
        return "flat_positive", f"Close ₹{session_close:,.2f} held above entry ₹{entry:,.2f}."
    return "flat", f"No stop/target hit. Close ₹{session_close:,.2f}."


def score_pinned_plans(
    *,
    trade_date: str | None = None,
    market: str = "india",
) -> list[WatchlistOutcome]:
    """Score today's pinned picks against session OHLC."""
    init_watchlist_outcomes()
    trade_date = trade_date or datetime.now(IST).strftime("%Y-%m-%d")
    pins = load_pinned_plans()
    if not pins:
        return []

    results: list[WatchlistOutcome] = []
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    with _connect() as conn:
        for p in pins:
            oid = f"wo_{trade_date}_{p.symbol}"
            existing = conn.execute(
                "SELECT id FROM watchlist_outcomes WHERE id = ?", (oid,)
            ).fetchone()
            if existing:
                continue

            ohlc = _session_ohlc(p.symbol, market=market)
            if not ohlc:
                outcome, note = "no_data", "Could not fetch session candles."
                high = low = close = None
            else:
                high, low, close = ohlc
                outcome, note = score_session_plan(
                    entry=p.entry,
                    stop_loss=p.stop_loss,
                    target=p.target,
                    session_high=high,
                    session_low=low,
                    session_close=close,
                )

            conn.execute(
                """
                INSERT OR REPLACE INTO watchlist_outcomes (
                    id, trade_date, symbol, entry, stop_loss, target,
                    session_high, session_low, session_close, outcome, note, scored_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    oid, trade_date, p.symbol, p.entry, p.stop_loss, p.target,
                    high, low, close, outcome, note, now,
                ),
            )
            results.append(
                WatchlistOutcome(
                    trade_date=trade_date,
                    symbol=p.symbol,
                    entry=p.entry,
                    stop_loss=p.stop_loss,
                    target=p.target,
                    session_high=high,
                    session_low=low,
                    session_close=close,
                    outcome=outcome,
                    note=note,
                    scored_at=now,
                )
            )
    return results


def fetch_watchlist_outcomes(*, limit: int = 30) -> list[WatchlistOutcome]:
    init_watchlist_outcomes()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM watchlist_outcomes
            ORDER BY trade_date DESC, symbol ASC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        WatchlistOutcome(
            trade_date=r["trade_date"],
            symbol=r["symbol"],
            entry=r["entry"],
            stop_loss=r["stop_loss"],
            target=r["target"],
            session_high=r["session_high"],
            session_low=r["session_low"],
            session_close=r["session_close"],
            outcome=r["outcome"],
            note=r["note"] or "",
            scored_at=r["scored_at"],
        )
        for r in rows
    ]


def outcome_label(outcome: str) -> str:
    labels = {
        "target_hit": "✅ Target hit",
        "stop_hit": "❌ Stop hit",
        "mixed": "⚠️ Mixed",
        "flat_positive": "➖ Flat+",
        "flat": "➖ Flat",
        "no_data": "— No data",
    }
    return labels.get(outcome, outcome)
