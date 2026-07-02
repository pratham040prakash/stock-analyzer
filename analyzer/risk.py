"""Position sizing and risk helpers."""

from __future__ import annotations


def suggest_position_size(
    capital: float,
    entry: float,
    stop: float,
    risk_pct: float = 1.0,
    max_single_pct: float = 8.0,
) -> dict:
    """
    Risk-based position size for Indian equities.
    risk_pct: max % of capital to risk on this trade (default 1%).
    """
    if capital <= 0 or entry <= 0 or stop <= 0 or entry == stop:
        return {"shares": 0, "value": 0.0, "risk_amount": 0.0, "note": "Invalid inputs"}

    risk_amount = capital * (risk_pct / 100)
    risk_per_share = abs(entry - stop)
    shares = int(risk_amount / risk_per_share)
    value = shares * entry
    max_value = capital * (max_single_pct / 100)
    if value > max_value:
        shares = int(max_value / entry)
        value = shares * entry

    return {
        "shares": shares,
        "value": round(value, 2),
        "risk_amount": round(risk_amount, 2),
        "note": f"Risk {risk_pct}% of ₹{capital:,.0f} · max {max_single_pct}% per stock",
    }


def capital_from_kite_margins(margins: dict | None) -> float | None:
    if not margins:
        return None
    try:
        avail = margins.get("available", {})
        cash = avail.get("cash") or avail.get("live_balance")
        return float(cash) if cash else None
    except (TypeError, ValueError):
        return None
