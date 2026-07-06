"""WhatsApp share links — reuses MIS prep text (no API key required)."""

from __future__ import annotations

import urllib.parse

from analyzer.market_session import market_session_status
from analyzer.watchlist_pins import load_pinned_plans
from analyzer.watchlist_telegram import format_combined_prep_telegram


def whatsapp_share_url(text: str) -> str:
    """Open WhatsApp with pre-filled message (user taps Send)."""
    clean = text.strip()[:2000]
    return f"https://wa.me/?text={urllib.parse.quote(clean)}"


def format_mis_prep_whatsapp(
    *,
    options_picks: list | None = None,
    market_bias: str = "",
) -> str:
    """Plain-text MIS prep for WhatsApp (derived from Telegram formatter)."""
    prep_date = market_session_status().get("date", "")
    msg = format_combined_prep_telegram(
        load_pinned_plans(),
        options_picks or [],
        market_bias=market_bias,
        prep_date=prep_date,
    )
    return msg.replace("*", "").replace("_", "")


def mis_prep_whatsapp_url(
    *,
    options_picks: list | None = None,
    market_bias: str = "",
) -> str:
    return whatsapp_share_url(
        format_mis_prep_whatsapp(options_picks=options_picks, market_bias=market_bias)
    )
