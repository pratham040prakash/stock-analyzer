"""SQLite journal of all trading suggestions for outcome tracking."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
STRATEGY_VERSION = "v1.0"

_BULLISH = frozenset({
    "STRONG BUY", "BUY", "ACCUMULATE", "CORE BUY", "OK TO ADD", "OK TO ADD (SMALL)",
})
_BEARISH = frozenset({"SELL", "STRONG SELL", "TRIM", "REDUCE", "AVOID", "WEAK"})


def journal_db_path() -> Path:
    d = Path(__file__).resolve().parent.parent / "data" / "suggestions"
    d.mkdir(parents=True, exist_ok=True)
    return d / "journal.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(journal_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_journal() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id TEXT PRIMARY KEY,
                signal_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                yahoo_symbol TEXT,
                source TEXT NOT NULL,
                horizon TEXT NOT NULL,
                action TEXT NOT NULL,
                score REAL,
                price_at_signal REAL,
                entry_hint TEXT,
                stop_hint TEXT,
                target_hint TEXT,
                reason TEXT,
                strategy_version TEXT,
                created_at TEXT NOT NULL,
                validated INTEGER DEFAULT 0,
                outcome_return_1d REAL,
                outcome_return_5d REAL,
                outcome_return_20d REAL,
                outcome_nifty_alpha_1d REAL,
                outcome_correct INTEGER,
                outcome_note TEXT,
                validated_at TEXT,
                UNIQUE(signal_date, symbol, source, horizon, action)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_suggestions_date ON suggestions(signal_date)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_suggestions_validated ON suggestions(validated)"
        )


@dataclass
class SuggestionRecord:
    id: str
    signal_date: str
    symbol: str
    yahoo_symbol: str
    source: str
    horizon: str
    action: str
    score: float | None
    price_at_signal: float | None
    entry_hint: str
    stop_hint: str
    target_hint: str
    reason: str
    strategy_version: str
    created_at: str
    validated: bool = False
    outcome_return_1d: float | None = None
    outcome_return_5d: float | None = None
    outcome_return_20d: float | None = None
    outcome_nifty_alpha_1d: float | None = None
    outcome_correct: int | None = None
    outcome_note: str | None = None
    validated_at: str | None = None


def _normalize_yahoo(symbol: str) -> str:
    s = symbol.upper().strip()
    if s.endswith(".NS") or s.endswith(".BO") or s.startswith("^"):
        return s
    return f"{s}.NS"


def record_suggestion(
    *,
    symbol: str,
    source: str,
    horizon: str,
    action: str,
    score: float | None = None,
    price_at_signal: float | None = None,
    yahoo_symbol: str | None = None,
    entry_hint: str = "",
    stop_hint: str = "",
    target_hint: str = "",
    reason: str = "",
    signal_date: str | None = None,
) -> str | None:
    """Append one suggestion. Returns id or None if duplicate."""
    init_journal()
    now = datetime.now(IST)
    signal_date = signal_date or now.strftime("%Y-%m-%d")
    yahoo = _normalize_yahoo(yahoo_symbol or symbol)
    base_sym = yahoo.replace(".NS", "").replace(".BO", "")
    sid = f"{signal_date}:{source}:{horizon}:{base_sym}:{action.upper()}"

    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO suggestions (
                    id, signal_date, symbol, yahoo_symbol, source, horizon, action,
                    score, price_at_signal, entry_hint, stop_hint, target_hint,
                    reason, strategy_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid,
                    signal_date,
                    base_sym,
                    yahoo,
                    source,
                    horizon,
                    action.upper(),
                    score,
                    price_at_signal,
                    entry_hint[:500],
                    stop_hint[:200],
                    target_hint[:200],
                    reason[:1000],
                    STRATEGY_VERSION,
                    now.strftime("%Y-%m-%d %H:%M IST"),
                ),
            )
            if conn.total_changes == 0:
                return None
        return sid
    except sqlite3.Error:
        return None


def record_from_daily_briefing(briefing) -> int:
    """Log holdings actions + short/long picks from DailyBriefing."""
    count = 0
    for pick in briefing.short_term_picks:
        if record_suggestion(
            symbol=pick.symbol,
            source="daily_advisor",
            horizon="short",
            action=pick.action,
            score=pick.score,
            price_at_signal=pick.price,
            reason=pick.reason,
            signal_date=briefing.date,
        ):
            count += 1
    for pick in briefing.long_term_picks:
        if record_suggestion(
            symbol=pick.symbol,
            source="daily_advisor",
            horizon="long",
            action=pick.action,
            score=pick.score,
            price_at_signal=pick.price,
            reason=pick.reason,
            signal_date=briefing.date,
        ):
            count += 1
    for holding in briefing.holdings:
        if holding.error:
            continue
        action = holding.today_action.split("—")[0].strip().upper()
        if record_suggestion(
            symbol=holding.yahoo_symbol or holding.kite_symbol,
            source="daily_advisor",
            horizon="holding",
            action=action,
            score=holding.combined_score,
            price_at_signal=holding.last_price,
            yahoo_symbol=holding.yahoo_symbol,
            reason=holding.today_reason,
            signal_date=briefing.date,
        ):
            count += 1
    return count


def record_from_market_pulse(report) -> int:
    """Log BUY picks from market pulse scan (skip cached replays)."""
    if getattr(report, "from_cache", False):
        return 0
    count = 0
    signal_date = datetime.now(IST).strftime("%Y-%m-%d")

    def _log_picks(picks, horizon: str) -> None:
        nonlocal count
        for pick in picks:
            if record_suggestion(
                symbol=pick.nse_symbol,
                source="market_pulse",
                horizon=horizon,
                action=pick.action,
                score=pick.score,
                price_at_signal=pick.price,
                yahoo_symbol=pick.symbol,
                entry_hint=pick.entry_hint,
                stop_hint=pick.stop_hint,
                target_hint=pick.target_hint,
                reason=pick.summary,
                signal_date=signal_date,
            ):
                count += 1

    _log_picks(report.intraday_picks, "intraday")
    _log_picks(report.short_term_picks, "short")
    _log_picks(report.long_term_picks, "long")
    return count


def fetch_suggestions(
    *,
    limit: int = 200,
    validated_only: bool = False,
    pending_only: bool = False,
) -> list[SuggestionRecord]:
    init_journal()
    clauses = []
    if validated_only:
        clauses.append("validated = 1")
    if pending_only:
        clauses.append("validated = 0")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM suggestions {where} ORDER BY signal_date DESC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def count_pending_validation() -> int:
    init_journal()
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM suggestions WHERE validated = 0 AND signal_date < date('now')"
        ).fetchone()
    return int(row["c"]) if row else 0


def _row_to_record(row: sqlite3.Row) -> SuggestionRecord:
    return SuggestionRecord(
        id=row["id"],
        signal_date=row["signal_date"],
        symbol=row["symbol"],
        yahoo_symbol=row["yahoo_symbol"] or "",
        source=row["source"],
        horizon=row["horizon"],
        action=row["action"],
        score=row["score"],
        price_at_signal=row["price_at_signal"],
        entry_hint=row["entry_hint"] or "",
        stop_hint=row["stop_hint"] or "",
        target_hint=row["target_hint"] or "",
        reason=row["reason"] or "",
        strategy_version=row["strategy_version"] or "",
        created_at=row["created_at"],
        validated=bool(row["validated"]),
        outcome_return_1d=row["outcome_return_1d"],
        outcome_return_5d=row["outcome_return_5d"],
        outcome_return_20d=row["outcome_return_20d"],
        outcome_nifty_alpha_1d=row["outcome_nifty_alpha_1d"],
        outcome_correct=row["outcome_correct"],
        outcome_note=row["outcome_note"],
        validated_at=row["validated_at"],
    )


def is_bullish_action(action: str) -> bool:
    a = action.upper()
    return any(b in a for b in _BULLISH)


def is_bearish_action(action: str) -> bool:
    a = action.upper()
    return any(b in a for b in _BEARISH)
