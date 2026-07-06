"""9:15 checklist and 3:20 square-off Telegram reminders."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.market_session import market_session_status
from analyzer.nse_holidays import skip_scheduled_job_reason
from analyzer.options_watchlist_history import fetch_options_snapshots_for_date
from analyzer.trade_selection import effective_trade_plans, load_selected_symbols
from analyzer.watchlist_history import session_target_date
from analyzer.watchlist_telegram import (
    format_options_watchlist_telegram,
    format_pinned_watchlist_telegram,
)

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "session_reminders.json"

OPEN_WINDOW = (9, 15, 9, 26)  # start h,m end h,m
EARLY_SQUARE_WINDOW = (15, 15, 15, 19)
SQUARE_WINDOW = (15, 20, 15, 31)


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


def _in_window(now: datetime, start_h: int, start_m: int, end_h: int, end_m: int) -> bool:
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    return start <= now <= end


def _was_sent(kind: str, day: str) -> bool:
    return bool(_load_state().get(day, {}).get(kind))


def _mark_sent(kind: str, day: str) -> None:
    data = _load_state()
    day_row = data.setdefault(day, {})
    day_row[kind] = datetime.now(IST).strftime("%H:%M IST")
    _save_state(data)


def format_open_reminder() -> str:
    from analyzer.gift_nifty import format_gift_nifty_telegram_line

    pins = effective_trade_plans()
    selected = load_selected_symbols()
    opt_snaps = fetch_options_snapshots_for_date(session_target_date())
    lines = [
        "*MIS session open — 9:15 IST*",
        format_gift_nifty_telegram_line(),
        "1. Open **Suggestions** → tick **Daily MIS checklist**",
    ]
    if selected:
        lines.append(
            f"2. Trade **only your 2 picks:** **{', '.join(selected)}** "
            "(+ options ★ side if loaded)"
        )
    else:
        lines.append(
            "2. **Star 2** names in Intraday (or trade top 2 by rank) · options ★ only"
        )
    lines.append("3. Place **stop on Kite** before entry")
    if pins:
        lines.append("")
        lines.append(format_pinned_watchlist_telegram(pins, with_shares=True).split("\n", 1)[-1])
    else:
        lines.append("")
        lines.append("_No equity picks yet — run **Quick scan** on Suggestions tonight._")
    if opt_snaps:
        lines.append("")
        lines.append(format_options_watchlist_telegram(opt_snaps, stars_only=True))
    else:
        lines.append("")
        lines.append("_No options CE/PE loaded — optional advanced section on Suggestions._")
    lines.append("_Not financial advice._")
    return "\n".join(lines)


def format_early_square_off_reminder() -> str:
    pins = effective_trade_plans()
    opt_snaps = fetch_options_snapshots_for_date(session_target_date())
    syms = ", ".join(p.symbol for p in pins[:3]) if pins else "MIS positions"
    if pins and len(pins) > 3:
        syms += f" +{len(pins) - 3} more"
    opt_bits = [
        f"{s.fno_symbol} {s.option_type}"
        for s in opt_snaps
        if s.recommended
    ]
    opt_line = f" Options: **{', '.join(opt_bits)}**." if opt_bits else ""
    return (
        "*MIS heads-up — 3:15 PM IST*\n"
        f"**5 minutes** to square-off window. Review: **{syms}**.{opt_line}\n"
        "Hard close all MIS by **3:20 PM**.\n"
        "_Not financial advice._"
    )


def format_square_off_reminder() -> str:
    pins = effective_trade_plans()
    opt_snaps = fetch_options_snapshots_for_date(session_target_date())
    syms = ", ".join(p.symbol for p in pins) if pins else "all MIS equity"
    opt_bits = [
        f"{s.fno_symbol} {s.option_type} {s.strike:g}"
        for s in opt_snaps
        if s.recommended
    ]
    opt_line = ""
    if opt_bits:
        opt_line = f"\nOptions: **{', '.join(opt_bits)}**."
    return (
        "*MIS square-off — 3:20 PM IST*\n"
        f"Close intraday positions: **{syms}**.{opt_line}\n"
        "Then: log trades + **Score today's picks** in Track Record.\n"
        "_Not financial advice._"
    )


def run_session_reminders(*, force: str | None = None) -> tuple[int, str]:
    """
    Send open and/or square-off reminders if in time window and not yet sent.
    force: 'open' | 'early_square_off' | 'square_off' | None
    Returns (count_sent, status).
    """
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    if not telegram_configured():
        return 0, "Telegram not configured"

    now = datetime.now(IST)
    skip = skip_scheduled_job_reason(now) if not force else None
    if skip:
        return 0, skip

    day = now.strftime("%Y-%m-%d")
    sent = 0
    messages: list[str] = []

    if force == "open" or (not force and _in_window(now, *OPEN_WINDOW) and not _was_sent("open", day)):
        messages.append(format_open_reminder())
        _mark_sent("open", day)
        sent += 1
    elif force == "early_square_off" or (
        not force
        and _in_window(now, *EARLY_SQUARE_WINDOW)
        and not _was_sent("early_square_off", day)
    ):
        messages.append(format_early_square_off_reminder())
        _mark_sent("early_square_off", day)
        sent += 1
    elif force == "square_off" or (
        not force
        and _in_window(now, *SQUARE_WINDOW)
        and not _was_sent("square_off", day)
    ):
        messages.append(format_square_off_reminder())
        _mark_sent("square_off", day)
        sent += 1

    if not messages:
        return 0, "No reminders due in this window"

    ok, err = send_telegram_broadcast("\n\n".join(messages), alert_type="intraday")
    if ok:
        return sent, f"Sent {sent} session reminder(s)"
    return 0, err


def maybe_send_session_reminders() -> None:
    """Called from app when market is open during reminder windows."""
    session = market_session_status()
    if not session.get("is_open"):
        return
    run_session_reminders()
