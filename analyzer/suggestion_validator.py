"""Validate past suggestions against actual market outcomes."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from analyzer.market_session import IST
from analyzer.suggestion_journal import (
    SuggestionRecord,
    _connect,
    fetch_suggestions,
    init_journal,
    is_bearish_action,
    is_bullish_action,
)


def _fetch_closes(yahoo_symbol: str, start: str, end: str) -> pd.Series:
    ticker = yf.Ticker(yahoo_symbol)
    hist = ticker.history(start=start, end=end, auto_adjust=True)
    if hist.empty:
        return pd.Series(dtype=float)
    return hist["Close"]


def _forward_returns(
    yahoo_symbol: str,
    signal_date: str,
) -> tuple[float | None, float | None, float | None, float | None]:
    """1d, 5d, 20d stock returns and 1d Nifty alpha (%)."""
    try:
        start = (datetime.strptime(signal_date, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d")
        end = (datetime.strptime(signal_date, "%Y-%m-%d") + timedelta(days=35)).strftime("%Y-%m-%d")
        closes = _fetch_closes(yahoo_symbol, start, end)
        nifty = _fetch_closes("^NSEI", start, end)
        if closes.empty:
            return None, None, None, None

        dates = closes.index.normalize()
        signal_ts = pd.Timestamp(signal_date).tz_localize(IST) if closes.index.tz else pd.Timestamp(signal_date)
        on_or_after = closes[dates >= signal_ts.normalize()]
        if on_or_after.empty:
            on_or_after = closes
        base = float(on_or_after.iloc[0])
        if base <= 0:
            return None, None, None, None

        def ret_at(offset: int) -> float | None:
            if len(on_or_after) <= offset:
                return None
            return round((float(on_or_after.iloc[offset]) / base - 1) * 100, 2)

        r1 = ret_at(1)
        r5 = ret_at(min(5, len(on_or_after) - 1)) if len(on_or_after) > 1 else None
        r20 = ret_at(min(20, len(on_or_after) - 1)) if len(on_or_after) > 1 else None

        alpha = None
        if r1 is not None and not nifty.empty:
            nd = nifty.index.normalize()
            n_on = nifty[nd >= signal_ts.normalize()]
            if len(n_on) >= 2:
                n_base = float(n_on.iloc[0])
                n_r1 = (float(n_on.iloc[1]) / n_base - 1) * 100 if n_base else 0
                alpha = round(r1 - n_r1, 2)

        return r1, r5, r20, alpha
    except Exception:
        return None, None, None, None


def _score_outcome(record: SuggestionRecord, r1: float | None, r5: float | None, r20: float | None) -> tuple[int, str]:
    """1=correct, 0=wrong, -1=not scored (HOLD/neutral)."""
    horizon = record.horizon
    ret = r1 if horizon in ("intraday", "holding") else (r5 if horizon == "short" else r20)
    if ret is None:
        return -1, "Insufficient price history"

    action = record.action.upper()
    if is_bullish_action(action):
        if ret > 0.3:
            return 1, f"Bullish call — stock +{ret:.2f}%"
        if ret < -0.3:
            return 0, f"Bullish call missed — stock {ret:.2f}%"
        return -1, f"Flat move {ret:.2f}% — inconclusive"
    if is_bearish_action(action):
        if ret < -0.3:
            return 1, f"Bearish call — stock {ret:.2f}%"
        if ret > 0.3:
            return 0, f"Bearish call missed — stock +{ret:.2f}%"
        return -1, f"Flat move {ret:.2f}% — inconclusive"
    return -1, f"HOLD/neutral — move {ret:.2f}%"


def validate_suggestion(record: SuggestionRecord) -> bool:
    """Validate one row; returns True if updated."""
    r1, r5, r20, alpha = _forward_returns(record.yahoo_symbol, record.signal_date)
    correct, note = _score_outcome(record, r1, r5, r20)
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    with _connect() as conn:
        conn.execute(
            """
            UPDATE suggestions SET
                validated = 1,
                outcome_return_1d = ?,
                outcome_return_5d = ?,
                outcome_return_20d = ?,
                outcome_nifty_alpha_1d = ?,
                outcome_correct = ?,
                outcome_note = ?,
                validated_at = ?
            WHERE id = ?
            """,
            (r1, r5, r20, alpha, correct, note, now, record.id),
        )
    return True


def validate_pending_suggestions(max_age_days: int = 60) -> dict:
    """
    Score all unvalidated suggestions older than signal_date.
    Run daily after market close (e.g. 4 PM IST cron).
    """
    init_journal()
    today = datetime.now(IST).strftime("%Y-%m-%d")
    cutoff = (datetime.now(IST) - timedelta(days=max_age_days)).strftime("%Y-%m-%d")

    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM suggestions
            WHERE validated = 0 AND signal_date < ? AND signal_date >= ?
            ORDER BY signal_date ASC
            """,
            (today, cutoff),
        ).fetchall()

    validated = 0
    errors = 0
    for row in rows:
        from analyzer.suggestion_journal import _row_to_record
        rec = _row_to_record(row)
        try:
            validate_suggestion(rec)
            validated += 1
        except Exception:
            errors += 1

    return {"validated": validated, "errors": errors, "pending_before": len(rows)}
