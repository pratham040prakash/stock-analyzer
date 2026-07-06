"""Indian market session clock (IST)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.nse_holidays import is_nse_trading_day

IST = ZoneInfo("Asia/Kolkata")


def market_session_status() -> dict:
    """Return Indian market session status (NSE hours 9:15–15:30 IST)."""
    now = datetime.now(IST)
    open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
    close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)

    is_weekday = now.weekday() < 5
    is_trading_day = is_nse_trading_day(now.date())
    is_open = is_weekday and is_trading_day and open_time <= now <= close_time

    if not is_weekday:
        status = "Closed (weekend)"
        phase = "weekend"
        next_session = "Opens Mon 9:15 AM IST"
    elif not is_trading_day:
        status = "Closed (NSE holiday)"
        phase = "holiday"
        next_session = "Next NSE session — see calendar"
    elif now < open_time:
        status = "Pre-market"
        phase = "pre_market"
        next_session = "Opens today 9:15 AM IST"
    elif now > close_time:
        status = "Closed (after hours)"
        phase = "after_hours"
        next_session = "Opens Mon 9:15 AM IST" if now.weekday() == 4 else "Opens tomorrow 9:15 AM IST"
    else:
        status = "Market OPEN"
        phase = "open"
        next_session = "Closes 3:30 PM IST"

    return {
        "status": status,
        "is_open": is_open,
        "is_closed": not is_open,
        "phase": phase,
        "next_session": next_session,
        "time_ist": now.strftime("%H:%M:%S IST"),
        "date": now.strftime("%Y-%m-%d"),
    }
