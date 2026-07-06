"""NSE equity trading calendar — weekdays excluding exchange holidays."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
HOLIDAYS_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "nse_holidays.json"

# Fallback if JSON missing (2026 NSE holidays — update data/nse_holidays.json yearly)
_DEFAULT_HOLIDAYS: set[str] = {
    "2026-01-26",
    "2026-03-03",
    "2026-03-26",
    "2026-03-27",
    "2026-03-31",
    "2026-04-03",
    "2026-04-14",
    "2026-05-01",
    "2026-05-28",
    "2026-06-26",
    "2026-08-15",
    "2026-10-02",
    "2026-10-20",
    "2026-11-09",
    "2026-11-24",
    "2026-12-25",
}


def _load_holiday_set() -> set[str]:
    if HOLIDAYS_PATH.exists():
        try:
            raw = json.loads(HOLIDAYS_PATH.read_text(encoding="utf-8"))
            dates = raw.get("holidays", raw) if isinstance(raw, dict) else raw
            return {str(d) for d in dates}
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    return set(_DEFAULT_HOLIDAYS)


def nse_holidays() -> set[str]:
    return _load_holiday_set()


def _as_date(d: date | str | datetime) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        return date.fromisoformat(d[:10])
    return d


def is_nse_trading_day(d: date | str | datetime) -> bool:
    """True on NSE equity session days (not weekend or exchange holiday)."""
    day = _as_date(d)
    if day.weekday() >= 5:
        return False
    return day.isoformat() not in nse_holidays()


def next_nse_trading_day(d: date | str | datetime) -> date:
    """Next calendar day that is an NSE session."""
    n = _as_date(d) + timedelta(days=1)
    while not is_nse_trading_day(n):
        n += timedelta(days=1)
    return n


def holiday_name(d: date | str) -> str | None:
    """Optional label from JSON metadata."""
    day = _as_date(d).isoformat()
    if not HOLIDAYS_PATH.exists():
        return None
    try:
        raw = json.loads(HOLIDAYS_PATH.read_text(encoding="utf-8"))
        labels = raw.get("labels", {})
        return labels.get(day)
    except (json.JSONDecodeError, OSError):
        return None


def skip_scheduled_job_reason(now: datetime | None = None) -> str | None:
    """
    Return a reason string if today's session jobs should not run; else None.
    Used by reminders, EOD, live alerts, prep nag.
    """
    now = now or datetime.now(IST)
    today = now.date()
    if not is_nse_trading_day(today):
        if today.weekday() >= 5:
            return "Weekend — no NSE session"
        label = holiday_name(today) or "NSE holiday"
        return f"{label} — no session"
    return None
