"""Resolve Market Pulse data for intraday watchlist without visiting Pulse tab."""

from __future__ import annotations

from analyzer.market_pulse_scan import CACHE_TTL, run_market_pulse_scan
from analyzer.pulse_cache import load_pulse_cache_with_stale

DEFAULT_INTRADAY_PULSE_PERIOD = "1y"


def pulse_cache_key(period: str, market: str) -> str:
    return f"pulse_{period}_{market}"


def load_pulse_for_watchlist(
    market: str,
    period: str = DEFAULT_INTRADAY_PULSE_PERIOD,
    *,
    session_report=None,
) -> tuple[object | None, str]:
    """
    Return (report, status) for watchlist building.
    status: session | cache_fresh | cache_stale | missing
    """
    if session_report is not None and getattr(session_report, "stock_map", None):
        return session_report, "session"

    cached, fresh = load_pulse_cache_with_stale(pulse_cache_key(period, market), CACHE_TTL)
    if cached is not None and getattr(cached, "stock_map", None):
        return cached, "cache_fresh" if fresh else "cache_stale"
    return None, "missing"


def run_quick_watchlist_scan(
    market: str,
    period: str = DEFAULT_INTRADAY_PULSE_PERIOD,
    *,
    use_cache: bool = True,
):
    """Full Nifty 50 scan for intraday watchlist (1–2 min without cache)."""
    return run_market_pulse_scan(period, market, use_cache=use_cache)
