"""Persist daily MIS checklist ticks (survives browser refresh)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.intraday_beginner_tips import daily_mis_checklist_items
from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "mis_checklist.json"


def _ensure_dir() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_all() -> dict:
    _ensure_dir()
    if not STORE_PATH.exists():
        return {}
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: dict) -> None:
    _ensure_dir()
    STORE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_checklist_done(trade_date: str | None = None) -> dict[str, bool]:
    trade_date = trade_date or session_target_date()
    row = _load_all().get(trade_date, {})
    return {k: bool(v) for k, v in row.get("items", {}).items()}


def save_checklist_item(item_id: str, done: bool, *, trade_date: str | None = None) -> None:
    trade_date = trade_date or session_target_date()
    data = _load_all()
    row = data.setdefault(trade_date, {"items": {}})
    row["items"][item_id] = done
    row["updated_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    _save_all(data)


def save_checklist_done(done_map: dict[str, bool], *, trade_date: str | None = None) -> None:
    trade_date = trade_date or session_target_date()
    data = _load_all()
    data[trade_date] = {
        "items": {k: bool(v) for k, v in done_map.items()},
        "updated_at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
    }
    _save_all(data)


def reset_checklist(trade_date: str | None = None) -> None:
    trade_date = trade_date or session_target_date()
    data = _load_all()
    if trade_date in data:
        del data[trade_date]
        _save_all(data)


def is_checklist_complete(trade_date: str | None = None) -> bool:
    trade_date = trade_date or session_target_date()
    done = load_checklist_done(trade_date)
    items = daily_mis_checklist_items()
    return bool(items) and all(done.get(it.id, False) for it in items)


def checklist_done_count(trade_date: str | None = None) -> tuple[int, int]:
    trade_date = trade_date or session_target_date()
    items = daily_mis_checklist_items()
    done = load_checklist_done(trade_date)
    count = sum(1 for it in items if done.get(it.id, False))
    return count, len(items)
