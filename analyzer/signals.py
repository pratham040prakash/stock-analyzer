"""Generate buy/sell/hold signals from technical indicators (Zerodha Varsity TA framework)."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.candlesticks import detect_patterns_at
from analyzer.varsity_knowledge import (
    ADX_TREND_THRESHOLD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    varsity_adx_is_trending,
    varsity_confidence_adjustment,
)


@dataclass
class SignalDetail:
    name: str
    signal: str  # bullish | bearish | neutral
    score: float  # -1.0 to +1.0
    detail: str


@dataclass
class AnalysisResult:
    ticker: str
    recommendation: str  # STRONG BUY | BUY | HOLD | SELL | STRONG SELL
    composite_score: float  # -100 to +100
    confidence: str  # low | medium | high
    current_price: float
    signals: list[SignalDetail] = field(default_factory=list)
    support: float | None = None
    resistance: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None


def _rsi_signal(rsi: float) -> SignalDetail:
    # Varsity Ch 14 — RSI 30/70 zones; use with trend filter
    if rsi < RSI_OVERSOLD:
        return SignalDetail(
            "RSI (14)", "bullish", 0.8,
            f"Oversold at {rsi:.1f} (Varsity Ch 14) — potential bounce; confirm in uptrend",
        )
    if rsi > RSI_OVERBOUGHT:
        return SignalDetail(
            "RSI (14)", "bearish", -0.8,
            f"Overbought at {rsi:.1f} (Varsity Ch 14) — pullback risk; don't fade strong trends blindly",
        )
    if rsi < 45:
        return SignalDetail("RSI (14)", "bullish", 0.3, f"RSI {rsi:.1f} — leaning bullish")
    if rsi > 55:
        return SignalDetail("RSI (14)", "bearish", -0.3, f"RSI {rsi:.1f} — leaning bearish")
    return SignalDetail("RSI (14)", "neutral", 0.0, f"RSI {rsi:.1f} — neutral zone")


def _macd_signal(macd: float, signal: float, hist: float) -> SignalDetail:
    if hist > 0 and macd > signal:
        score = min(1.0, abs(hist) * 10)
        return SignalDetail("MACD", "bullish", score, "MACD above signal line — bullish momentum")
    if hist < 0 and macd < signal:
        score = max(-1.0, -abs(hist) * 10)
        return SignalDetail("MACD", "bearish", score, "MACD below signal line — bearish momentum")
    return SignalDetail("MACD", "neutral", 0.0, "MACD and signal converging — no clear trend")


def _ma_signal(price: float, sma20: float, sma50: float, sma200: float | None) -> SignalDetail:
    score = 0.0
    parts = []

    if price > sma20:
        score += 0.25
        parts.append("above SMA-20")
    else:
        score -= 0.25
        parts.append("below SMA-20")

    if price > sma50:
        score += 0.35
        parts.append("above SMA-50")
    else:
        score -= 0.35
        parts.append("below SMA-50")

    if sma200 and not pd.isna(sma200):
        if price > sma200:
            score += 0.4
            parts.append("above SMA-200 (long-term bullish)")
        else:
            score -= 0.4
            parts.append("below SMA-200 (long-term bearish)")

    if sma50 > (sma200 or sma50):
        score += 0.2
        parts.append("golden cross territory")
    elif sma200 and sma50 < sma200:
        score -= 0.2
        parts.append("death cross territory")

    score = max(-1.0, min(1.0, score))
    direction = "bullish" if score > 0.2 else "bearish" if score < -0.2 else "neutral"
    return SignalDetail("Moving Averages", direction, score, "; ".join(parts))


def _bollinger_signal(price: float, lower: float, upper: float, mid: float) -> SignalDetail:
    band_width = upper - lower
    if band_width <= 0:
        return SignalDetail("Bollinger Bands", "neutral", 0.0, "Insufficient band data")

    position = (price - lower) / band_width
    if position < 0.15:
        return SignalDetail("Bollinger Bands", "bullish", 0.7, "Price near lower band — oversold bounce likely")
    if position > 0.85:
        return SignalDetail("Bollinger Bands", "bearish", -0.7, "Price near upper band — overextended")
    if price > mid:
        return SignalDetail("Bollinger Bands", "bullish", 0.2, "Price above middle band")
    return SignalDetail("Bollinger Bands", "bearish", -0.2, "Price below middle band")


def _stochastic_signal(k: float, d: float) -> SignalDetail:
    if k < 20 and d < 20:
        return SignalDetail("Stochastic", "bullish", 0.7, f"%K={k:.1f}, %D={d:.1f} — oversold")
    if k > 80 and d > 80:
        return SignalDetail("Stochastic", "bearish", -0.7, f"%K={k:.1f}, %D={d:.1f} — overbought")
    if k > d:
        return SignalDetail("Stochastic", "bullish", 0.3, f"%K crossing above %D ({k:.1f}/{d:.1f})")
    if k < d:
        return SignalDetail("Stochastic", "bearish", -0.3, f"%K crossing below %D ({k:.1f}/{d:.1f})")
    return SignalDetail("Stochastic", "neutral", 0.0, f"%K={k:.1f}, %D={d:.1f}")


def _adx_signal(adx: float, plus_di: float, minus_di: float) -> SignalDetail:
    # Varsity Ch 20 — ADX measures trend strength, +DI/-DI direction
    if not varsity_adx_is_trending(adx):
        return SignalDetail(
            "ADX", "neutral", 0.0,
            f"ADX {adx:.1f} < {ADX_TREND_THRESHOLD} (Ch 20) — range-bound; avoid trend strategies",
        )
    if plus_di > minus_di:
        strength = min(1.0, adx / 50)
        return SignalDetail("ADX", "bullish", strength, f"Uptrend (Ch 20): ADX {adx:.1f}, +DI > -DI")
    strength = max(-1.0, -adx / 50)
    return SignalDetail("ADX", "bearish", strength, f"Downtrend (Ch 20): ADX {adx:.1f}, -DI > +DI")


def _volume_signal(volume: float, vol_sma: float, price_change: float) -> SignalDetail:
    # Varsity Ch 12 — volume validates price moves
    if vol_sma <= 0 or pd.isna(vol_sma):
        return SignalDetail("Volume", "neutral", 0.0, "Insufficient volume data")

    ratio = volume / vol_sma
    if ratio > 1.5 and price_change > 0:
        return SignalDetail(
            "Volume", "bullish", 0.6,
            f"High volume up-day {ratio:.1f}x avg (Ch 12) — breakout conviction",
        )
    if ratio > 1.5 and price_change < 0:
        return SignalDetail(
            "Volume", "bearish", -0.6,
            f"High volume down-day {ratio:.1f}x avg (Ch 12) — distribution",
        )
    if ratio < 0.7:
        return SignalDetail("Volume", "neutral", 0.0, f"Low volume ({ratio:.1f}x avg) — weak conviction")
    return SignalDetail("Volume", "neutral", 0.0, f"Normal volume ({ratio:.1f}x avg)")


def _support_resistance_signal(
    price: float, support: float, resistance: float,
) -> SignalDetail:
    """Varsity Ch 11 — S/R zones for entries and targets."""
    span = resistance - support
    if span <= 0:
        return SignalDetail("Support/Resistance", "neutral", 0.0, "Insufficient S/R data")
    pos = (price - support) / span
    if pos < 0.2:
        return SignalDetail(
            "Support/Resistance", "bullish", 0.55,
            f"Near support ₹{support:,.2f} (Ch 11) — buy zone; stop below support",
        )
    if pos > 0.8:
        return SignalDetail(
            "Support/Resistance", "bearish", -0.55,
            f"Near resistance ₹{resistance:,.2f} (Ch 11) — trim/target zone",
        )
    return SignalDetail(
        "Support/Resistance", "neutral", 0.0,
        f"Mid-range between ₹{support:,.2f} and ₹{resistance:,.2f}",
    )


def _score_to_recommendation(score: float) -> str:
    if score >= 50:
        return "STRONG BUY"
    if score >= 20:
        return "BUY"
    if score <= -50:
        return "STRONG SELL"
    if score <= -20:
        return "SELL"
    return "HOLD"


def _score_to_confidence(signals: list[SignalDetail]) -> str:
    return varsity_confidence_adjustment(signals)


def analyze_at_index(df: pd.DataFrame, ticker: str, index: int = -1) -> AnalysisResult:
    """Run signal analysis at a specific row index (for backtesting)."""
    if index < 0:
        index = len(df) + index
    if index < 0 or index >= len(df):
        raise IndexError(f"Index {index} out of range for dataframe with {len(df)} rows")

    row = df.iloc[index]
    prev = df.iloc[index - 1] if index > 0 else row
    price = float(row["Close"])

    signals: list[SignalDetail] = []

    if not pd.isna(row.get("RSI_14")):
        signals.append(_rsi_signal(float(row["RSI_14"])))

    macd_col = "MACD_12_26_9"
    signal_col = "MACDs_12_26_9"
    hist_col = "MACDh_12_26_9"
    if all(c in df.columns and not pd.isna(row.get(c)) for c in (macd_col, signal_col, hist_col)):
        signals.append(
            _macd_signal(float(row[macd_col]), float(row[signal_col]), float(row[hist_col]))
        )

    if not pd.isna(row.get("SMA_20")) and not pd.isna(row.get("SMA_50")):
        sma200 = float(row["SMA_200"]) if not pd.isna(row.get("SMA_200")) else None
        signals.append(_ma_signal(price, float(row["SMA_20"]), float(row["SMA_50"]), sma200))

    bb_lower = "BBL_20_2.0"
    bb_upper = "BBU_20_2.0"
    bb_mid = "BBM_20_2.0"
    if all(c in df.columns and not pd.isna(row.get(c)) for c in (bb_lower, bb_upper, bb_mid)):
        signals.append(
            _bollinger_signal(price, float(row[bb_lower]), float(row[bb_upper]), float(row[bb_mid]))
        )

    stoch_k = "STOCHk_14_3_3"
    stoch_d = "STOCHd_14_3_3"
    if stoch_k in df.columns and stoch_d in df.columns and not pd.isna(row.get(stoch_k)):
        signals.append(_stochastic_signal(float(row[stoch_k]), float(row[stoch_d])))

    adx_col = "ADX_14"
    plus_di = "DMP_14"
    minus_di = "DMN_14"
    if all(c in df.columns and not pd.isna(row.get(adx_col)) for c in (adx_col, plus_di, minus_di)):
        signals.append(_adx_signal(float(row[adx_col]), float(row[plus_di]), float(row[minus_di])))

    if not pd.isna(row.get("VOL_SMA_20")):
        price_change = float(row["Close"]) - float(prev["Close"])
        signals.append(_volume_signal(float(row["Volume"]), float(row["VOL_SMA_20"]), price_change))

    # Varsity Ch 4–10 — candlestick patterns (with trend context)
    for hit in detect_patterns_at(df, index):
        signals.append(SignalDetail(hit.name, hit.signal, hit.score, hit.detail))

    window = df.iloc[max(0, index - 19) : index + 1]
    recent_lows = float(window["Low"].min())
    recent_highs = float(window["High"].max())
    signals.append(_support_resistance_signal(price, recent_lows, recent_highs))

    weights = {
        "RSI (14)": 1.2,
        "MACD": 1.3,
        "Moving Averages": 1.5,
        "Bollinger Bands": 1.0,
        "Stochastic": 0.9,
        "ADX": 1.1,
        "Volume": 0.8,
        "Candlestick (Varsity)": 1.2,
        "Support/Resistance": 1.0,
    }
    total_weight = sum(weights.get(s.name, 1.0) for s in signals)
    composite = sum(s.score * weights.get(s.name, 1.0) for s in signals) / total_weight * 100

    atr = float(row["ATR_14"]) if not pd.isna(row.get("ATR_14")) else price * 0.02

    return AnalysisResult(
        ticker=ticker,
        recommendation=_score_to_recommendation(composite),
        composite_score=round(composite, 1),
        confidence=_score_to_confidence(signals),
        current_price=price,
        signals=signals,
        support=round(recent_lows, 2),
        resistance=round(recent_highs, 2),
        stop_loss=round(price - 2 * atr, 2),
        take_profit=round(price + 3 * atr, 2),
    )


def analyze(df: pd.DataFrame, ticker: str) -> AnalysisResult:
    """Run full signal analysis on the latest row."""
    return analyze_at_index(df, ticker, index=-1)
