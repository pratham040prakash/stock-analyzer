"""Opening-range confirmation for MIS entries (post 9:45 IST)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.intraday_beginner_tips import OPENING_OBSERVE_UNTIL

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class OrConfirmResult:
    phase: str  # observe | confirmed | wait | invalid
    label: str
    emoji: str
    detail: str
    allow_entry: bool


def _past_or_window(now: datetime) -> bool:
    cutoff = now.replace(
        hour=OPENING_OBSERVE_UNTIL[0],
        minute=OPENING_OBSERVE_UNTIL[1],
        second=0,
        microsecond=0,
    )
    return now >= cutoff


def confirm_or_long_entry(
    ltp: float | None,
    *,
    entry: float,
    or_high: float,
    or_low: float,
    now: datetime | None = None,
) -> OrConfirmResult:
    """
    Long MIS rule after 9:45:
    - Observe until OR window ends
    - Confirmed if LTP >= entry AND LTP >= OR high (breakout)
    - Cautious if above entry but below OR high
    """
    now = now or datetime.now(IST)
    if now.weekday() >= 5:
        return OrConfirmResult(
            "observe", "Weekend", "⚪", "Market closed.", False,
        )
    if ltp is None or ltp <= 0:
        return OrConfirmResult(
            "wait", "No LTP", "⚪", "Live price unavailable.", False,
        )
    if not _past_or_window(now):
        return OrConfirmResult(
            "observe",
            "Observe OR",
            "🟡",
            f"Wait until 9:45 — note OR High ₹{or_high:,.0f} · OR Low ₹{or_low:,.0f}.",
            False,
        )
    if ltp < or_low:
        return OrConfirmResult(
            "invalid",
            "Below OR low",
            "🔴",
            f"LTP ₹{ltp:,.2f} below OR low ₹{or_low:,.0f} — skip long.",
            False,
        )
    if ltp >= entry and ltp >= or_high:
        return OrConfirmResult(
            "confirmed",
            "OR breakout confirmed",
            "🟢",
            f"LTP ₹{ltp:,.2f} ≥ entry ₹{entry:,.0f} and OR high ₹{or_high:,.0f}.",
            True,
        )
    if ltp >= entry:
        return OrConfirmResult(
            "wait",
            "Above entry, below OR high",
            "🟡",
            f"LTP ₹{ltp:,.2f} ≥ entry but below OR high ₹{or_high:,.0f} — wait for breakout.",
            False,
        )
    return OrConfirmResult(
        "wait",
        "Below entry",
        "⚪",
        f"LTP ₹{ltp:,.2f} below entry ₹{entry:,.0f}.",
        False,
    )


def fetch_symbol_opening_range(
    symbol: str,
    *,
    market: str = "india",
) -> tuple[float, float] | None:
    """First 15-min OR from 5m session bars."""
    from analyzer.intraday_signals import _opening_range
    from analyzer.providers import fetch_intraday_bars

    try:
        df, _ = fetch_intraday_bars(symbol, interval="5m", market=market)
        if df is None or df.empty or len(df) < 3:
            return None
        return _opening_range(df)
    except Exception:
        return None
