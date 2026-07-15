"""Auto-pick recommended ★ option leg at 9:10 PM if user has not starred manually."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "intraday" / "options_selection_auto.json"
)
AUTO_WINDOW = (21, 10, 21, 25)


def _ensure_dir() -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_state() -> dict:
    _ensure_dir()
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(data: dict) -> None:
    _ensure_dir()
    STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def was_auto_option_select_run(trade_date: str) -> bool:
    return bool(_load_state().get(trade_date, {}).get("ran"))


def mark_auto_option_select_run(trade_date: str) -> None:
    data = _load_state()
    data[trade_date] = {
        "ran": True,
        "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
    }
    _save_state(data)


def _in_window(now: datetime, start_h: int, start_m: int, end_h: int, end_m: int) -> bool:
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=59, microsecond=0)
    return start <= now <= end


def run_auto_option_selection(*, force: bool = False) -> tuple[int, str]:
    """
    At 9:10 PM IST, star the top ★ recommended CE/PE from tonight's snapshot.
    Returns (1 if ran else 0, status).
    """
    from analyzer.options_trade_selection import auto_select_recommended_option

    now = datetime.now(IST)
    trade_date = session_target_date(now)

    if not force:
        if now.weekday() >= 5:
            return 0, "Weekend — no option auto-select"
        if not _in_window(now, *AUTO_WINDOW):
            return 0, "Outside 9:10–21:25 IST option auto-select window"
        if was_auto_option_select_run(trade_date):
            return 0, f"Option auto-select already ran for {trade_date}"

    ok, msg = auto_select_recommended_option(trade_date=trade_date)
    if ok:
        mark_auto_option_select_run(trade_date)
        return 1, msg
    if force:
        return 0, msg
    mark_auto_option_select_run(trade_date)
    return 0, msg
