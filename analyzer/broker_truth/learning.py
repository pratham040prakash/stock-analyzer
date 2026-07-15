"""Learning interfaces — broker truth primary, coach/EOD fallback."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo

from analyzer.broker_truth.models import TradeRecord
from analyzer.broker_truth.reconciliation import ReconciliationService
from analyzer.broker_truth.service import BrokerTruthService
from analyzer.broker_truth.store import fetch_trade_records
from analyzer.broker_truth.symbols import normalize_equity_symbol
from analyzer.structured_log import log_event
from analyzer.suggestion_journal import journal_db_path

IST = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)
FLAT_PNL_THRESHOLD = 1.0  # ₹ — below this counts as flat


class LearningOutcomeSource(str, Enum):
    BROKER = "broker"
    COACH_FALLBACK = "coach_fallback"
    NONE = "none"


@dataclass
class LearningOutcomeRow:
    trade_date: str
    symbol: str
    outcome: str
    source: LearningOutcomeSource
    realized_pnl: float | None = None
    prep_score: float = 0.0
    checklist_passed: int = 0
    atr_pct: float | None = None
    rsi: float | None = None
    volume_ratio: float | None = None
    sector_tailwind: bool = False
    macd_bullish: bool = False


def normalize_outcome_from_pnl(realized_pnl: float) -> str:
    """Map broker P&L to legacy outcome labels for backward-compatible learning."""
    if realized_pnl > FLAT_PNL_THRESHOLD:
        return "target_hit"
    if realized_pnl < -FLAT_PNL_THRESHOLD:
        return "stop_hit"
    return "flat"


def sync_broker_truth_for_learning(trade_date: str | None = None) -> dict:
    """Sync Kite data and reconcile before learning runs."""
    trade_date = trade_date or datetime.now(IST).strftime("%Y-%m-%d")
    broker = BrokerTruthService()
    sync = broker.sync_session(trade_date)
    recon_errors: list[str] = []
    results = []
    try:
        recon = ReconciliationService(broker)
        results = recon.reconcile_session(trade_date)
    except Exception as exc:
        recon_errors.append(str(exc))
        logger.warning("broker_truth reconciliation failed: %s", exc)

    broker_matched = sum(1 for r in results if r.matched)
    payload = {
        "trade_date": trade_date,
        "connected": sync.connected,
        "orders": sync.orders_imported,
        "fills": sync.fills_imported,
        "records": sync.records_built,
        "reconciled": len(results),
        "matched": broker_matched,
        "errors": sync.errors + recon_errors,
    }
    log_event("broker_truth_learning_sync", **{k: v for k, v in payload.items() if k != "errors"}, error_count=len(payload["errors"]))
    return payload


def _broker_outcomes_since(cutoff: str) -> dict[tuple[str, str], LearningOutcomeRow]:
    records = fetch_trade_records(since_date=cutoff, limit=2000)
    out: dict[tuple[str, str], LearningOutcomeRow] = {}
    for rec in records:
        key = (rec.trade_date, rec.symbol.upper())
        if key in out:
            continue
        out[key] = LearningOutcomeRow(
            trade_date=rec.trade_date,
            symbol=rec.symbol.upper(),
            outcome=normalize_outcome_from_pnl(rec.realized_pnl),
            source=LearningOutcomeSource.BROKER,
            realized_pnl=rec.realized_pnl,
        )
    return out


def _coach_outcome_rows(*, days: int) -> list[LearningOutcomeRow]:
    """Legacy coach/EOD outcomes — fallback only."""
    cutoff = (datetime.now(IST).date() - timedelta(days=days)).isoformat()
    from analyzer.watchlist_eod import init_watchlist_outcomes
    from analyzer.watchlist_history import init_watchlist_history

    init_watchlist_outcomes()
    init_watchlist_history()
    try:
        with sqlite3.connect(journal_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    o.trade_date, o.symbol, o.outcome,
                    COALESCE(s.prep_score, 0) AS prep_score,
                    COALESCE(s.checklist_passed, 0) AS checklist_passed,
                    s.atr_pct, s.rsi, s.volume_ratio,
                    COALESCE(s.sector_tailwind, 0) AS sector_tailwind,
                    COALESCE(s.macd_bullish, 0) AS macd_bullish
                FROM watchlist_outcomes o
                LEFT JOIN watchlist_daily_snapshots s
                  ON s.trade_date = o.trade_date AND s.symbol = o.symbol
                WHERE o.trade_date >= ?
                  AND o.outcome NOT IN ('no_data', 'pending')
                ORDER BY o.trade_date DESC
                """,
                (cutoff,),
            ).fetchall()
    except sqlite3.Error as exc:
        logger.warning("coach outcome fetch failed: %s", exc)
        return []

    return [
        LearningOutcomeRow(
            trade_date=r["trade_date"],
            symbol=normalize_equity_symbol(r["symbol"]),
            outcome=r["outcome"],
            source=LearningOutcomeSource.COACH_FALLBACK,
            prep_score=float(r["prep_score"] or 0),
            checklist_passed=int(r["checklist_passed"] or 0),
            atr_pct=float(r["atr_pct"]) if r["atr_pct"] is not None else None,
            rsi=float(r["rsi"]) if r["rsi"] is not None else None,
            volume_ratio=float(r["volume_ratio"]) if r["volume_ratio"] is not None else None,
            sector_tailwind=bool(r["sector_tailwind"]),
            macd_bullish=bool(r["macd_bullish"]),
        )
        for r in rows
    ]


def resolve_learning_outcomes(*, days: int = 14) -> list[LearningOutcomeRow]:
    """
    Broker truth wins per (trade_date, symbol).
    Coach/EOD used only when no broker record exists.
    """
    cutoff = (datetime.now(IST).date() - timedelta(days=days)).isoformat()
    coach_rows = _coach_outcome_rows(days=days)
    broker_by_key = _broker_outcomes_since(cutoff)

    merged: list[LearningOutcomeRow] = []
    seen: set[tuple[str, str]] = set()

    for coach in coach_rows:
        key = (coach.trade_date, coach.symbol.upper())
        if key in seen:
            continue
        seen.add(key)
        if key in broker_by_key:
            broker = broker_by_key[key]
            merged.append(
                LearningOutcomeRow(
                    trade_date=broker.trade_date,
                    symbol=broker.symbol,
                    outcome=broker.outcome,
                    source=LearningOutcomeSource.BROKER,
                    realized_pnl=broker.realized_pnl,
                    prep_score=coach.prep_score,
                    checklist_passed=coach.checklist_passed,
                    atr_pct=coach.atr_pct,
                    rsi=coach.rsi,
                    volume_ratio=coach.volume_ratio,
                    sector_tailwind=coach.sector_tailwind,
                    macd_bullish=coach.macd_bullish,
                )
            )
        else:
            merged.append(coach)

    for key, broker in broker_by_key.items():
        if key not in seen:
            merged.append(broker)
            seen.add(key)

    merged.sort(key=lambda r: (r.trade_date, r.symbol), reverse=True)
    return merged


def learning_source_stats(*, days: int = 14) -> dict:
    rows = resolve_learning_outcomes(days=days)
    broker_n = sum(1 for r in rows if r.source == LearningOutcomeSource.BROKER)
    coach_n = sum(1 for r in rows if r.source == LearningOutcomeSource.COACH_FALLBACK)
    return {
        "total": len(rows),
        "broker": broker_n,
        "coach_fallback": coach_n,
        "broker_pct": round(100.0 * broker_n / len(rows), 1) if rows else 0.0,
    }


def broker_trade_for_symbol(trade_date: str, symbol: str) -> TradeRecord | None:
    sym = normalize_equity_symbol(symbol)
    records = fetch_trade_records(trade_date=trade_date, symbol=sym, limit=5)
    return records[0] if records else None
