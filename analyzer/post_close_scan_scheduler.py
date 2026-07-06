"""Post-close Quick scan (3:45 PM IST) — save tomorrow's top 5 without opening the app."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "intraday" / "post_close_scan.json"
)
SCAN_WINDOW = (15, 45, 16, 15)


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
    return trade_date or session_target_date()


def was_post_close_scan_sent(prep_for: str | None = None) -> bool:
    prep_for = prep_for or prep_session_key()
    return bool(_load_state().get(prep_for, {}).get("sent"))


def post_close_scan_meta(prep_for: str | None = None) -> dict:
    prep_for = prep_for or prep_session_key()
    return dict(_load_state().get(prep_for, {}))


def mark_post_close_scan_sent(
    prep_for: str | None = None,
    *,
    equity_count: int = 0,
    telegram_sent: bool = False,
) -> None:
    prep_for = prep_for or prep_session_key()
    data = _load_state()
    data[prep_for] = {
        "sent": True,
        "equity_count": equity_count,
        "telegram_sent": telegram_sent,
        "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
    }
    _save_state(data)


def _in_window(now: datetime, start_h: int, start_m: int, end_h: int, end_m: int) -> bool:
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=59, microsecond=0)
    return start <= now <= end


def run_post_close_scan(
    market: str = "india",
    *,
    force: bool = False,
    send_telegram: bool = True,
    scheduled: bool = False,
) -> tuple[int, str]:
    """
    Quick scan + persist top 5 after market close.
    Returns (1 if ran else 0, status message).
    """
    from analyzer.intraday_pulse_source import DEFAULT_INTRADAY_PULSE_PERIOD, run_quick_watchlist_scan
    from analyzer.intraday_watchlist import build_intraday_watchlist
    from analyzer.market_session import market_session_status
    from analyzer.nse_holidays import skip_scheduled_job_reason
    from analyzer.prep_status import mark_prep_step
    from analyzer.watchlist_persist import persist_watchlist_state
    from analyzer.watchlist_pins import TOP_TOMORROW_PICKS

    now = datetime.now(IST)
    prep_for = prep_session_key()

    if not force:
        skip = skip_scheduled_job_reason(now)
        if skip:
            return 0, skip
        if market_session_status().get("is_open"):
            return 0, "Market still open — post-close scan waits until after 3:30 PM"
        if was_post_close_scan_sent(prep_for):
            return 0, f"Post-close scan already done for {prep_for}"
        if scheduled and not _in_window(now, *SCAN_WINDOW):
            return 0, "Outside 3:45–4:15 PM IST window"

    try:
        report = run_quick_watchlist_scan(market, DEFAULT_INTRADAY_PULSE_PERIOD, use_cache=False)
    except Exception as exc:
        return 0, f"Scan failed: {exc}"

    if not report or not getattr(report, "stock_map", None):
        return 0, "Quick scan returned no stocks"

    wl = build_intraday_watchlist(report, limit=TOP_TOMORROW_PICKS)
    if not wl.picks:
        return 0, "No watchlist picks built"

    prep_date = market_session_status().get("date", "")
    persist_watchlist_state(wl, prep_date=prep_date, force=True)
    mark_prep_step("equity", trade_date=prep_for)

    telegram_sent = False
    if send_telegram:
        from analyzer.suggestions_telegram import format_nightly_suggestions_telegram
        from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured
        from analyzer.watchlist_pins import load_pinned_plans

        if telegram_configured():
            msg = format_nightly_suggestions_telegram(
                load_pinned_plans(),
                market_bias=wl.market_bias,
                prep_date=prep_date,
            )
            ok, _ = send_telegram_broadcast(msg, alert_type="morning")
            telegram_sent = ok
            if ok:
                mark_prep_step("telegram", trade_date=prep_for)

    mark_post_close_scan_sent(
        prep_for,
        equity_count=len(wl.picks),
        telegram_sent=telegram_sent,
    )
    try:
        from analyzer.structured_log import log_event

        log_event("post_close_scan", ok=True, picks=len(wl.picks), prep_for=prep_for)
    except Exception:
        pass
    parts = [f"Saved **{len(wl.picks)}** picks for **{prep_for}**"]
    if telegram_sent:
        parts.append("Telegram sent")
    return 1, " · ".join(parts)


def maybe_run_post_close_scan() -> None:
    """In-app fallback when Streamlit is open after close."""
    run_post_close_scan(force=False, send_telegram=True, scheduled=False)
