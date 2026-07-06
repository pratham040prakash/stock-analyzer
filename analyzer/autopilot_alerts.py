"""Telegram alerts when Autopilot steps miss their window."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.autopilot_status import build_autopilot_status
from analyzer.market_session import market_session_status
from analyzer.mis_eod_summary import was_eod_summary_sent
from analyzer.nse_holidays import skip_scheduled_job_reason
from analyzer.post_close_scan_scheduler import was_post_close_scan_sent
from analyzer.nightly_prep_scheduler import prep_session_key
from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "autopilot_alerts.json"


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(data: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _alert_sent(key: str, day: str) -> bool:
    return bool(_load_state().get(day, {}).get(key))


def _mark_alert_sent(key: str, day: str) -> None:
    data = _load_state()
    data.setdefault(day, {})[key] = datetime.now(IST).strftime("%H:%M IST")
    _save_state(data)


def collect_autopilot_gaps() -> list[str]:
    """Human-readable gaps for today (no side effects)."""
    now = datetime.now(IST)
    if skip_scheduled_job_reason(now):
        return []

    gaps: list[str] = []
    trade_date = session_target_date(now)
    prep_for = prep_session_key()
    status = build_autopilot_status()
    session = market_session_status()
    h, m = now.hour, now.minute

    if h >= 16 and not was_eod_summary_sent(trade_date):
        eod_step = next((s for s in status.steps if s.key == "eod_score"), None)
        if eod_step and not eod_step.done_today:
            gaps.append(f"EOD score not done for **{trade_date}**")

    if h >= 16 and m >= 30 and not was_post_close_scan_sent(prep_for):
        scan_step = next((s for s in status.steps if s.key == "post_close_scan"), None)
        if scan_step and not scan_step.done_today and not session.get("is_open"):
            gaps.append(f"Post-close Quick scan missing for **{prep_for}**")

    if status.schedules_installed == 0:
        gaps.append("Autopilot schedules not installed — enable in sidebar")

    return gaps


def maybe_send_autopilot_failure_alert() -> tuple[int, str]:
    """Send one Telegram per gap per day after grace windows."""
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    now = datetime.now(IST)
    day = now.strftime("%Y-%m-%d")
    gaps = collect_autopilot_gaps()
    if not gaps:
        return 0, "No autopilot gaps"

    if not telegram_configured():
        return 0, "Telegram not configured"

    to_send = [g for g in gaps if not _alert_sent(g[:20], day)]
    if not to_send:
        return 0, "Alerts already sent today"

    msg = "*⚠️ Autopilot check*\n" + "\n".join(f"· {g}" for g in to_send)
    msg += "\n\n_Open Suggestions → 🤖 Autopilot or run step manually._"
    ok, err = send_telegram_broadcast(msg, alert_type="intraday")
    if ok:
        for g in to_send:
            _mark_alert_sent(g[:20], day)
        return len(to_send), "Autopilot gap alert sent"
    return 0, err
