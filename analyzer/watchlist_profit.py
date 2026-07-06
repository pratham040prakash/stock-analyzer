"""Expected profit helpers for watchlist and options tables."""

from __future__ import annotations


def equity_target_profit_one_share(
    entry: float,
    target: float,
    *,
    side: str | None = None,
) -> float | None:
    """Profit in ₹ if 1 share hits target (long or short MIS)."""
    if entry <= 0:
        return None
    if side == "SHORT" or (side is None and target < entry):
        if target < entry:
            return round(entry - target, 2)
        return None
    if target > entry:
        return round(target - entry, 2)
    return None


def options_target_profit_one_lot(
    entry_premium: float | None,
    target_premium: float | None,
    lot_size: int,
) -> float | None:
    """Profit in ₹ if 1 lot hits target premium."""
    if (
        entry_premium is not None
        and target_premium is not None
        and entry_premium > 0
        and target_premium > entry_premium
        and lot_size > 0
    ):
        return round((target_premium - entry_premium) * lot_size, 2)
    return None


def format_expected_profit(amount: float | None) -> str:
    if amount is None:
        return "—"
    return f"₹{amount:,.2f}"
