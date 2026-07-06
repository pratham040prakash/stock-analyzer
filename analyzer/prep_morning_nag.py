"""8:45 AM Telegram nag when last night's MIS prep is incomplete."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.nse_holidays import skip_scheduled_job_reason
from analyzer.prep_status import is_nightly_prep_complete, prep_incomplete_reasons, prep_status_for
from analyzer.trade_selection import load_selected_symbols
from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "prep_morning_nag.json"
NAG_WINDOW = (8, 45, 8, 55)


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


def was_prep_nag_sent(trade_date: str) -> bool:
    return bool(_load_state().get(trade_date, {}).get("sent"))


def mark_prep_nag_sent(trade_date: str) -> None:
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


def format_prep_morning_nag() -> str:
    status = prep_status_for()
    trade_date = status["trade_date"]
    selected = load_selected_symbols(trade_date)
    lines = [f"*MIS prep incomplete — {trade_date}*"]
    for reason in prep_incomplete_reasons(status):
        lines.append(f"· {reason}")
    if selected:
        lines.append(f"_Selected so far:_ **{', '.join(selected)}**")
    lines.append("")
    lines.append("Open **Intraday** tab now — market opens **9:15 IST**.")
    lines.append("_Not financial advice._")
    return "\n".join(lines)


def needs_prep_nag(trade_date: str | None = None) -> bool:
    status = prep_status_for(trade_date)
    return not is_nightly_prep_complete(status)


def run_prep_morning_nag(*, force: bool = False) -> tuple[int, str]:
    """Send Telegram once if prep checklist incomplete before open."""
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    now = datetime.now(IST)
    trade_date = session_target_date(now)

    if not force:
        skip = skip_scheduled_job_reason(now)
        if skip:
            return 0, skip
        if not _in_window(now, *NAG_WINDOW):
            return 0, "Outside 8:45–8:55 IST prep nag window"
        if was_prep_nag_sent(trade_date):
            return 0, f"Prep nag already sent for {trade_date}"
        if not needs_prep_nag(trade_date):
            return 0, "Prep complete — no nag needed"

    if not telegram_configured():
        return 0, "Telegram not configured"

    ok, err = send_telegram_broadcast(format_prep_morning_nag(), alert_type="intraday")
    if ok:
        mark_prep_nag_sent(trade_date)
        return 1, f"Prep nag sent for {trade_date}"
    return 0, err


def maybe_send_prep_morning_nag() -> None:
    """Called from app during pre-open window."""
    run_prep_morning_nag()
