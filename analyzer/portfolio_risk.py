"""Portfolio-level risk: concentration, sector weights, beta vs Nifty."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from analyzer.data import fetch_stock_data
from analyzer.portfolio import PortfolioRow


@dataclass
class HoldingWeight:
    kite_symbol: str
    name: str
    value: float
    weight_pct: float
    sector: str


@dataclass
class PortfolioRiskSummary:
    total_value: float
    holdings_count: int
    top5_concentration_pct: float
    largest_holding: str
    sector_weights: dict[str, float]
    portfolio_beta: float | None
    beta_note: str
    warnings: list[str] = field(default_factory=list)


def _holding_value(row: PortfolioRow) -> float:
    price = row.last_price or 0.0
    return max(0.0, price * row.quantity)


def compute_portfolio_risk(
    rows: list[PortfolioRow],
    period: str = "6mo",
) -> PortfolioRiskSummary:
    """Compute concentration, sector allocation, and beta vs Nifty."""
    valid = [r for r in rows if not r.error and r.quantity > 0]
    warnings: list[str] = []

    if not valid:
        return PortfolioRiskSummary(
            total_value=0.0,
            holdings_count=0,
            top5_concentration_pct=0.0,
            largest_holding="—",
            sector_weights={},
            portfolio_beta=None,
            beta_note="No holdings to analyze",
            warnings=["Import holdings first"],
        )

    weights: list[HoldingWeight] = []
    sector_map: dict[str, float] = {}

    for r in valid:
        val = _holding_value(r)
        sector = "Unknown"
        try:
            _, info = fetch_stock_data(r.yahoo_symbol, period="3mo", market="india", enrich_nse=False)
            sector = info.get("sector") or "Unknown"
        except Exception:
            warnings.append(f"Could not fetch sector for {r.kite_symbol}")
        weights.append(HoldingWeight(
            kite_symbol=r.kite_symbol,
            name=r.name,
            value=val,
            weight_pct=0.0,
            sector=sector,
        ))

    total = sum(w.value for w in weights) or 1.0
    for w in weights:
        w.weight_pct = round(w.value / total * 100, 2)
        sector_map[w.sector] = sector_map.get(w.sector, 0.0) + w.weight_pct

    weights.sort(key=lambda w: -w.weight_pct)
    top5 = sum(w.weight_pct for w in weights[:5])
    largest = weights[0].kite_symbol if weights else "—"

    if top5 > 60:
        warnings.append(f"High concentration: top 5 holdings = {top5:.0f}% of portfolio")
    if sector_map.get("Unknown", 0) > 30:
        warnings.append("Many holdings missing sector data")

    beta, beta_note = _portfolio_beta(valid, period)

    return PortfolioRiskSummary(
        total_value=round(total, 2),
        holdings_count=len(valid),
        top5_concentration_pct=round(top5, 1),
        largest_holding=largest,
        sector_weights=dict(sorted(sector_map.items(), key=lambda x: -x[1])),
        portfolio_beta=beta,
        beta_note=beta_note,
        warnings=warnings,
    )


def _portfolio_beta(rows: list[PortfolioRow], period: str) -> tuple[float | None, str]:
    try:
        nifty_df, _ = fetch_stock_data("^NSEI", period=period, market="india")
        nifty_ret = nifty_df["Close"].pct_change().dropna()
        nifty_ret.index = pd.DatetimeIndex([pd.Timestamp(t).date() for t in nifty_ret.index])

        betas: list[float] = []
        weights: list[float] = []

        for r in rows:
            val = _holding_value(r)
            if val <= 0:
                continue
            try:
                df, _ = fetch_stock_data(r.yahoo_symbol, period=period, market="india", enrich_nse=False)
                s_ret = df["Close"].pct_change().dropna()
                s_ret.index = pd.DatetimeIndex([pd.Timestamp(t).date() for t in s_ret.index])
                aligned = pd.DataFrame({"s": s_ret, "n": nifty_ret}).dropna()
                if len(aligned) < 20:
                    continue
                var_n = float(aligned["n"].var())
                if var_n < 1e-12:
                    continue
                beta = float(aligned["s"].cov(aligned["n"]) / var_n)
                betas.append(beta)
                weights.append(val)
            except Exception:
                continue

        if not betas:
            return None, "Could not compute stock betas vs Nifty"

        wbeta = float(np.average(betas, weights=weights))
        note = "β > 1 = more volatile than Nifty" if wbeta > 1.05 else (
            "β < 1 = defensive vs Nifty" if wbeta < 0.95 else "Near-market beta"
        )
        return round(wbeta, 2), note
    except Exception as exc:
        return None, f"Beta calc failed: {exc}"
