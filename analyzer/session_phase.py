"""UI session phase — pre-market, live, after-hours."""

from __future__ import annotations

from analyzer.market_session import market_session_status
from analyzer.watchlist_history import can_score_trade_date, session_target_date


def suggestions_ui_phase() -> str:
    """
    Phase for Suggestions home layout.
    pre_market | live | post_close | weekend
    """
    session = market_session_status()
    phase = session.get("phase", "")
    if phase == "open":
        return "live"
    if phase in ("weekend", "holiday"):
        return "weekend"
    if phase == "pre_market":
        return "pre_market"
    if phase == "after_hours" and can_score_trade_date(session_target_date()):
        return "post_close"
    return "pre_market"


def phase_banner_text(phase: str) -> str:
    messages = {
        "live": "**Live session** — trade your starred picks. OR and ladder refresh below.",
        "post_close": "**After close** — score today's picks, then **Quick scan** for tomorrow.",
        "pre_market": "**Pre-market** — review today's list. Opens **9:15 AM IST**.",
        "weekend": "**Market closed** — review track record or prep for the next session.",
    }
    return messages.get(phase, "")
