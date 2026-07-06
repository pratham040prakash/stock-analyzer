"""Monte Carlo scenario targets from historical return distribution."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ScenarioCase:
    name: str
    description: str
    probability_pct: float | None
    target_price: str = ""
    expected_cagr: str = ""


def _fmt(val: float, currency: str) -> str:
    return f"{currency}{val:,.2f}"


def monte_carlo_scenarios(
    df: pd.DataFrame,
    current_price: float,
    currency: str,
    *,
    horizon_days: int = 252,
    simulations: int = 2000,
    earnings_growth: float | None = None,
) -> list[ScenarioCase]:
    """
    GBM-style simulation from historical daily log returns.
    Bull/Base/Bear = 75th / 50th / 25th percentile of simulated 1Y prices.
    """
    if df is None or df.empty or current_price <= 0:
        return []

    rets = np.log(df["Close"] / df["Close"].shift(1)).dropna()
    if len(rets) < 60:
        return []

    mu = float(rets.mean())
    sigma = float(rets.std())
    if sigma < 1e-8:
        sigma = 0.015

    rng = np.random.default_rng(42)
    shocks = rng.normal(mu, sigma, size=(simulations, horizon_days))
    paths = current_price * np.exp(np.cumsum(shocks, axis=1))
    terminal = paths[:, -1]

    p75, p50, p25 = np.percentile(terminal, [75, 50, 25])
    eg = earnings_growth
    cagr_bull = f"{eg * 100 * 1.15:+.0f}% (ESTIMATE)" if eg is not None else "MC p75 path"
    cagr_base = f"{eg * 100:+.0f}% (ESTIMATE)" if eg is not None else "MC median path"
    cagr_bear = "MC p25 path — downside stress"

    return [
        ScenarioCase(
            "Bull",
            f"Monte Carlo p75 after {horizon_days}d ({simulations} sims, σ={sigma:.2%}/day)",
            25.0,
            _fmt(float(p75), currency),
            cagr_bull,
        ),
        ScenarioCase(
            "Base",
            f"Monte Carlo median after {horizon_days}d",
            50.0,
            _fmt(float(p50), currency),
            cagr_base,
        ),
        ScenarioCase(
            "Bear",
            f"Monte Carlo p25 after {horizon_days}d",
            25.0,
            _fmt(float(p25), currency),
            cagr_bear,
        ),
    ]
