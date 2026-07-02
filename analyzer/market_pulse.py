"""Market-wide pulse — index signals and regime detection."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analyzer.data import _fetch_single
from analyzer.india import INDIAN_INDICES
from analyzer.indicators import add_indicators
from analyzer.signals import analyze


@dataclass
class IndexPulse:
    symbol: str
    name: str
    price: float
    change_1m_pct: float | None
    recommendation: str
    score: float
    regime: str  # Bullish | Bearish | Neutral


def _change_pct(df: pd.DataFrame, days: int = 21) -> float | None:
    if len(df) <= days:
        return None
    start = float(df["Close"].iloc[-days - 1])
    end = float(df["Close"].iloc[-1])
    return round((end / start - 1) * 100, 2)


def analyze_index(symbol: str, name: str, period: str = "6mo") -> IndexPulse:
    df, _ = _fetch_single(symbol, period)
    df = add_indicators(df)
    result = analyze(df, symbol)
    score = result.composite_score
    if score >= 20:
        regime = "Bullish"
    elif score <= -20:
        regime = "Bearish"
    else:
        regime = "Neutral"
    return IndexPulse(
        symbol=symbol,
        name=name,
        price=float(df["Close"].iloc[-1]),
        change_1m_pct=_change_pct(df),
        recommendation=result.recommendation,
        score=score,
        regime=regime,
    )


def india_market_pulse(period: str = "6mo") -> list[IndexPulse]:
    """Analyze key Indian indices."""
    indices = [
        (v["symbol"], v["name"]) for v in INDIAN_INDICES.values()
        if v["symbol"] in ("^NSEI", "^NSEBANK", "^BSESN", "^CNXIT")
    ]
    pulses: list[IndexPulse] = []
    for sym, name in indices:
        for try_period in (period, "3mo", "1mo"):
            try:
                pulses.append(analyze_index(sym, name, try_period))
                break
            except Exception:
                continue
    return pulses


def overall_market_verdict(pulses: list[IndexPulse]) -> str:
    if not pulses:
        return "Unable to assess market"
    avg = sum(p.score for p in pulses) / len(pulses)
    if avg >= 15:
        return "Market bias: **Bullish** — favour stock picking, trail stop-losses"
    if avg <= -15:
        return "Market bias: **Bearish** — be cautious, avoid aggressive buying"
    return "Market bias: **Neutral** — selective stock picking, wait for clear signals"
