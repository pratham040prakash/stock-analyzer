"""9:46 AM refresh of Nifty/Bank Nifty CE/PE after opening range forms."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.affordable_invest import DEFAULT_MAX_OPTION_LOT_COST_INR
from analyzer.market_session import market_session_status
from analyzer.nse_holidays import skip_scheduled_job_reason
from analyzer.options_expiry_watchlist import build_options_expiry_watchlist
from analyzer.options_watchlist_history import save_options_watchlist_snapshot
from analyzer.prep_status import mark_prep_step
from analyzer.watchlist_history import session_target_date
from analyzer.watchlist_telegram import format_options_watchlist_telegram

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class MorningOptionsRescanResult:
    pick_count: int
    recommended_count: int
    telegram_sent: bool
    telegram_error: str
    errors: list[str]


def format_morning_options_rescan_telegram(wl) -> str:
    trade_date = session_target_date()
    lines = [
        f"*☀️ Options re-scan — {trade_date}*",
        "_After 9:45 OR — fresh CE/PE ★. Trade only if entry gate is green._",
        "",
    ]
    lines.append(
        format_options_watchlist_telegram(
            wl.picks,
            prep_date=trade_date,
            stars_only=True,
        )
    )
    return "\n".join(lines)


def run_morning_options_rescan(
    *,
    max_lot_cost: float | None = None,
    send_telegram: bool = True,
    market: str = "india",
) -> MorningOptionsRescanResult:
    """Rebuild options watchlist once OR is known (~9:46 AM)."""
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    max_lot = max_lot_cost if max_lot_cost is not None else DEFAULT_MAX_OPTION_LOT_COST_INR

    wl = build_options_expiry_watchlist(max_lot_cost=max_lot, market=market)
    tg_sent = False
    tg_err = ""

    if wl.picks:
        save_options_watchlist_snapshot(
            wl.picks,
            prep_date=market_session_status().get("date", ""),
        )
        mark_prep_step("options")

    if send_telegram and wl.picks and telegram_configured():
        msg = format_morning_options_rescan_telegram(wl)
        ok, err = send_telegram_broadcast(msg, alert_type="intraday")
        tg_sent = ok
        tg_err = err or ""

    rec = sum(1 for p in wl.picks if p.recommended)
    if wl.picks:
        mark_morning_options_rescan_sent(
            market_session_status().get("date", session_target_date()),
            pick_count=len(wl.picks),
        )
    return MorningOptionsRescanResult(
        pick_count=len(wl.picks),
        recommended_count=rec,
        telegram_sent=tg_sent,
        telegram_error=tg_err,
        errors=list(wl.errors),
    )


def run_morning_options_rescan_job() -> tuple[int, str]:
    """Scheduled job entry — only during 9:46–10:00 IST on open days."""
    now = datetime.now(IST)
    skip = skip_scheduled_job_reason(now)
    if skip:
        return 0, skip
    session = market_session_status()
    if not session.get("is_open"):
        return 0, "Market closed"
    if not (now.hour == 9 and now.minute >= 46) and not (now.hour == 10 and now.minute == 0):
        return 0, "Outside 9:46–10:00 window"

    result = run_morning_options_rescan(send_telegram=True)
    if result.errors and result.pick_count == 0:
        return 0, "; ".join(result.errors[:2])
    msg = f"Re-scanned {result.pick_count} CE/PE ({result.recommended_count} ★)"
    if result.telegram_sent:
        msg += " · Telegram sent"
    elif result.telegram_error:
        msg += f" · Telegram: {result.telegram_error}"
    return result.pick_count, msg


def was_morning_options_rescan_sent(trade_date: str) -> bool:
    from pathlib import Path
    import json

    path = Path(__file__).resolve().parent.parent / "data" / "intraday" / "morning_options_rescan.json"
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(data.get(trade_date, {}).get("sent"))
    except (json.JSONDecodeError, OSError):
        return False


def mark_morning_options_rescan_sent(trade_date: str, *, pick_count: int = 0) -> None:
    from pathlib import Path
    import json

    path = Path(__file__).resolve().parent.parent / "data" / "intraday" / "morning_options_rescan.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data[trade_date] = {
        "sent": True,
        "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "pick_count": pick_count,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
