"""Index OR reversal alerts — invalidate starred CE/PE when spot flips."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.intraday_beginner_tips import OPENING_OBSERVE_UNTIL
from analyzer.opening_range_confirm import fetch_symbol_opening_range
from analyzer.options_trade_selection import load_selected_option
from analyzer.providers import get_live_ltp
from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "options_reversal_alerts.json"

INDEX_YAHOO = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
}

INDEX_LABEL = {
    "NIFTY": "Nifty 50",
    "BANKNIFTY": "Bank Nifty",
}


@dataclass
class IndexReversalStatus:
    fno_symbol: str
    option_type: str
    strike: float
    index_label: str
    spot: float | None
    or_high: float
    or_low: float
    phase: str  # observe | ok | invalidated
    label: str
    emoji: str
    detail: str
    opposite_side: str
    action: str


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


def _state_key(trade_date: str, leg_key: str) -> str:
    return f"{trade_date}:{leg_key}"


def _was_reversal_sent(trade_date: str, leg_key: str) -> bool:
    return bool(_load_state().get(_state_key(trade_date, leg_key), {}).get("invalidated"))


def _mark_reversal_sent(trade_date: str, leg_key: str) -> None:
    data = _load_state()
    key = _state_key(trade_date, leg_key)
    data[key] = {"invalidated": datetime.now(IST).strftime("%H:%M IST")}
    _save_state(data)


def _past_or_window(now: datetime) -> bool:
    cutoff = now.replace(
        hour=OPENING_OBSERVE_UNTIL[0],
        minute=OPENING_OBSERVE_UNTIL[1],
        second=0,
        microsecond=0,
    )
    return now >= cutoff


def index_yahoo_symbol(fno_symbol: str) -> str | None:
    key = fno_symbol.upper().strip()
    return INDEX_YAHOO.get(key)


def leg_key(fno_symbol: str, option_type: str, strike: float) -> str:
    return f"{fno_symbol.upper()}:{option_type.upper()}:{strike:g}"


def assess_option_index_thesis(
    option_type: str,
    *,
    fno_symbol: str,
    strike: float,
    spot: float | None,
    or_high: float,
    or_low: float,
    now: datetime | None = None,
) -> IndexReversalStatus:
    """PE invalidated above OR high; CE invalidated below OR low (after 9:45)."""
    now = now or datetime.now(IST)
    opt = option_type.upper().strip()
    index_label = INDEX_LABEL.get(fno_symbol.upper(), fno_symbol)
    opposite = "CE" if opt == "PE" else "PE"

    if now.weekday() >= 5:
        return IndexReversalStatus(
            fno_symbol, opt, strike, index_label, spot, or_high, or_low,
            "observe", "Weekend", "⚪", "Market closed.", opposite, "No trade",
        )
    if spot is None or spot <= 0:
        return IndexReversalStatus(
            fno_symbol, opt, strike, index_label, spot, or_high, or_low,
            "observe", "No index LTP", "⚪", "Index price unavailable.", opposite, "Wait",
        )
    if not _past_or_window(now):
        return IndexReversalStatus(
            fno_symbol, opt, strike, index_label, spot, or_high, or_low,
            "observe",
            "Observe OR",
            "🟡",
            f"Wait until 9:45 — OR High ₹{or_high:,.0f} · OR Low ₹{or_low:,.0f}.",
            opposite,
            "No entry before 9:45",
        )

    if opt == "PE" and spot > or_high:
        return IndexReversalStatus(
            fno_symbol, opt, strike, index_label, spot, or_high, or_low,
            "invalidated",
            "PE thesis broken",
            "🔴",
            f"{index_label} **₹{spot:,.0f}** reclaimed **OR high ₹{or_high:,.0f}** — "
            f"bearish PE idea invalid.",
            opposite,
            f"Exit PE · refresh CE/PE — consider {opposite} only on fresh ★",
        )
    if opt == "CE" and spot < or_low:
        return IndexReversalStatus(
            fno_symbol, opt, strike, index_label, spot, or_high, or_low,
            "invalidated",
            "CE thesis broken",
            "🔴",
            f"{index_label} **₹{spot:,.0f}** broke **OR low ₹{or_low:,.0f}** — "
            f"bullish CE idea invalid.",
            opposite,
            f"Exit CE · refresh CE/PE — consider {opposite} only on fresh ★",
        )

    if opt == "PE":
        detail = (
            f"{index_label} ₹{spot:,.0f} · OR ₹{or_low:,.0f}–₹{or_high:,.0f}. "
            f"PE OK while spot ≤ OR high."
        )
    else:
        detail = (
            f"{index_label} ₹{spot:,.0f} · OR ₹{or_low:,.0f}–₹{or_high:,.0f}. "
            f"CE OK while spot ≥ OR low."
        )
    return IndexReversalStatus(
        fno_symbol, opt, strike, index_label, spot, or_high, or_low,
        "ok", "Thesis intact", "🟢", detail, opposite, "Hold plan / trail premium stop",
    )


def assess_pick_index_reversal(
    pick: Any,
    *,
    market: str = "india",
    now: datetime | None = None,
) -> IndexReversalStatus | None:
    fno = getattr(pick, "fno_symbol", pick.get("fno_symbol") if isinstance(pick, dict) else "")
    opt = getattr(pick, "option_type", pick.get("option_type") if isinstance(pick, dict) else "")
    strike = float(getattr(pick, "strike", pick.get("strike", 0) if isinstance(pick, dict) else 0))
    yahoo = index_yahoo_symbol(str(fno))
    if not yahoo:
        return None
    or_rng = fetch_symbol_opening_range(yahoo, market=market)
    if not or_rng:
        return None
    or_high, or_low = or_rng
    spot, _ = get_live_ltp(yahoo, market=market)
    return assess_option_index_thesis(
        str(opt),
        fno_symbol=str(fno),
        strike=strike,
        spot=spot,
        or_high=or_high,
        or_low=or_low,
        now=now,
    )


def format_options_reversal_telegram(status: IndexReversalStatus) -> str:
    leg = f"{status.fno_symbol} {status.option_type} {status.strike:g}"
    return (
        f"*{status.emoji} Index reversal — {leg}*\n"
        f"**{status.label}** — {status.detail}\n"
        f"OR High ₹{status.or_high:,.0f} · OR Low ₹{status.or_low:,.0f}\n"
        f"**Action:** {status.action}"
    )


def check_options_reversal_alerts(
    *,
    trade_date: str | None = None,
    market: str = "india",
    now: datetime | None = None,
) -> list[str]:
    """Return new Telegram messages when starred option thesis is invalidated."""
    trade_date = trade_date or session_target_date()
    now = now or datetime.now(IST)
    pick = load_selected_option(trade_date)
    if not pick:
        return []

    status = assess_pick_index_reversal(pick, market=market, now=now)
    if status is None or status.phase != "invalidated":
        return []

    key = leg_key(pick["fno_symbol"], pick["option_type"], pick["strike"])
    if _was_reversal_sent(trade_date, key):
        return []

    _mark_reversal_sent(trade_date, key)
    return [format_options_reversal_telegram(status)]


def run_options_reversal_alerts(
    *,
    trade_date: str | None = None,
    market: str = "india",
) -> tuple[int, str]:
    from analyzer.market_session import market_session_status
    from analyzer.nse_holidays import skip_scheduled_job_reason
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    now = datetime.now(IST)
    skip = skip_scheduled_job_reason(now)
    if skip:
        return 0, skip
    if not market_session_status().get("is_open"):
        return 0, "Market closed"
    if not telegram_configured():
        return 0, "Telegram not configured"

    messages = check_options_reversal_alerts(trade_date=trade_date, market=market, now=now)
    if not messages:
        return 0, "No index reversal alerts"

    ok, err = send_telegram_broadcast("\n\n".join(messages), alert_type="intraday")
    if ok:
        return len(messages), f"Sent {len(messages)} reversal alert(s)"
    return 0, err
