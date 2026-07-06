"""Nightly MIS prep checklist persistence (equity · options · telegram · selection)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.trade_selection import is_selection_complete
from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STATUS_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "prep_status.json"
PREP_STEPS = ("equity", "options", "telegram", "selection")


def _ensure_dir() -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_all() -> dict:
    _ensure_dir()
    if not STATUS_PATH.exists():
        return {}
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: dict) -> None:
    _ensure_dir()
    STATUS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def prep_status_for(trade_date: str | None = None) -> dict:
    trade_date = trade_date or session_target_date()
    row = dict(_load_all().get(trade_date, {}))
    selection_done = bool(row.get("selection")) or is_selection_complete(trade_date)
    return {
        "trade_date": trade_date,
        "equity": bool(row.get("equity")),
        "options": bool(row.get("options")),
        "telegram": bool(row.get("telegram")),
        "selection": selection_done,
        "updated_at": row.get("updated_at", ""),
    }


def mark_prep_step(step: str, *, trade_date: str | None = None, done: bool = True) -> dict:
    if step not in PREP_STEPS:
        raise ValueError(f"Unknown prep step: {step}")
    trade_date = trade_date or session_target_date()
    data = _load_all()
    row = data.setdefault(trade_date, {})
    row[step] = done
    row["updated_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    _save_all(data)
    return prep_status_for(trade_date)


def sync_selection_prep_step(trade_date: str | None = None) -> dict:
    """Mark selection step when 2 trades are starred."""
    trade_date = trade_date or session_target_date()
    if is_selection_complete(trade_date):
        return mark_prep_step("selection", trade_date=trade_date, done=True)
    return prep_status_for(trade_date)


def prep_complete_count(status: dict | None = None) -> int:
    status = status or prep_status_for()
    return sum(1 for k in PREP_STEPS if status.get(k))


def is_nightly_prep_complete(status: dict | None = None) -> bool:
    status = status or prep_status_for()
    return all(status.get(k) for k in PREP_STEPS)


def prep_incomplete_reasons(status: dict | None = None) -> list[str]:
    status = status or prep_status_for()
    labels = {
        "equity": "Run **Quick scan** / **Prep all** for top 5 equity",
        "options": "Load **Nifty/Bank Nifty CE/PE**",
        "telegram": "Send **MIS prep to Telegram**",
        "selection": "**Star 2** names to trade tomorrow",
    }
    return [labels[k] for k in PREP_STEPS if not status.get(k)]
