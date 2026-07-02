"""Live LTP vs written entry/stop/target plan."""

from __future__ import annotations

from dataclasses import dataclass

NEAR_PCT = 0.35  # % of price — within this band = "near" a level


@dataclass
class LivePlanStatus:
    symbol: str
    ltp: float | None
    entry: float
    stop_loss: float
    target: float
    label: str
    emoji: str
    detail: str


def _near(ltp: float, level: float) -> bool:
    if level <= 0:
        return False
    return abs(ltp - level) / level * 100 <= NEAR_PCT


def assess_live_plan(
    ltp: float | None,
    *,
    entry: float,
    stop_loss: float,
    target: float,
    symbol: str = "",
) -> LivePlanStatus:
    """Long-biased MIS plan status vs current LTP."""
    sym = symbol or "—"
    if ltp is None or ltp <= 0:
        return LivePlanStatus(
            sym, None, entry, stop_loss, target,
            "LTP unavailable", "⚪", "Refresh or connect Kite for live price.",
        )

    if ltp <= stop_loss:
        return LivePlanStatus(
            sym, ltp, entry, stop_loss, target,
            "At/below stop", "🔴", f"LTP ₹{ltp:,.2f} — stop ₹{stop_loss:,.2f}. Do not add.",
        )
    if _near(ltp, stop_loss):
        return LivePlanStatus(
            sym, ltp, entry, stop_loss, target,
            "Near stop", "🟠", f"LTP ₹{ltp:,.2f} approaching stop ₹{stop_loss:,.2f}.",
        )
    if ltp >= target:
        return LivePlanStatus(
            sym, ltp, entry, stop_loss, target,
            "At/above target", "🟢", f"LTP ₹{ltp:,.2f} — target ₹{target:,.2f}. Book per plan.",
        )
    if _near(ltp, target):
        return LivePlanStatus(
            sym, ltp, entry, stop_loss, target,
            "Near target", "🟢", f"LTP ₹{ltp:,.2f} approaching target ₹{target:,.2f}.",
        )
    if ltp < entry:
        if _near(ltp, entry):
            return LivePlanStatus(
                sym, ltp, entry, stop_loss, target,
                "Near entry", "🟡", f"LTP ₹{ltp:,.2f} — watch for entry ₹{entry:,.2f}.",
            )
        return LivePlanStatus(
            sym, ltp, entry, stop_loss, target,
            "Below entry", "⚪", f"Wait — LTP ₹{ltp:,.2f} below entry ₹{entry:,.2f}.",
        )
    if _near(ltp, entry):
        return LivePlanStatus(
            sym, ltp, entry, stop_loss, target,
            "At entry", "🟡", f"LTP ₹{ltp:,.2f} at entry zone ₹{entry:,.2f}.",
        )
    return LivePlanStatus(
        sym, ltp, entry, stop_loss, target,
        "In trade zone", "🔵", f"LTP ₹{ltp:,.2f} between entry ₹{entry:,.2f} and target ₹{target:,.2f}.",
    )
