"""8:50 AM Telegram — today's pick list (entry / target / stop)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "intraday" / "morning_suggestions.json"
)
MORNING_WINDOW = (8, 48, 9, 5)


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


def was_morning_suggestions_sent(trade_date: str | None = None) -> bool:
    trade_date = trade_date or session_target_date()
    return bool(_load_state().get(trade_date, {}).get("sent"))


def morning_suggestions_meta(trade_date: str | None = None) -> dict:
    trade_date = trade_date or session_target_date()
    return dict(_load_state().get(trade_date, {}))


def mark_morning_suggestions_sent(trade_date: str | None = None) -> None:
    trade_date = trade_date or session_target_date()
    data = _load_state()
    data[trade_date] = {
        "sent": True,
        "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
    }
    _save_state(data)


def _in_window(now: datetime, start_h: int, start_m: int, end_h: int, end_m: int) -> bool:
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=59, microsecond=0)
    return start <= now <= end


def run_morning_suggestions(*, force: bool = False) -> tuple[int, str]:
    """Send compact morning pick list once per session."""
    from analyzer.nse_holidays import skip_scheduled_job_reason
    from analyzer.suggestions_telegram import format_morning_suggestions_telegram
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    now = datetime.now(IST)
    trade_date = session_target_date(now)

    if not force:
        skip = skip_scheduled_job_reason(now)
        if skip:
            return 0, skip
        if not _in_window(now, *MORNING_WINDOW):
            return 0, "Outside 8:48–9:05 AM morning list window"
        if was_morning_suggestions_sent(trade_date):
            return 0, f"Morning list already sent for {trade_date}"

    if not telegram_configured():
        return 0, "Telegram not configured"

    ok, err = send_telegram_broadcast(
        format_morning_suggestions_telegram(trade_date=trade_date),
        alert_type="morning",
    )
    if ok:
        mark_morning_suggestions_sent(trade_date)
        return 1, f"Morning pick list sent for {trade_date}"
    return 0, err
