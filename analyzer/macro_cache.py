"""Daily-cached India macro summary for Alpha AI (avoid per-ticker global fetches)."""

from __future__ import annotations

from analyzer.cache_utils import cached_compute
from analyzer.global_impact import IndiaImpactReport, build_india_impact_report

_DAILY_TTL = 86400  # 24 hours


def get_daily_india_macro() -> IndiaImpactReport:
    """One global impact report per day — shared across all Alpha AI runs."""
    return cached_compute("india_macro_daily_v1", _DAILY_TTL, build_india_impact_report)


def format_macro_summary(report: IndiaImpactReport) -> str:
    return (
        f"**Nifty bias (model):** {report.predicted_nifty_bias} · "
        f"**Spillover:** {report.spillover_score:+.0f} · "
        f"**Predicted move:** {report.predicted_move_pct:+.2f}% · "
        f"**Confidence:** {report.confidence}\n\n"
        f"{report.narrative[:400]}"
    )
