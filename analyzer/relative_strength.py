"""Relative strength — stock performance vs benchmark index."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

BENCHMARKS = {
    "india": "^NSEI",
    "us": "^GSPC",
}


@dataclass
class PeriodRS:
    label: str
    stock_return_pct: float
    benchmark_return_pct: float
    alpha_pct: float  # stock - benchmark


@dataclass
class RelativeStrengthResult:
    benchmark_symbol: str
    benchmark_name: str
    periods: list[PeriodRS] = field(default_factory=list)
    verdict: str = "Inline"  # Outperforming | Underperforming | Inline


def _return_pct(series: pd.Series, days: int) -> float | None:
    if len(series) <= days:
        return None
    start = float(series.iloc[-days - 1])
    end = float(series.iloc[-1])
    if start <= 0:
        return None
    return (end / start - 1) * 100


def compute_relative_strength(
    stock_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    benchmark_symbol: str = "^NSEI",
    benchmark_name: str = "Nifty 50",
) -> RelativeStrengthResult:
    """Compare stock returns vs benchmark over 1M, 3M, 6M."""
    stock_close = stock_df["Close"]
    bench_close = benchmark_df["Close"]

    # Align on common dates for fair comparison
    combined = pd.DataFrame({"stock": stock_close, "bench": bench_close}).dropna()
    if len(combined) < 22:
        return RelativeStrengthResult(benchmark_symbol=benchmark_symbol, benchmark_name=benchmark_name)

    stock_s = combined["stock"]
    bench_s = combined["bench"]

    period_defs = [("1 Month", 21), ("3 Months", 63), ("6 Months", 126)]
    periods: list[PeriodRS] = []
    alphas: list[float] = []

    for label, days in period_defs:
        sr = _return_pct(stock_s, days)
        br = _return_pct(bench_s, days)
        if sr is not None and br is not None:
            alpha = sr - br
            periods.append(PeriodRS(label, round(sr, 2), round(br, 2), round(alpha, 2)))
            alphas.append(alpha)

    if not alphas:
        verdict = "Inline"
    elif sum(alphas) / len(alphas) > 2:
        verdict = "Outperforming"
    elif sum(alphas) / len(alphas) < -2:
        verdict = "Underperforming"
    else:
        verdict = "Inline"

    return RelativeStrengthResult(
        benchmark_symbol=benchmark_symbol,
        benchmark_name=benchmark_name,
        periods=periods,
        verdict=verdict,
    )


def rs_chart(stock_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.DataFrame:
    """Normalized price series (100 = start) for overlay chart."""
    combined = pd.DataFrame(
        {"Stock": stock_df["Close"], "Benchmark": benchmark_df["Close"]}
    ).dropna()
    if combined.empty:
        return combined
    return (combined / combined.iloc[0] * 100).rename(
        columns={"Stock": "stock_norm", "Benchmark": "bench_norm"}
    )
