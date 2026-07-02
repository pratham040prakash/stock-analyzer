"""Aggregate suggestion outcomes — daily learning insights."""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.suggestion_journal import SuggestionRecord, fetch_suggestions, init_journal


@dataclass
class PerformanceSlice:
    label: str
    total: int
    scored: int
    wins: int
    losses: int
    win_rate_pct: float
    avg_return_1d: float | None
    avg_alpha_1d: float | None


@dataclass
class LearningReport:
    total_suggestions: int
    validated_count: int
    pending_count: int
    overall_win_rate_pct: float
    slices: list[PerformanceSlice] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    recent_validated: list[SuggestionRecord] = field(default_factory=list)


def _slice_stats(records: list[SuggestionRecord], label: str) -> PerformanceSlice:
    scored = [r for r in records if r.outcome_correct in (0, 1)]
    wins = sum(1 for r in scored if r.outcome_correct == 1)
    losses = sum(1 for r in scored if r.outcome_correct == 0)
    r1_vals = [r.outcome_return_1d for r in scored if r.outcome_return_1d is not None]
    alpha_vals = [r.outcome_nifty_alpha_1d for r in scored if r.outcome_nifty_alpha_1d is not None]
    win_rate = round(wins / len(scored) * 100, 1) if scored else 0.0
    return PerformanceSlice(
        label=label,
        total=len(records),
        scored=len(scored),
        wins=wins,
        losses=losses,
        win_rate_pct=win_rate,
        avg_return_1d=round(sum(r1_vals) / len(r1_vals), 2) if r1_vals else None,
        avg_alpha_1d=round(sum(alpha_vals) / len(alpha_vals), 2) if alpha_vals else None,
    )


def build_learning_report(limit: int = 500) -> LearningReport:
    init_journal()
    all_rows = fetch_suggestions(limit=limit)
    validated = [r for r in all_rows if r.validated]
    pending = [r for r in all_rows if not r.validated]

    scored = [r for r in validated if r.outcome_correct in (0, 1)]
    wins = sum(1 for r in scored if r.outcome_correct == 1)
    overall_wr = round(wins / len(scored) * 100, 1) if scored else 0.0

    slices: list[PerformanceSlice] = []
    for source in ("market_pulse", "daily_advisor"):
        subset = [r for r in validated if r.source == source]
        if subset:
            slices.append(_slice_stats(subset, source.replace("_", " ").title()))

    for horizon in ("intraday", "short", "long", "holding"):
        subset = [r for r in validated if r.horizon == horizon]
        if subset:
            slices.append(_slice_stats(subset, f"Horizon: {horizon}"))

    insights = _generate_insights(slices, overall_wr, len(scored))

    return LearningReport(
        total_suggestions=len(all_rows),
        validated_count=len(validated),
        pending_count=len(pending),
        overall_win_rate_pct=overall_wr,
        slices=slices,
        insights=insights,
        recent_validated=validated[:30],
    )


def _generate_insights(slices: list[PerformanceSlice], overall_wr: float, scored_n: int) -> list[str]:
    insights: list[str] = []

    if scored_n < 10:
        insights.append(
            "Collecting data — need **10+ validated suggestions** before calibration. "
            "Run Market Pulse and Daily Advisor daily; validate after close."
        )
        return insights

    if overall_wr >= 55:
        insights.append(f"Overall direction accuracy **{overall_wr:.0f}%** — above random; keep logging picks.")
    elif overall_wr < 45:
        insights.append(
            f"Overall accuracy **{overall_wr:.0f}%** — below target. "
            "Raise buy thresholds or wait for stronger confluence before acting."
        )
    else:
        insights.append(f"Overall accuracy **{overall_wr:.0f}%** — near coin-flip; focus on high-score picks only.")

    by_horizon = {s.label: s for s in slices if s.label.startswith("Horizon:")}
    intra = by_horizon.get("Horizon: intraday")
    short = by_horizon.get("Horizon: short")
    if intra and short and intra.scored >= 5 and short.scored >= 5:
        if intra.win_rate_pct < short.win_rate_pct - 10:
            insights.append(
                f"Intraday ({intra.win_rate_pct:.0f}% win) lags swing ({short.win_rate_pct:.0f}% win) — "
                "prefer daily-chart picks over MIS unless score ≥ 40."
            )
        elif intra.win_rate_pct > short.win_rate_pct + 10:
            insights.append(
                f"Intraday picks outperforming swing — session momentum regime may favor MIS setups."
            )

    pulse = next((s for s in slices if s.label == "Market Pulse"), None)
    advisor = next((s for s in slices if s.label == "Daily Advisor"), None)
    if pulse and advisor and pulse.scored >= 5 and advisor.scored >= 5:
        better = "Market Pulse" if pulse.win_rate_pct >= advisor.win_rate_pct else "Daily Advisor"
        insights.append(
            f"**{better}** has higher hit rate this period — weight that source for tomorrow's actions."
        )

    insights.append(
        "Re-run validation daily after 3:30 PM IST: `python scripts/validate_suggestions.py`"
    )
    return insights
