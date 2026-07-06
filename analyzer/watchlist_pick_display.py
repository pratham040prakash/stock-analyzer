"""Format watchlist pick rows for UI — why picked, rolling stats."""

from __future__ import annotations

from analyzer.intraday_watchlist import IntradayWatchlistPick
from analyzer.symbol_track_record import symbol_rolling_stats


def format_pick_why(p: IntradayWatchlistPick) -> str:
    """Compact reason string for table column."""
    parts: list[str] = []
    if p.confidence_pct is not None:
        parts.append(f"Conf {p.confidence_pct:.0f}%")
    if p.atr_pct is not None:
        parts.append(f"ATR {p.atr_pct:.1f}%")
    if p.volume_ratio is not None:
        parts.append(f"Vol {p.volume_ratio:.1f}×")
    if p.rsi is not None:
        parts.append(f"RSI {p.rsi:.0f}")
    if p.sector_tailwind:
        parts.append("Sector ✓")
    if p.macd_bullish:
        parts.append("MACD ✓")
    for note in (p.checklist.notes or [])[:2]:
        if note and note not in parts:
            parts.append(note[:24])
    return " · ".join(parts[:5]) if parts else f"Checks {p.checklist.passed}/{p.checklist.total}"


def format_pick_history(p: IntradayWatchlistPick, days: int = 30) -> str:
    stats = symbol_rolling_stats(p.nse_symbol, days=days)
    if stats["decided"] == 0:
        return "30d: —"
    return f"30d: {stats['label']}"
