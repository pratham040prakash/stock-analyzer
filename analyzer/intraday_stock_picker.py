"""
Investopedia-style intraday stock screening.

Liquidity, volatility (sweet spot), Nifty correlation, relative volume, and TA alignment.
https://www.investopedia.com/day-trading/pick-stocks-intraday-trading/
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# Investopedia / India large-cap intraday bars
MIN_AVG_DAILY_VOLUME = 500_000  # ~5 lakh shares
IDEAL_RANGE_MIN_PCT = 2.0
IDEAL_RANGE_MAX_PCT = 5.0
MAX_RANGE_PCT = 8.0
CORRELATION_LOOKBACK = 20
REL_VOLUME_BOOST = 1.5


@dataclass
class IntradayScreenResult:
    nse_symbol: str
    liquidity_score: float
    volatility_score: float
    correlation_score: float
    volume_score: float
    composite_score: float
    passed_liquidity: bool
    passed_volatility: bool
    avg_daily_volume: float | None
    daily_range_pct: float | None
    relative_volume: float | None
    nifty_correlation: float | None
    notes: list[str] = field(default_factory=list)


def rolling_nifty_correlation(
    stock_df: pd.DataFrame,
    nifty_df: pd.DataFrame,
    lookback: int = CORRELATION_LOOKBACK,
) -> float | None:
    """Pearson correlation of daily returns vs Nifty over lookback."""
    if stock_df is None or nifty_df is None or len(stock_df) < lookback + 2:
        return None
    s = stock_df[["Close"]].rename(columns={"Close": "stock"})
    b = nifty_df[["Close"]].rename(columns={"Close": "nifty"})
    merged = s.join(b, how="inner")
    if len(merged) < lookback:
        return None
    rets = merged.pct_change().dropna().tail(lookback)
    if len(rets) < 10:
        return None
    corr = rets["stock"].corr(rets["nifty"])
    if corr is None or pd.isna(corr):
        return None
    return round(float(corr), 3)


def _avg_daily_volume(df: pd.DataFrame, bars: int = 20) -> float | None:
    if df is None or len(df) < bars:
        return None
    vol = float(df["Volume"].tail(bars).mean())
    return vol if vol > 0 else None


def _daily_range_pct(df: pd.DataFrame, bars: int = 14) -> float | None:
    if df is None or len(df) < bars:
        return None
    tail = df.tail(bars)
    ranges = (tail["High"] - tail["Low"]) / tail["Close"].replace(0, pd.NA) * 100
    val = float(ranges.mean())
    return val if not pd.isna(val) else None


def _session_range_pct(intraday_df: pd.DataFrame | None) -> float | None:
    if intraday_df is None or len(intraday_df) < 3:
        return None
    hi = float(intraday_df["High"].max())
    lo = float(intraday_df["Low"].min())
    last = float(intraday_df["Close"].iloc[-1])
    if last <= 0:
        return None
    return round((hi - lo) / last * 100, 2)


def score_liquidity(
    avg_volume: float | None,
    relative_volume: float | None,
) -> tuple[float, bool, list[str]]:
    """0–40 pts. Investopedia: high volume = easy entry/exit."""
    notes: list[str] = []
    if avg_volume is None:
        notes.append("Volume data limited — assume Nifty 50 liquidity")
        return 22.0, True, notes

    if avg_volume >= 2_000_000:
        notes.append(f"Very liquid — ~{avg_volume/1e6:.1f}M shares/day")
        return 40.0, True, notes
    if avg_volume >= MIN_AVG_DAILY_VOLUME:
        notes.append(f"Liquid — ~{avg_volume/1e5:.1f}L shares/day (≥5L rule)")
        score = 32.0
        if relative_volume and relative_volume >= REL_VOLUME_BOOST:
            notes.append(f"Relative volume **{relative_volume:.1f}×** — unusual interest")
            score = min(40.0, score + 6.0)
        return score, True, notes
    if avg_volume >= 200_000:
        notes.append(f"Moderate liquidity — ~{avg_volume/1e5:.1f}L shares/day")
        return 18.0, True, notes

    notes.append(f"Low liquidity — ~{avg_volume:,.0f} shares/day; skip for MIS")
    return 5.0, False, notes


def score_volatility(
    daily_range_pct: float | None,
    session_range_pct: float | None,
) -> tuple[float, bool, list[str]]:
    """0–30 pts. Sweet spot 2–5% daily range; avoid dead or extreme names."""
    notes: list[str] = []
    range_pct = session_range_pct if session_range_pct is not None else daily_range_pct
    if range_pct is None:
        notes.append("Volatility unknown — use chart levels")
        return 15.0, True, notes

    if range_pct > MAX_RANGE_PCT:
        notes.append(f"Too volatile — {range_pct:.1f}% range (cap {MAX_RANGE_PCT:.0f}%)")
        return 5.0, False, notes
    if range_pct < 1.0:
        notes.append(f"Low movement — {range_pct:.1f}% range; hard to scalp")
        return 10.0, True, notes
    if IDEAL_RANGE_MIN_PCT <= range_pct <= IDEAL_RANGE_MAX_PCT:
        notes.append(f"Ideal volatility — {range_pct:.1f}% intraday range")
        return 30.0, True, notes
    if range_pct < IDEAL_RANGE_MIN_PCT:
        notes.append(f"Moderate volatility — {range_pct:.1f}% range")
        return 20.0, True, notes
    notes.append(f"Elevated volatility — {range_pct:.1f}% range (manage size)")
    return 22.0, True, notes


def score_correlation(
    correlation: float | None,
    nifty_bias: str,
    trade_action: str,
) -> tuple[float, list[str]]:
    """0–20 pts. Trade with index when positively correlated (Investopedia rule #3)."""
    notes: list[str] = []
    if correlation is None:
        notes.append("Nifty correlation not computed")
        return 10.0, notes

    notes.append(f"Nifty correlation **{correlation:+.2f}** (20d)")
    bullish_market = nifty_bias.upper() in ("BULLISH", "STRONG BUY", "BUY", "RISK-ON")
    bearish_market = nifty_bias.upper() in ("BEARISH", "STRONG SELL", "SELL", "RISK-OFF")
    buy_setup = trade_action in ("STRONG BUY", "BUY")
    sell_setup = trade_action in ("STRONG SELL", "SELL")

    if correlation >= 0.5:
        if (bullish_market and buy_setup) or (bearish_market and sell_setup):
            notes.append("Moves with index — aligned with market trend")
            return 20.0, notes
        notes.append("High index correlation — confirm direction vs Nifty")
        return 14.0, notes
    if correlation >= 0.2:
        return 12.0, notes
    if correlation <= -0.3:
        notes.append("Inverse to Nifty — hedge/divergence play only")
        return 8.0, notes
    return 10.0, notes


def score_relative_volume(relative_volume: float | None) -> tuple[float, list[str]]:
    """0–10 pts. Investopedia: volume spike signals participation."""
    if relative_volume is None:
        return 5.0, []
    if relative_volume >= 2.0:
        return 10.0, [f"Volume surge **{relative_volume:.1f}×** 20d average"]
    if relative_volume >= REL_VOLUME_BOOST:
        return 8.0, [f"Above-average volume **{relative_volume:.1f}×**"]
    if relative_volume >= 1.0:
        return 6.0, []
    return 3.0, [f"Thin session volume **{relative_volume:.1f}×** avg"]


def screen_intraday_stock(
    *,
    nse_symbol: str,
    daily_df: pd.DataFrame | None,
    intraday_df: pd.DataFrame | None,
    relative_volume: float | None,
    nifty_df: pd.DataFrame | None,
    trade_action: str,
    nifty_bias: str = "NEUTRAL",
    avg_daily_volume: float | None = None,
    daily_range_pct: float | None = None,
    nifty_correlation: float | None = None,
) -> IntradayScreenResult:
    avg_vol = avg_daily_volume if avg_daily_volume is not None else (
        _avg_daily_volume(daily_df) if daily_df is not None else None
    )
    daily_range = daily_range_pct if daily_range_pct is not None else (
        _daily_range_pct(daily_df) if daily_df is not None else None
    )
    session_range = _session_range_pct(intraday_df)
    corr = nifty_correlation
    if corr is None and daily_df is not None:
        corr = rolling_nifty_correlation(daily_df, nifty_df)

    liq_s, liq_ok, liq_notes = score_liquidity(avg_vol, relative_volume)
    vol_s, vol_ok, vol_notes = score_volatility(daily_range, session_range)
    corr_s, corr_notes = score_correlation(corr, nifty_bias, trade_action)
    rv_s, rv_notes = score_relative_volume(relative_volume)

    notes = liq_notes + vol_notes + corr_notes + rv_notes
    composite = round(liq_s + vol_s + corr_s + rv_s, 1)

    return IntradayScreenResult(
        nse_symbol=nse_symbol,
        liquidity_score=liq_s,
        volatility_score=vol_s,
        correlation_score=corr_s,
        volume_score=rv_s,
        composite_score=composite,
        passed_liquidity=liq_ok,
        passed_volatility=vol_ok,
        avg_daily_volume=avg_vol,
        daily_range_pct=daily_range or session_range,
        relative_volume=relative_volume,
        nifty_correlation=corr,
        notes=notes,
    )


def investopedia_screen_summary() -> str:
    return (
        "Intraday picks follow [Investopedia day-trading stock selection](https://www.investopedia.com/day-trading/pick-stocks-intraday-trading/): "
        "**liquidity** (≥5L shares/day), **volatility** (≈2–5% range, not extreme), "
        "**Nifty correlation** (trade with the index trend), and **relative volume** spikes."
    )


def combined_intraday_rank(ta_score: float, screen_score: float) -> float:
    """Blend chart TA score with Investopedia screen (TA 55%, screen 45%)."""
    return round(ta_score * 0.55 + screen_score * 0.45, 1)
