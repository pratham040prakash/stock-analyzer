"""Sector concentration checks for intraday watchlist."""

from __future__ import annotations

from collections import Counter


def sector_concentration_warning(
    picks: list,
    *,
    threshold: int = 4,
) -> str | None:
    """
    Warn when too many picks share the same sector (default 4 of 5).
    `picks` items need `.sector` attribute.
    """
    if not picks or threshold < 2:
        return None
    sectors = [getattr(p, "sector", "").strip() for p in picks if getattr(p, "sector", "")]
    if not sectors:
        return None
    sector, count = Counter(sectors).most_common(1)[0]
    if count >= threshold and count >= len(picks) - 1:
        return (
            f"**{count}/{len(picks)}** picks are **{sector}** — "
            "high correlation; prefer **max 2** from the same sector."
        )
    if count >= threshold:
        return (
            f"**{count}/{len(picks)}** picks are **{sector}** — "
            "consider diversifying which 2 you trade."
        )
    return None
