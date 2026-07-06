"""Scheduled nightly MIS prep (9 PM IST) — idempotent once per prep session."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "nightly_prep_scheduler.json"

# 21:00–22:30 IST window (weekdays)
PREP_WINDOW = (21, 0, 22, 30)


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


def prep_session_key(trade_date: str | None = None) -> str:
    """Date the prep is being built for (tomorrow's MIS session after close)."""
    return trade_date or session_target_date()


def was_nightly_prep_sent(prep_for: str | None = None) -> bool:
    prep_for = prep_for or prep_session_key()
    return bool(_load_state().get(prep_for, {}).get("sent"))


def mark_nightly_prep_sent(prep_for: str | None = None) -> None:
    prep_for = prep_for or prep_session_key()
    data = _load_state()
    data[prep_for] = {
        "sent": True,
        "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
    }
    _save_state(data)


def _in_window(now: datetime, start_h: int, start_m: int, end_h: int, end_m: int) -> bool:
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=59, microsecond=0)
    return start <= now <= end


def should_run_scheduled_prep(now: datetime | None = None, *, force: bool = False) -> bool:
    if force:
        return True
    now = now or datetime.now(IST)
    if now.weekday() >= 5:
        return False
    if not _in_window(now, *PREP_WINDOW):
        return False
    return not was_nightly_prep_sent()


def run_scheduled_nightly_prep(
    market: str = "india",
    *,
    force: bool = False,
    send_telegram: bool = True,
) -> tuple[int, str]:
    """
    Run prep if in 9 PM window and not yet sent for tomorrow's session.
    Returns (1 if ran else 0, status message).
    """
    from analyzer.affordable_invest import DEFAULT_MAX_OPTION_LOT_COST_INR
    from analyzer.intraday_prefs import load_intraday_prefs
    from analyzer.nightly_prep import run_nightly_prep

    now = datetime.now(IST)
    prep_for = prep_session_key()

    if not should_run_scheduled_prep(now, force=force):
        if now.weekday() >= 5 and not force:
            return 0, "Weekend — no nightly prep"
        if was_nightly_prep_sent(prep_for):
            return 0, f"Nightly prep already sent for {prep_for}"
        return 0, "Outside 9:00–22:30 IST prep window"

    prefs = load_intraday_prefs()
    lot_budget = float(
        getattr(prefs, "option_lot_budget", None) or DEFAULT_MAX_OPTION_LOT_COST_INR
    )

    result, _ = run_nightly_prep(
        market,
        max_lot_cost=lot_budget,
        send_telegram=send_telegram,
        use_cache=False,
    )
    mark_nightly_prep_sent(prep_for)

    parts = [
        f"Prep for **{prep_for}**",
        f"equity **{result.equity_count}**",
        f"options **{result.options_count}**",
    ]
    if result.telegram_sent:
        parts.append("Telegram sent")
    elif result.telegram_error:
        parts.append(result.telegram_error)
    for err in result.errors[:2]:
        parts.append(err)
    return 1, " · ".join(parts)
