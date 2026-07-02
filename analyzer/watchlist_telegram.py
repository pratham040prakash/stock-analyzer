"""Telegram formatting for pinned / watchlist picks."""

from __future__ import annotations

from analyzer.watchlist_pins import PinnedPlan


def format_pinned_watchlist_telegram(
    picks: list[PinnedPlan],
    *,
    market_bias: str = "",
    prep_date: str = "",
) -> str:
    if not picks:
        return "*Watchlist* — no picks pinned yet."

    lines = ["*🌙 My MIS picks — tomorrow*"]
    if prep_date:
        lines.append(f"Prep date: {prep_date}")
    if market_bias:
        lines.append(f"Bias: *{market_bias}*")
    lines.append("")

    for i, p in enumerate(picks, start=1):
        lines.append(
            f"*{i}. {p.symbol}*\n"
            f"Entry ₹{p.entry:,.0f} · Stop ₹{p.stop_loss:,.0f} · Target ₹{p.target:,.0f}"
        )

    lines.append("")
    lines.append("_Trade only these. Stop on Kite first. Not financial advice._")
    return "\n".join(lines)
