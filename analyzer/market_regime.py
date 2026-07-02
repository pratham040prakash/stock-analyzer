"""Nifty market regime — trending vs range-bound (ADX filter)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analyzer.data import _fetch_single
from analyzer.indicators import add_indicators
from analyzer.varsity_knowledge import ADX_TREND_THRESHOLD


@dataclass
class MarketRegime:
    symbol: str
    adx: float | None
    plus_di: float | None
    minus_di: float | None
    regime: str  # Trending Bullish | Trending Bearish | Range-bound | Unknown
    allow_aggressive_intraday: bool
    allow_aggressive_swing: bool
    message: str
    banner: str


def _adx_cols(df: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
    adx = dip = dim = None
    for col in df.columns:
        if col.startswith("ADX_"):
            adx = col
        elif col.startswith("DMP_"):
            dip = col
        elif col.startswith("DMN_"):
            dim = col
    return adx, dip, dim


def detect_nifty_regime(period: str = "6mo", symbol: str = "^NSEI") -> MarketRegime:
    """Classify Nifty regime using daily ADX (+DI / -DI). Varsity Ch 20."""
    try:
        df, _ = _fetch_single(symbol, period)
        df = add_indicators(df)
        row = df.iloc[-1]
        adx_col, dmp_col, dmn_col = _adx_cols(df)
        adx = float(row[adx_col]) if adx_col and not pd.isna(row.get(adx_col)) else None
        pdi = float(row[dmp_col]) if dmp_col and not pd.isna(row.get(dmp_col)) else None
        mdi = float(row[dmn_col]) if dmn_col and not pd.isna(row.get(dmn_col)) else None
    except Exception as exc:
        return MarketRegime(
            symbol=symbol,
            adx=None,
            plus_di=None,
            minus_di=None,
            regime="Unknown",
            allow_aggressive_intraday=True,
            allow_aggressive_swing=True,
            message=f"Regime unavailable: {exc}",
            banner="⚪ Market regime unknown — use normal discretion",
        )

    if adx is None:
        regime = "Unknown"
    elif adx < ADX_TREND_THRESHOLD:
        regime = "Range-bound"
    elif pdi and mdi and pdi > mdi:
        regime = "Trending Bullish"
    elif pdi and mdi and mdi > pdi:
        regime = "Trending Bearish"
    else:
        regime = "Neutral trend"

    range_bound = regime == "Range-bound"
    bear_trend = regime == "Trending Bearish"

    allow_intra = not range_bound and not bear_trend
    allow_swing = not range_bound or (adx is not None and adx >= 18)

    if range_bound:
        msg = (
            f"Nifty ADX {adx:.0f} < {ADX_TREND_THRESHOLD:.0f} — **range-bound** market. "
            "Favour mean-reversion; downgrade chase BUYs on breakouts."
        )
        banner = f"🟡 **Range-bound** (ADX {adx:.0f}) — cautious with intraday/swing BUYs"
    elif regime == "Trending Bullish":
        msg = f"Nifty ADX {adx:.0f}, +DI > -DI — trending up. Tailwind for longs."
        banner = f"🟢 **Trending bullish** (ADX {adx:.0f}) — favour BUY setups"
    elif regime == "Trending Bearish":
        msg = f"Nifty ADX {adx:.0f}, -DI > +DI — downtrend. Tight stops; avoid dip-buying."
        banner = f"🔴 **Trending bearish** (ADX {adx:.0f}) — favour defence / PE hedges"
    else:
        msg = f"Nifty ADX {adx:.0f} — mixed trend."
        banner = f"⚪ **Mixed trend** (ADX {adx:.0f}) — selective entries only"

    return MarketRegime(
        symbol=symbol,
        adx=round(adx, 1) if adx else None,
        plus_di=round(pdi, 1) if pdi else None,
        minus_di=round(mdi, 1) if mdi else None,
        regime=regime,
        allow_aggressive_intraday=allow_intra,
        allow_aggressive_swing=allow_swing,
        message=msg,
        banner=banner,
    )


def apply_regime_to_action(action: str, score: float, horizon: str, regime: MarketRegime) -> tuple[str, float, str]:
    """Downgrade aggressive BUYs in poor regimes. Returns (action, score, note)."""
    if action not in ("STRONG BUY", "BUY", "CORE BUY", "ACCUMULATE"):
        return action, score, ""

    if horizon == "intraday" and not regime.allow_aggressive_intraday:
        if action in ("STRONG BUY", "BUY"):
            return "WATCH", score * 0.6, f"Downgraded: {regime.regime} — wait for OR/VWAP confirmation"
    if horizon == "short" and not regime.allow_aggressive_swing:
        if action in ("STRONG BUY", "BUY"):
            return "WATCH", score * 0.7, f"Downgraded: {regime.regime} — swing edge weaker in chop"

    if regime.regime == "Trending Bearish" and horizon in ("intraday", "short"):
        if action == "STRONG BUY":
            return "BUY", score * 0.85, "Caution: Nifty bearish trend"

    return action, score, ""
