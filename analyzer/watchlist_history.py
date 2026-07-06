"""Persist pre-market watchlist snapshots and score success over time."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from analyzer.intraday_watchlist import IntradayWatchlistPick
from analyzer.market_session import market_session_status
from analyzer.suggestion_journal import journal_db_path
from analyzer.watchlist_eod import (
    WatchlistOutcome,
    fetch_watchlist_outcomes,
    init_watchlist_outcomes,
    outcome_label,
    score_session_plan,
)
from analyzer.watchlist_pins import infer_trade_side, load_pinned_plans, pinned_symbols

IST = ZoneInfo("Asia/Kolkata")
MIN_RETENTION_DAYS = 7
DEFAULT_KEEP_DAYS = 180


@dataclass
class WatchlistSnapshot:
    trade_date: str
    prep_date: str
    symbol: str
    rank: int
    entry: float
    stop_loss: float
    target: float
    prep_score: float
    market_bias: str
    saved_at: str
    side: str = "LONG"
    confidence_pct: float | None = None


@dataclass
class DailyWatchlistSummary:
    trade_date: str
    pick_count: int
    scored_count: int
    target_hits: int
    stop_hits: int
    success_pct: float | None


@dataclass
class WatchlistSuccessReport:
    days_window: int
    days_with_data: int
    total_picks: int
    scored_picks: int
    target_hits: int
    stop_hits: int
    mixed: int
    flat: int
    no_data: int
    win_rate_pct: float | None
    daily: list[DailyWatchlistSummary]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(journal_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _next_trading_day(d: date) -> date:
    from analyzer.nse_holidays import next_nse_trading_day

    return next_nse_trading_day(d)


def session_target_date(now: datetime | None = None) -> str:
    """Calendar date the current watchlist is meant for."""
    now = now or datetime.now(IST)
    if now.weekday() >= 5:
        return _next_trading_day(now.date()).isoformat()
    close_min = 15 * 60 + 30
    now_min = now.hour * 60 + now.minute
    if now_min > close_min:
        return _next_trading_day(now.date()).isoformat()
    return now.strftime("%Y-%m-%d")


def init_watchlist_history() -> None:
    init_watchlist_outcomes()
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_daily_snapshots (
                id TEXT PRIMARY KEY,
                trade_date TEXT NOT NULL,
                prep_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                rank INTEGER,
                entry REAL,
                stop_loss REAL,
                target REAL,
                prep_score REAL,
                market_bias TEXT,
                saved_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_wl_snap_trade ON watchlist_daily_snapshots(trade_date)"
        )
        snap_cols = {r[1] for r in conn.execute("PRAGMA table_info(watchlist_daily_snapshots)").fetchall()}
        for col, typ in {
            "checklist_passed": "INTEGER",
            "atr_pct": "REAL",
            "rsi": "REAL",
            "volume_ratio": "REAL",
            "sector_tailwind": "INTEGER DEFAULT 0",
            "macd_bullish": "INTEGER DEFAULT 0",
            "side": "TEXT DEFAULT 'LONG'",
            "confidence_pct": "REAL",
        }.items():
            if col not in snap_cols:
                conn.execute(f"ALTER TABLE watchlist_daily_snapshots ADD COLUMN {col} {typ}")
        cols = {r[1] for r in conn.execute("PRAGMA table_info(watchlist_outcomes)").fetchall()}
        if "was_pinned" not in cols:
            conn.execute(
                "ALTER TABLE watchlist_outcomes ADD COLUMN was_pinned INTEGER DEFAULT 0"
            )
        if "rank" not in cols:
            conn.execute("ALTER TABLE watchlist_outcomes ADD COLUMN rank INTEGER")


@dataclass
class SessionWatchlistRow:
    rank: int
    symbol: str
    entry: float
    stop_loss: float
    target: float
    session_high: float | None
    session_low: float | None
    session_close: float | None
    outcome: str
    note: str
    scored: bool


def can_score_trade_date(trade_date: str) -> bool:
    """True when that calendar session has finished (not a future MIS day)."""
    now = datetime.now(IST)
    td = date.fromisoformat(trade_date)
    if td > now.date():
        return False
    if td == now.date():
        return not market_session_status().get("is_open", False)
    return td.weekday() < 5


def fetch_outcomes_for_date(trade_date: str) -> list[WatchlistOutcome]:
    init_watchlist_history()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM watchlist_outcomes
            WHERE trade_date = ? ORDER BY rank ASC, symbol ASC
            """,
            (trade_date,),
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


def latest_scored_session_date() -> str | None:
    init_watchlist_history()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT trade_date FROM watchlist_outcomes
            WHERE outcome NOT IN ('no_data', 'pending')
            ORDER BY trade_date DESC LIMIT 1
            """
        ).fetchone()
    return str(row[0]) if row else None


def todays_track_record_date() -> str | None:
    """Prefer today's scored session; else most recent scored day."""
    today = datetime.now(IST).strftime("%Y-%m-%d")
    if fetch_outcomes_for_date(today):
        return today
    return latest_scored_session_date()


def build_session_watchlist_rows(
    trade_date: str | None = None,
) -> tuple[str, list[SessionWatchlistRow]]:
    """Merge snapshot picks with scored outcomes for one MIS session."""
    trade_date = trade_date or session_target_date()
    snaps = fetch_snapshots_for_date(trade_date)
    by_sym = {o.symbol: o for o in fetch_outcomes_for_date(trade_date)}
    rows: list[SessionWatchlistRow] = []
    for s in snaps:
        o = by_sym.get(s.symbol)
        if o and o.outcome not in ("no_data",):
            rows.append(
                SessionWatchlistRow(
                    rank=s.rank,
                    symbol=s.symbol,
                    entry=s.entry,
                    stop_loss=s.stop_loss,
                    target=s.target,
                    session_high=o.session_high,
                    session_low=o.session_low,
                    session_close=o.session_close,
                    outcome=o.outcome,
                    note=o.note,
                    scored=True,
                )
            )
        else:
            rows.append(
                SessionWatchlistRow(
                    rank=s.rank,
                    symbol=s.symbol,
                    entry=s.entry,
                    stop_loss=s.stop_loss,
                    target=s.target,
                    session_high=None,
                    session_low=None,
                    session_close=None,
                    outcome="pending",
                    note="",
                    scored=False,
                )
            )
    return trade_date, rows


def fetch_snapshot_trade_dates_since(days: int = 7) -> list[str]:
    """Distinct MIS session dates with saved watchlist snapshots."""
    days = max(days, MIN_RETENTION_DAYS)
    cutoff = (datetime.now(IST).date() - timedelta(days=max(days - 1, 0))).isoformat()
    init_watchlist_history()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT trade_date FROM watchlist_daily_snapshots
            WHERE trade_date >= ?
            ORDER BY trade_date DESC
            """,
            (cutoff,),
        ).fetchall()
    return [str(r[0]) for r in rows]


def build_recent_suggested_picks(
    days: int = 7,
    *,
    market: str = "india",
) -> list[tuple[str, SessionWatchlistRow]]:
    """Every suggested pick across recent sessions, merged with EOD outcomes."""
    picks: list[tuple[str, SessionWatchlistRow]] = []
    for trade_date in fetch_snapshot_trade_dates_since(days):
        maybe_score_session_watchlist(trade_date=trade_date, market=market)
        _, rows = build_session_watchlist_rows(trade_date)
        for row in rows:
            picks.append((trade_date, row))
    return picks


def maybe_score_session_watchlist(
    *,
    trade_date: str | None = None,
    market: str = "india",
) -> list[WatchlistOutcome]:
    """Score snapshot picks when that session has closed."""
    trade_date = trade_date or session_target_date()
    if not can_score_trade_date(trade_date):
        return []
    snaps = fetch_snapshots_for_date(trade_date)
    if not snaps:
        return []
    existing = {o.symbol for o in fetch_outcomes_for_date(trade_date)}
    if len(existing) >= len(snaps):
        return []
    return score_daily_watchlist(trade_date=trade_date, market=market)


def save_watchlist_snapshot(
    picks: list[IntradayWatchlistPick],
    *,
    market_bias: str = "",
    prep_date: str | None = None,
) -> int:
    """Replace today's target-session snapshot with current watchlist picks."""
    if not picks:
        return 0
    init_watchlist_history()
    prep_date = prep_date or market_session_status().get("date", "")
    trade_date = session_target_date()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    pinned = pinned_symbols()

    with _connect() as conn:
        conn.execute(
            "DELETE FROM watchlist_daily_snapshots WHERE trade_date = ?",
            (trade_date,),
        )
        for p in picks:
            sym = p.nse_symbol.upper().replace(".NS", "")
            conn.execute(
                """
                INSERT OR REPLACE INTO watchlist_daily_snapshots (
                    id, trade_date, prep_date, symbol, rank, entry, stop_loss,
                    target, prep_score, market_bias, saved_at,
                    checklist_passed, atr_pct, rsi, volume_ratio,
                    sector_tailwind, macd_bullish, side, confidence_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"snap_{trade_date}_{sym}",
                    trade_date,
                    prep_date,
                    sym,
                    p.rank,
                    p.entry,
                    p.stop_loss,
                    p.target,
                    p.prep_score,
                    market_bias,
                    now,
                    p.checklist.passed,
                    p.atr_pct,
                    p.rsi,
                    p.volume_ratio,
                    int(p.sector_tailwind),
                    int(p.macd_bullish),
                    getattr(p, "side", "LONG") or "LONG",
                    p.confidence_pct,
                ),
            )
    return len(picks)


def fetch_snapshots_for_date(trade_date: str) -> list[WatchlistSnapshot]:
    init_watchlist_history()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM watchlist_daily_snapshots
            WHERE trade_date = ? ORDER BY rank ASC
            """,
            (trade_date,),
        ).fetchall()
    return [
        WatchlistSnapshot(
            trade_date=r["trade_date"],
            prep_date=r["prep_date"],
            symbol=r["symbol"],
            rank=int(r["rank"] or 0),
            entry=float(r["entry"]),
            stop_loss=float(r["stop_loss"]),
            target=float(r["target"]),
            prep_score=float(r["prep_score"] or 0),
            market_bias=r["market_bias"] or "",
            saved_at=r["saved_at"],
            side=infer_trade_side(
                float(r["entry"]),
                float(r["stop_loss"]),
                explicit=r["side"] if "side" in r.keys() else None,
            ),
            confidence_pct=float(r["confidence_pct"]) if r["confidence_pct"] is not None else None,
        )
        for r in rows
    ]


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


def score_daily_watchlist(
    *,
    trade_date: str | None = None,
    market: str = "india",
) -> list[WatchlistOutcome]:
    """Score all watchlist snapshot picks for a session (not only pinned)."""
    init_watchlist_history()
    trade_date = trade_date or datetime.now(IST).strftime("%Y-%m-%d")
    if not can_score_trade_date(trade_date):
        return []
    snaps = fetch_snapshots_for_date(trade_date)

    if not snaps:
        pins = load_pinned_plans()
        snaps = [
            WatchlistSnapshot(
                trade_date=trade_date,
                prep_date=p.prep_date,
                symbol=p.symbol,
                rank=0,
                entry=p.entry,
                stop_loss=p.stop_loss,
                target=p.target,
                prep_score=0,
                market_bias="",
                saved_at="",
                side=p.side,
            )
            for p in pins
        ]

    if not snaps:
        return []

    pinned = pinned_symbols()
    results: list[WatchlistOutcome] = []
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    with _connect() as conn:
        for s in snaps:
            oid = f"wo_{trade_date}_{s.symbol}"
            existing = conn.execute(
                "SELECT id FROM watchlist_outcomes WHERE id = ?", (oid,)
            ).fetchone()
            if existing:
                continue

            ohlc = _session_ohlc(s.symbol, market=market)
            if not ohlc:
                outcome, note = "no_data", "Could not fetch session candles."
                high = low = close = None
            else:
                high, low, close = ohlc
                outcome, note = score_session_plan(
                    entry=s.entry,
                    stop_loss=s.stop_loss,
                    target=s.target,
                    session_high=high,
                    session_low=low,
                    session_close=close,
                    side=s.side,
                )

            was_pinned = 1 if s.symbol in pinned else 0
            conn.execute(
                """
                INSERT OR REPLACE INTO watchlist_outcomes (
                    id, trade_date, symbol, entry, stop_loss, target,
                    session_high, session_low, session_close, outcome, note,
                    scored_at, was_pinned, rank
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    oid,
                    trade_date,
                    s.symbol,
                    s.entry,
                    s.stop_loss,
                    s.target,
                    high,
                    low,
                    close,
                    outcome,
                    note,
                    now,
                    was_pinned,
                    s.rank,
                ),
            )
            results.append(
                WatchlistOutcome(
                    trade_date=trade_date,
                    symbol=s.symbol,
                    entry=s.entry,
                    stop_loss=s.stop_loss,
                    target=s.target,
                    session_high=high,
                    session_low=low,
                    session_close=close,
                    outcome=outcome,
                    note=note,
                    scored_at=now,
                )
            )
    return results


def fetch_outcomes_since(days: int = 7) -> list[WatchlistOutcome]:
    init_watchlist_history()
    cutoff = (datetime.now(IST).date() - timedelta(days=max(days - 1, 0))).isoformat()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM watchlist_outcomes
            WHERE trade_date >= ?
            ORDER BY trade_date DESC, symbol ASC
            """,
            (cutoff,),
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


def build_watchlist_success_report(days: int = 7) -> WatchlistSuccessReport:
    days = max(days, MIN_RETENTION_DAYS)
    outcomes = fetch_outcomes_since(days)
    return _aggregate_watchlist_outcomes(days, outcomes)


def build_selected_trades_success_report(days: int = 7) -> WatchlistSuccessReport:
    """Win rate for your 2 starred picks only (when selection was saved)."""
    from analyzer.trade_selection import load_selected_symbols

    days = max(days, MIN_RETENTION_DAYS)
    outcomes = fetch_outcomes_since(days)
    filtered: list[WatchlistOutcome] = []
    for o in outcomes:
        selected = load_selected_symbols(o.trade_date)
        if not selected:
            continue
        sel = {s.upper().replace(".NS", "") for s in selected}
        if o.symbol.upper().replace(".NS", "") in sel:
            filtered.append(o)
    return _aggregate_watchlist_outcomes(days, filtered)


def _aggregate_watchlist_outcomes(
    days: int,
    outcomes: list[WatchlistOutcome],
) -> WatchlistSuccessReport:
    by_date: dict[str, list[WatchlistOutcome]] = {}
    for o in outcomes:
        by_date.setdefault(o.trade_date, []).append(o)

    daily: list[DailyWatchlistSummary] = []
    total = target = stop = mixed = flat = no_data = 0

    for trade_date in sorted(by_date.keys(), reverse=True):
        rows = by_date[trade_date]
        t = sum(1 for r in rows if r.outcome == "target_hit")
        s = sum(1 for r in rows if r.outcome == "stop_hit")
        scored = [r for r in rows if r.outcome not in ("no_data",)]
        decided = t + s
        daily.append(
            DailyWatchlistSummary(
                trade_date=trade_date,
                pick_count=len(rows),
                scored_count=len(scored),
                target_hits=t,
                stop_hits=s,
                success_pct=(100.0 * t / decided) if decided else None,
            )
        )
        total += len(rows)
        target += t
        stop += s
        mixed += sum(1 for r in rows if r.outcome == "mixed")
        flat += sum(1 for r in rows if r.outcome in ("flat", "flat_positive"))
        no_data += sum(1 for r in rows if r.outcome == "no_data")

    decided_all = target + stop
    return WatchlistSuccessReport(
        days_window=days,
        days_with_data=len(daily),
        total_picks=total,
        scored_picks=total - no_data,
        target_hits=target,
        stop_hits=stop,
        mixed=mixed,
        flat=flat,
        no_data=no_data,
        win_rate_pct=(100.0 * target / decided_all) if decided_all else None,
        daily=daily,
    )


def prune_old_watchlist_data(keep_days: int = DEFAULT_KEEP_DAYS) -> int:
    """Delete snapshots/outcomes older than keep_days (never below MIN_RETENTION_DAYS)."""
    keep_days = max(keep_days, MIN_RETENTION_DAYS)
    cutoff = (datetime.now(IST).date() - timedelta(days=keep_days)).isoformat()
    init_watchlist_history()
    with _connect() as conn:
        c1 = conn.execute(
            "DELETE FROM watchlist_daily_snapshots WHERE trade_date < ?", (cutoff,)
        ).rowcount
        c2 = conn.execute(
            "DELETE FROM watchlist_outcomes WHERE trade_date < ?", (cutoff,)
        ).rowcount
    return (c1 or 0) + (c2 or 0)


def success_summary_line(days: int = 7) -> str:
    report = build_watchlist_success_report(days)
    if report.total_picks == 0:
        return "No watchlist outcomes yet — build a watchlist and score after close."
    wr = f"{report.win_rate_pct:.0f}%" if report.win_rate_pct is not None else "—"
    return (
        f"Last **{days} days**: {report.target_hits} targets · {report.stop_hits} stops "
        f"· win rate **{wr}** ({report.scored_picks} picks scored)"
    )
