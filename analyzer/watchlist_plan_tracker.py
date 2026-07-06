"""Live LTP vs written entry/stop/target plan (T1/T2/T3 ladder)."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.trade_ladder import (
    TradeLadder,
    assess_equity_ladder,
    assess_options_ladder,
    build_equity_ladder,
    build_options_ladder,
)

NEAR_PCT = 0.35  # kept for backward-compatible imports


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
    target2: float | None = None
    target3: float | None = None
    active_stop: float | None = None
    ladder_stage: int = 0
    ladder_note: str = ""


def equity_ladder_for_plan(
    entry: float,
    stop_loss: float,
    target: float,
    *,
    side: str = "LONG",
    pivot_r2: float | None = None,
) -> TradeLadder:
    return build_equity_ladder(side, entry, stop_loss, target, pivot_r2=pivot_r2)


def assess_live_plan(
    ltp: float | None,
    *,
    entry: float,
    stop_loss: float,
    target: float,
    symbol: str = "",
    side: str = "LONG",
    pivot_r2: float | None = None,
) -> LivePlanStatus:
    """Long-biased MIS plan status vs current LTP with T1/T2/T3 ladder."""
    ladder = build_equity_ladder(side, entry, stop_loss, target, pivot_r2=pivot_r2)
    status = assess_equity_ladder(ltp, ladder, symbol=symbol)
    return LivePlanStatus(
        symbol=status.symbol,
        ltp=status.ltp,
        entry=entry,
        stop_loss=stop_loss,
        target=target,
        label=status.label,
        emoji=status.emoji,
        detail=status.detail,
        target2=ladder.target2,
        target3=ladder.target3,
        active_stop=status.active_stop,
        ladder_stage=status.stage,
        ladder_note=status.ladder_note,
    )


def assess_options_live_plan(
    premium: float | None,
    *,
    entry: float,
    stop_loss: float,
    target: float,
    label: str = "",
) -> LivePlanStatus:
    if entry > 0 and target > entry:
        mults = (
            target / entry,
            max(target / entry + 0.5, 2.0),
            max(target / entry + 1.0, 2.5),
        )
        ladder = build_options_ladder(entry, target_mults=mults)
    else:
        ladder = build_options_ladder(entry)
    status = assess_options_ladder(premium, ladder, label=label)
    return LivePlanStatus(
        symbol=label,
        ltp=premium,
        entry=entry,
        stop_loss=stop_loss,
        target=target,
        label=status.label,
        emoji=status.emoji,
        detail=status.detail,
        target2=ladder.target2,
        target3=ladder.target3,
        active_stop=status.active_stop,
        ladder_stage=status.stage,
        ladder_note=status.ladder_note,
    )
