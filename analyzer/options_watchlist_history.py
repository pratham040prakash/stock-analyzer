"""Persist options expiry snapshots and score premium target/stop outcomes."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from analyzer.options_expiry_watchlist import OptionsExpiryPick
from analyzer.suggestion_journal import journal_db_path
from analyzer.watchlist_eod import outcome_label, score_session_plan
from analyzer.watchlist_history import (
    MIN_RETENTION_DAYS,
    can_score_trade_date,
    session_target_date,
)

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class OptionsWatchlistSnapshot:
    trade_date: str
    prep_date: str
    fno_symbol: str
    name: str
    rank: int
    option_type: str
    strike: float
    expiry: str
    entry: float
    stop_loss: float
    target: float
    lot_size: int
    signal: str
    spot: float
    recommended: bool
    saved_at: str


@dataclass
class OptionsWatchlistOutcome:
    trade_date: str
    fno_symbol: str
    option_type: str
    strike: float
    entry: float
    stop_loss: float
    target: float
    session_high: float | None
    session_low: float | None
    session_close: float | None
    outcome: str
    note: str
    scored_at: str


@dataclass
class OptionsSessionRow:
    rank: int
    fno_symbol: str
    name: str
    option_type: str
    strike: float
    expiry: str
    entry: float
    stop_loss: float
    target: float
    lot_size: int
    session_high: float | None
    session_low: float | None
    session_close: float | None
    outcome: str
    note: str
    scored: bool


@dataclass
class OptionsSuccessReport:
    days_window: int
    total_picks: int
    scored_picks: int
    target_hits: int
    stop_hits: int
    win_rate_pct: float | None


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(journal_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_options_watchlist_history() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS options_watchlist_snapshots (
                id TEXT PRIMARY KEY,
                trade_date TEXT NOT NULL,
                prep_date TEXT NOT NULL,
                fno_symbol TEXT NOT NULL,
                name TEXT,
                rank INTEGER,
                option_type TEXT,
                strike REAL,
                expiry TEXT,
                entry REAL,
                stop_loss REAL,
                target REAL,
                lot_size INTEGER,
                signal TEXT,
                spot REAL,
                recommended INTEGER DEFAULT 0,
                saved_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_opt_snap_trade ON options_watchlist_snapshots(trade_date)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS options_watchlist_outcomes (
                id TEXT PRIMARY KEY,
                trade_date TEXT NOT NULL,
                fno_symbol TEXT NOT NULL,
                option_type TEXT,
                strike REAL,
                entry REAL,
                stop_loss REAL,
                target REAL,
                session_high REAL,
                session_low REAL,
                session_close REAL,
                outcome TEXT,
                note TEXT,
                scored_at TEXT NOT NULL,
                rank INTEGER
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_opt_out_trade ON options_watchlist_outcomes(trade_date)"
        )


def _snap_id(trade_date: str, fno_symbol: str, option_type: str, strike: float) -> str:
    return f"opt_{trade_date}_{fno_symbol}_{option_type}_{strike:g}"


def _out_id(trade_date: str, fno_symbol: str, option_type: str, strike: float) -> str:
    return f"owo_{trade_date}_{fno_symbol}_{option_type}_{strike:g}"


def save_options_watchlist_snapshot(
    picks: list[OptionsExpiryPick],
    *,
    prep_date: str | None = None,
) -> int:
    """Save tonight's Nifty/Bank Nifty CE/PE picks for tomorrow's session."""
    if not picks:
        return 0
    init_options_watchlist_history()
    from analyzer.market_session import market_session_status

    prep_date = prep_date or market_session_status().get("date", "")
    trade_date = session_target_date()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    saved = 0
    with _connect() as conn:
        conn.execute(
            "DELETE FROM options_watchlist_snapshots WHERE trade_date = ?",
            (trade_date,),
        )
        for p in picks:
            if not p.premium or not p.stop_premium or not p.target_premium:
                continue
            sid = _snap_id(trade_date, p.fno_symbol, p.option_type, p.strike)
            conn.execute(
                """
                INSERT OR REPLACE INTO options_watchlist_snapshots (
                    id, trade_date, prep_date, fno_symbol, name, rank,
                    option_type, strike, expiry, entry, stop_loss, target,
                    lot_size, signal, spot, recommended, saved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid,
                    trade_date,
                    prep_date,
                    p.fno_symbol,
                    p.name,
                    p.rank,
                    p.option_type,
                    p.strike,
                    p.expiry,
                    float(p.premium or 0),
                    float(p.stop_premium or 0),
                    float(p.target_premium or 0),
                    p.lot_size,
                    p.signal,
                    p.spot,
                    1 if p.recommended else 0,
                    now,
                ),
            )
            saved += 1
    return saved


def fetch_options_snapshots_for_date(trade_date: str) -> list[OptionsWatchlistSnapshot]:
    init_options_watchlist_history()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM options_watchlist_snapshots
            WHERE trade_date = ? ORDER BY rank ASC
            """,
            (trade_date,),
        ).fetchall()
    return [
        OptionsWatchlistSnapshot(
            trade_date=r["trade_date"],
            prep_date=r["prep_date"],
            fno_symbol=r["fno_symbol"],
            name=r["name"] or r["fno_symbol"],
            rank=int(r["rank"] or 0),
            option_type=r["option_type"] or "",
            strike=float(r["strike"]),
            expiry=r["expiry"] or "",
            entry=float(r["entry"]),
            stop_loss=float(r["stop_loss"]),
            target=float(r["target"]),
            lot_size=int(r["lot_size"] or 0),
            signal=r["signal"] or "",
            spot=float(r["spot"] or 0),
            recommended=bool(r["recommended"]),
            saved_at=r["saved_at"],
        )
        for r in rows
    ]


def snapshots_to_expiry_picks(
    snaps: list[OptionsWatchlistSnapshot],
    *,
    max_lot_cost: float | None = None,
) -> list[OptionsExpiryPick]:
    """Rebuild OptionsExpiryPick rows from a saved snapshot."""
    picks: list[OptionsExpiryPick] = []
    for s in snaps:
        premium = float(s.entry or 0)
        lot_cost = premium * int(s.lot_size or 0)
        if max_lot_cost is not None and lot_cost > max_lot_cost:
            continue
        picks.append(
            OptionsExpiryPick(
                rank=int(s.rank or 0),
                fno_symbol=s.fno_symbol,
                name=s.name or s.fno_symbol,
                expiry=s.expiry,
                spot=float(s.spot or 0),
                signal=s.signal or "",
                option_type=s.option_type,
                strike=float(s.strike),
                premium=premium or None,
                lot_size=int(s.lot_size or 0),
                lot_cost=lot_cost or None,
                stop_premium=float(s.stop_loss) if s.stop_loss else None,
                target_premium=float(s.target) if s.target else None,
                iv=None,
                recommended=bool(s.recommended),
                reason=f"Saved {s.saved_at} (stale snapshot)",
            )
        )
    return picks


def load_stale_options_watchlist(
    *,
    max_lot_cost: float | None = None,
    trade_date: str | None = None,
):
    """Last saved CE/PE when NSE fetch fails."""
    from analyzer.options_expiry_watchlist import OptionsExpiryWatchlist

    td = trade_date or session_target_date()
    snaps = fetch_options_snapshots_for_date(td)
    if not snaps:
        return None
    picks = snapshots_to_expiry_picks(snaps, max_lot_cost=max_lot_cost)
    if not picks:
        return None
    saved_at = snaps[0].saved_at if snaps else ""
    return OptionsExpiryWatchlist(
        picks=picks,
        routine_note=f"**Stale snapshot** from {saved_at} — NSE live fetch failed.",
        nse_available=False,
        errors=["Showing last saved CE/PE — tap Retry when NSE recovers."],
    )


def fetch_options_outcomes_for_date(trade_date: str) -> list[OptionsWatchlistOutcome]:
    init_options_watchlist_history()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM options_watchlist_outcomes
            WHERE trade_date = ? ORDER BY rank ASC
            """,
            (trade_date,),
        ).fetchall()
    return [
        OptionsWatchlistOutcome(
            trade_date=r["trade_date"],
            fno_symbol=r["fno_symbol"],
            option_type=r["option_type"] or "",
            strike=float(r["strike"]),
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


def _parse_nse_expiry(expiry: str) -> date:
    return datetime.strptime(expiry.strip(), "%d-%b-%Y").date()


def resolve_kite_nfo_option(
    fno_symbol: str,
    strike: float,
    expiry: str,
    option_type: str,
) -> tuple[str, int] | None:
    """Return (tradingsymbol, instrument_token) for an index option."""
    from analyzer.zerodha import get_kite_client

    kite = get_kite_client()
    if kite is None:
        return None
    try:
        exp_date = _parse_nse_expiry(expiry)
    except ValueError:
        return None
    for row in kite.instruments("NFO"):
        if (
            row.get("name") == fno_symbol
            and row.get("instrument_type") == option_type
            and abs(float(row.get("strike") or 0) - float(strike)) < 0.01
            and row.get("expiry") == exp_date
        ):
            return str(row["tradingsymbol"]), int(row["instrument_token"])
    return None


def fetch_option_premium_ohlc(
    trade_date: str,
    *,
    fno_symbol: str,
    strike: float,
    expiry: str,
    option_type: str,
) -> tuple[float, float, float] | None:
    """Session high/low/close for option premium (Kite NFO)."""
    from analyzer.zerodha import get_kite_client

    resolved = resolve_kite_nfo_option(fno_symbol, strike, expiry, option_type)
    if not resolved:
        return None
    tradingsymbol, token = resolved
    kite = get_kite_client()
    if kite is None:
        return None

    td = date.fromisoformat(trade_date)
    today = datetime.now(IST).date()

    if td == today:
        try:
            q = kite.quote([f"NFO:{tradingsymbol}"]).get(f"NFO:{tradingsymbol}", {})
            ohlc = q.get("ohlc") or {}
            high = ohlc.get("high")
            low = ohlc.get("low")
            close = q.get("last_price")
            if high and low and close:
                return float(high), float(low), float(close)
        except Exception:
            pass

    try:
        start = datetime.combine(td, time(9, 15), tzinfo=IST)
        end = datetime.combine(td, time(15, 30), tzinfo=IST)
        raw = kite.historical_data(
            token,
            start.replace(tzinfo=None),
            end.replace(tzinfo=None),
            "5minute",
            continuous=False,
            oi=False,
        )
        if not raw:
            return None
        highs = [float(r["high"]) for r in raw if r.get("high")]
        lows = [float(r["low"]) for r in raw if r.get("low")]
        if not highs or not lows:
            return None
        return max(highs), min(lows), float(raw[-1]["close"])
    except Exception:
        return None


def score_options_daily_watchlist(
    *,
    trade_date: str | None = None,
) -> list[OptionsWatchlistOutcome]:
    """Score saved CE/PE picks vs session premium high/low."""
    init_options_watchlist_history()
    trade_date = trade_date or datetime.now(IST).strftime("%Y-%m-%d")
    if not can_score_trade_date(trade_date):
        return []

    snaps = fetch_options_snapshots_for_date(trade_date)
    if not snaps:
        return []

    results: list[OptionsWatchlistOutcome] = []
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    with _connect() as conn:
        for s in snaps:
            oid = _out_id(trade_date, s.fno_symbol, s.option_type, s.strike)
            existing = conn.execute(
                "SELECT id FROM options_watchlist_outcomes WHERE id = ?", (oid,)
            ).fetchone()
            if existing:
                continue

            if s.entry <= 0 or s.stop_loss <= 0 or s.target <= 0:
                outcome, note = "no_data", "Missing entry/stop/target premium at snapshot."
                high = low = close = None
            else:
                ohlc = fetch_option_premium_ohlc(
                    trade_date,
                    fno_symbol=s.fno_symbol,
                    strike=s.strike,
                    expiry=s.expiry,
                    option_type=s.option_type,
                )
                source = "Kite" if ohlc else ""
                if not ohlc:
                    from analyzer.nse_option_history import fetch_nse_option_day_ohlc

                    ohlc = fetch_nse_option_day_ohlc(
                        trade_date,
                        fno_symbol=s.fno_symbol,
                        strike=s.strike,
                        expiry=s.expiry,
                        option_type=s.option_type,
                    )
                    source = "NSE" if ohlc else ""
                if not ohlc:
                    outcome, note = (
                        "no_data",
                        "Connect **Kite** or retry when **NSE** historical is available.",
                    )
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
                    )
                    if source:
                        note = f"{note} ({source})"

            conn.execute(
                """
                INSERT OR REPLACE INTO options_watchlist_outcomes (
                    id, trade_date, fno_symbol, option_type, strike,
                    entry, stop_loss, target,
                    session_high, session_low, session_close,
                    outcome, note, scored_at, rank
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    oid,
                    trade_date,
                    s.fno_symbol,
                    s.option_type,
                    s.strike,
                    s.entry,
                    s.stop_loss,
                    s.target,
                    high,
                    low,
                    close,
                    outcome,
                    note,
                    now,
                    s.rank,
                ),
            )
            results.append(
                OptionsWatchlistOutcome(
                    trade_date=trade_date,
                    fno_symbol=s.fno_symbol,
                    option_type=s.option_type,
                    strike=s.strike,
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


def maybe_score_options_watchlist(
    *,
    trade_date: str | None = None,
) -> list[OptionsWatchlistOutcome]:
    trade_date = trade_date or session_target_date()
    if not can_score_trade_date(trade_date):
        return []
    snaps = fetch_options_snapshots_for_date(trade_date)
    if not snaps:
        return []
    existing = fetch_options_outcomes_for_date(trade_date)
    scored_syms = {
        (o.fno_symbol, o.option_type, o.strike)
        for o in existing
        if o.outcome not in ("no_data", "pending")
    }
    if len(scored_syms) >= len(snaps):
        return []
    return score_options_daily_watchlist(trade_date=trade_date)


def build_options_session_rows(
    trade_date: str | None = None,
) -> tuple[str, list[OptionsSessionRow]]:
    trade_date = trade_date or session_target_date()
    snaps = fetch_options_snapshots_for_date(trade_date)
    by_key = {
        (o.fno_symbol, o.option_type, o.strike): o
        for o in fetch_options_outcomes_for_date(trade_date)
    }
    rows: list[OptionsSessionRow] = []
    for s in snaps:
        o = by_key.get((s.fno_symbol, s.option_type, s.strike))
        if o and o.outcome not in ("no_data",):
            rows.append(
                OptionsSessionRow(
                    rank=s.rank,
                    fno_symbol=s.fno_symbol,
                    name=s.name,
                    option_type=s.option_type,
                    strike=s.strike,
                    expiry=s.expiry,
                    entry=s.entry,
                    stop_loss=s.stop_loss,
                    target=s.target,
                    lot_size=s.lot_size,
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
                OptionsSessionRow(
                    rank=s.rank,
                    fno_symbol=s.fno_symbol,
                    name=s.name,
                    option_type=s.option_type,
                    strike=s.strike,
                    expiry=s.expiry,
                    entry=s.entry,
                    stop_loss=s.stop_loss,
                    target=s.target,
                    lot_size=s.lot_size,
                    session_high=None,
                    session_low=None,
                    session_close=None,
                    outcome="pending",
                    note="",
                    scored=False,
                )
            )
    return trade_date, rows


def latest_scored_options_date() -> str | None:
    init_options_watchlist_history()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT trade_date FROM options_watchlist_outcomes
            WHERE outcome NOT IN ('no_data', 'pending')
            ORDER BY trade_date DESC LIMIT 1
            """
        ).fetchone()
    return str(row[0]) if row else None


def todays_options_track_date() -> str | None:
    today = datetime.now(IST).strftime("%Y-%m-%d")
    if fetch_options_outcomes_for_date(today):
        return today
    return latest_scored_options_date()


def fetch_options_snapshot_dates_since(days: int = 7) -> list[str]:
    days = max(days, MIN_RETENTION_DAYS)
    cutoff = (datetime.now(IST).date() - timedelta(days=max(days - 1, 0))).isoformat()
    init_options_watchlist_history()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT trade_date FROM options_watchlist_snapshots
            WHERE trade_date >= ? ORDER BY trade_date DESC
            """,
            (cutoff,),
        ).fetchall()
    return [str(r[0]) for r in rows]


def build_recent_options_picks(days: int = 7) -> list[tuple[str, OptionsSessionRow]]:
    picks: list[tuple[str, OptionsSessionRow]] = []
    for trade_date in fetch_options_snapshot_dates_since(days):
        maybe_score_options_watchlist(trade_date=trade_date)
        _, rows = build_options_session_rows(trade_date)
        for row in rows:
            picks.append((trade_date, row))
    return picks


def build_options_success_report(days: int = 7) -> OptionsSuccessReport:
    days = max(days, MIN_RETENTION_DAYS)
    cutoff = (datetime.now(IST).date() - timedelta(days=max(days - 1, 0))).isoformat()
    init_options_watchlist_history()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT outcome FROM options_watchlist_outcomes
            WHERE trade_date >= ? AND outcome NOT IN ('no_data', 'pending')
            """,
            (cutoff,),
        ).fetchall()
    outcomes = [r[0] for r in rows]
    targets = sum(1 for o in outcomes if o == "target_hit")
    stops = sum(1 for o in outcomes if o in ("stop_hit", "mixed"))
    decided = targets + stops
    return OptionsSuccessReport(
        days_window=days,
        total_picks=len(outcomes),
        scored_picks=len(outcomes),
        target_hits=targets,
        stop_hits=stops,
        win_rate_pct=(100.0 * targets / decided) if decided else None,
    )


def score_pending_options_sessions() -> int:
    """Score all past option sessions with snapshots."""
    init_options_watchlist_history()
    cutoff = (datetime.now(IST).date() - timedelta(days=14)).isoformat()
    with _connect() as conn:
        dates = [
            r[0]
            for r in conn.execute(
                """
                SELECT DISTINCT trade_date FROM options_watchlist_snapshots
                WHERE trade_date >= ? ORDER BY trade_date DESC
                """,
                (cutoff,),
            ).fetchall()
        ]
    total = 0
    for td in dates:
        if can_score_trade_date(td):
            total += len(score_options_daily_watchlist(trade_date=td))
    return total


def prune_old_options_data(keep_days: int = 90) -> int:
    keep_days = max(keep_days, MIN_RETENTION_DAYS)
    cutoff = (datetime.now(IST).date() - timedelta(days=keep_days)).isoformat()
    init_options_watchlist_history()
    with _connect() as conn:
        c1 = conn.execute(
            "DELETE FROM options_watchlist_snapshots WHERE trade_date < ?", (cutoff,)
        ).rowcount
        c2 = conn.execute(
            "DELETE FROM options_watchlist_outcomes WHERE trade_date < ?", (cutoff,)
        ).rowcount
    return (c1 or 0) + (c2 or 0)
