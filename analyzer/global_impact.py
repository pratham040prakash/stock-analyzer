"""Global → India spillover analysis and Nifty bias prediction."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from analyzer.global_markets import (
    EXTERNAL_SYMBOLS,
    WORLD_INDICES,
    GlobalMarketSnapshot,
    MarketQuote,
    fetch_daily_history,
    fetch_global_snapshot,
)

NIFTY = "^NSEI"
LOOKBACK_DAYS = 60


@dataclass
class CorrelationRow:
    market: str
    symbol: str
    correlation_60d: float
    beta_60d: float
    latest_1d_pct: float | None


@dataclass
class IndiaImpactReport:
    fetched_at: str
    global_snapshot: GlobalMarketSnapshot
    spillover_score: float  # -100 to +100
    predicted_nifty_bias: str  # BULLISH | BEARISH | NEUTRAL
    predicted_move_pct: float
    confidence: str
    india_action: str  # STRONG BUY bias | CAUTION | etc.
    ce_pe_hint: str
    drivers: list[str] = field(default_factory=list)
    correlations: list[CorrelationRow] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    narrative: str = ""


def _daily_returns(close: pd.Series) -> pd.Series:
    return close.pct_change().dropna()


def _to_date_index(series: pd.Series) -> pd.Series:
    """Align daily returns across exchanges (IST vs US/EU tz)."""
    out = series.copy()
    out.index = pd.DatetimeIndex([pd.Timestamp(ts).date() for ts in series.index])
    return out


def _corr_beta(nifty_ret: pd.Series, other_ret: pd.Series) -> tuple[float, float]:
    aligned = pd.DataFrame({"n": nifty_ret, "o": other_ret}).dropna()
    if len(aligned) < 20:
        return 0.0, 0.0
    corr = float(aligned["n"].corr(aligned["o"]))
    var_o = float(aligned["o"].var())
    beta = float(aligned["n"].cov(aligned["o"]) / var_o) if var_o > 1e-12 else 0.0
    return round(corr, 3), round(beta, 3)


def compute_correlations(nifty_df: pd.DataFrame) -> list[CorrelationRow]:
    nifty_ret = _to_date_index(_daily_returns(nifty_df["Close"]))
    rows: list[CorrelationRow] = []
    name_map = {s: n for s, n, _, _ in WORLD_INDICES}

    for sym in EXTERNAL_SYMBOLS:
        try:
            odf = fetch_daily_history(sym, "6mo")
            if odf.empty:
                continue
            o_ret = _to_date_index(_daily_returns(odf["Close"]))
            combined = pd.DataFrame({"n": nifty_ret, "o": o_ret}).dropna().tail(LOOKBACK_DAYS)
            if len(combined) < 20:
                continue
            corr, beta = _corr_beta(combined["n"], combined["o"])
            latest_1d = None
            if len(odf) >= 2:
                latest_1d = round(
                    (float(odf["Close"].iloc[-1]) / float(odf["Close"].iloc[-2]) - 1) * 100, 2
                )
            rows.append(CorrelationRow(
                market=name_map.get(sym, sym),
                symbol=sym,
                correlation_60d=corr,
                beta_60d=beta,
                latest_1d_pct=latest_1d,
            ))
        except Exception:
            continue

    rows.sort(key=lambda r: abs(r.correlation_60d), reverse=True)
    return rows


def _spillover_from_quotes(
    quotes: list[MarketQuote],
    correlations: list[CorrelationRow],
) -> tuple[float, list[str]]:
    """Weighted global move → implied Nifty pressure."""
    corr_map = {c.symbol: c for c in correlations}
    score = 0.0
    drivers: list[str] = []
    total_w = 0.0

    for q in quotes:
        if q.symbol in (NIFTY, "^NSEBANK", "^BSESN"):
            continue
        move = q.change_1d_pct
        if move is None:
            continue
        crow = corr_map.get(q.symbol)
        corr = crow.correlation_60d if crow else 0.3
        beta = crow.beta_60d if crow else 0.5
        # Weight by model weight × correlation strength
        w = q.weight * (0.5 + 0.5 * abs(corr))
        # Predicted nifty impact ≈ beta * move
        contrib = beta * move * w * 10
        score += contrib
        total_w += w
        if abs(move) >= 0.4 and abs(corr) >= 0.25:
            direction = "↑" if move > 0 else "↓"
            drivers.append(
                f"{q.name} {direction}{abs(move):.2f}% (corr {corr:+.2f}, β {beta:+.2f})"
            )

    if total_w > 0:
        score = score / total_w * 3
    return round(max(-100, min(100, score)), 1), drivers[:8]


def _predict_move(spillover: float, correlations: list[CorrelationRow]) -> float:
    """Estimate next Nifty session % from spillover score."""
    # Calibrate: score ±30 ≈ ±0.5% nifty typical spillover
    base = spillover / 60.0
    # US overnight dominant when available
    us = [c for c in correlations if c.symbol in ("^GSPC", "^IXIC") and c.latest_1d_pct is not None]
    if us:
        us_move = np.mean([c.latest_1d_pct for c in us])
        us_beta = np.mean([c.beta_60d for c in us])
        base = base * 0.5 + us_beta * us_move * 0.01 * 0.5
    return round(base, 2)


def _bias_from_score(score: float, move: float) -> tuple[str, str, str]:
    if score >= 25 or move >= 0.4:
        return "BULLISH", "Risk-on — global tailwind for Nifty", "Favour **CE** / add quality large-caps"
    if score <= -25 or move <= -0.4:
        return "BEARISH", "Risk-off — global headwind", "Favour **PE** / hedge · reduce beta"
    return "NEUTRAL", "Mixed global cues", "Wait for Nifty OR breakout · avoid aggressive options"


def _build_india_impact_report() -> IndiaImpactReport:
    snapshot = fetch_global_snapshot()
    nifty_q = next((q for q in snapshot.quotes if q.symbol == NIFTY), None)
    nifty_df = fetch_daily_history(NIFTY, "6mo")
    correlations = compute_correlations(nifty_df) if not nifty_df.empty else []

    spillover, drivers = _spillover_from_quotes(snapshot.quotes, correlations)
    predicted_move = _predict_move(spillover, correlations)
    bias, india_action, ce_pe = _bias_from_score(spillover, predicted_move)

    # Confidence from driver agreement
    pos = sum(1 for d in drivers if "↑" in d)
    neg = sum(1 for d in drivers if "↓" in d)
    if len(drivers) >= 3 and (pos >= 3 or neg >= 3):
        confidence = "high"
    elif len(drivers) >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    risks = [
        "Model uses 60-day correlation — regimes change after RBI/Fed events",
        "Yahoo data may lag 15–20 min; not tick-by-tick",
        "India decouples short-term — global signal is probability, not certainty",
    ]
    if nifty_q and nifty_q.change_1d_pct is not None:
        drivers.insert(0, f"Nifty today {nifty_q.change_1d_pct:+.2f}% (spot ₹{nifty_q.price:,.0f})")

    narrative = (
        f"Global spillover score **{spillover:+.0f}** → predicted Nifty move **{predicted_move:+.2f}%** "
        f"next session ({confidence} confidence). "
        f"When US/Europe/Asia rally together, Nifty often gaps up; sustained selling abroad "
        f"typically pressures FII flows and Bank Nifty."
    )

    return IndiaImpactReport(
        fetched_at=snapshot.fetched_at,
        global_snapshot=snapshot,
        spillover_score=spillover,
        predicted_nifty_bias=bias,
        predicted_move_pct=predicted_move,
        confidence=confidence,
        india_action=india_action,
        ce_pe_hint=ce_pe,
        drivers=drivers,
        correlations=correlations,
        risks=risks,
        narrative=narrative,
    )


def build_india_impact_report() -> IndiaImpactReport:
    from analyzer.cache_utils import cached_compute

    return cached_compute("global_impact_v1", 60, _build_india_impact_report)
