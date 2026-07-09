"""MIS trade journal — mistakes and fixes after each session."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "trade_journal.json"
MAX_ENTRIES = 200


@dataclass
class TradeJournalEntry:
    trade_date: str
    symbol: str
    leg: str
    entry: float | None
    exit: float | None
    pnl_inr: float | None
    mistake: str
    fix: str
    saved_at: str


def _ensure_dir() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_all() -> list[dict]:
    _ensure_dir()
    if not STORE_PATH.exists():
        return []
    try:
        data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
        return list(data.get("entries", []))
    except (json.JSONDecodeError, OSError):
        return []


def _save_all(entries: list[dict]) -> None:
    _ensure_dir()
    payload = {
        "version": 1,
        "updated_at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "entries": entries[:MAX_ENTRIES],
    }
    STORE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sanitize(text: str, max_len: int = 500) -> str:
    clean = re.sub(r"[\r\n]+", " ", text.strip())
    return clean[:max_len]


def save_journal_entry(
    *,
    trade_date: str | None = None,
    symbol: str,
    leg: str = "",
    entry: float | None = None,
    exit: float | None = None,
    pnl_inr: float | None = None,
    mistake: str = "",
    fix: str = "",
) -> TradeJournalEntry:
    trade_date = trade_date or session_target_date()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    row = {
        "trade_date": trade_date,
        "symbol": _sanitize(symbol, 64),
        "leg": _sanitize(leg, 32),
        "entry": entry,
        "exit": exit,
        "pnl_inr": pnl_inr,
        "mistake": _sanitize(mistake),
        "fix": _sanitize(fix),
        "saved_at": now,
    }
    entries = _load_all()
    entries.insert(0, row)
    _save_all(entries)
    return TradeJournalEntry(**row)


def load_journal_entries(*, limit: int = 30) -> list[TradeJournalEntry]:
    rows = []
    for r in _load_all()[:limit]:
        rows.append(
            TradeJournalEntry(
                trade_date=r.get("trade_date", ""),
                symbol=r.get("symbol", ""),
                leg=r.get("leg", ""),
                entry=r.get("entry"),
                exit=r.get("exit"),
                pnl_inr=r.get("pnl_inr"),
                mistake=r.get("mistake", ""),
                fix=r.get("fix", ""),
                saved_at=r.get("saved_at", ""),
            )
        )
    return rows


def delete_journal_entry(trade_date: str, symbol: str, saved_at: str) -> bool:
    entries = _load_all()
    new_entries = [
        e for e in entries
        if not (
            e.get("trade_date") == trade_date
            and e.get("symbol") == symbol
            and e.get("saved_at") == saved_at
        )
    ]
    if len(new_entries) == len(entries):
        return False
    _save_all(new_entries)
    return True
