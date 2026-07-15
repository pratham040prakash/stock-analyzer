"""Combined technical + fundamental analysis."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.fundamentals import FundamentalResult, analyze_fundamentals
from analyzer.signals import AnalysisResult, analyze


@dataclass
class CombinedResult:
    ticker: str
    technical: AnalysisResult
    fundamental: FundamentalResult
    combined_score: float
    combined_recommendation: str
    technical_weight: float = 0.55
    fundamental_weight: float = 0.45


def _score_to_rec(score: float) -> str:
    if score >= 40:
        return "STRONG BUY"
    if score >= 15:
        return "BUY"
    if score <= -40:
        return "STRONG SELL"
    if score <= -15:
        return "SELL"
    return "HOLD"


def analyze_combined(
    df,
    ticker: str,
    yf_info: dict | None = None,
    tech_weight: float = 0.55,
    fund_weight: float = 0.45,
) -> CombinedResult:
    """Run technical and fundamental analysis and merge scores."""
    technical = analyze(df, ticker)
    fundamental = analyze_fundamentals(ticker, yf_info)

    combined = technical.composite_score * tech_weight + fundamental.composite_score * fund_weight
    result = CombinedResult(
        ticker=ticker,
        technical=technical,
        fundamental=fundamental,
        combined_score=round(combined, 1),
        combined_recommendation="HOLD",
        technical_weight=tech_weight,
        fundamental_weight=fund_weight,
    )
    from analyzer.decision_engine.verdict_bridge import attach_decision_to_combined

    attach_decision_to_combined(result)
    return result
