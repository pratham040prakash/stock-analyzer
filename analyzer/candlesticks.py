"""
Candlestick pattern detection — rules aligned with Zerodha Varsity TA (Ch 4–10).

Source: https://zerodha.com/varsity/module/technical-analysis/
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class PatternHit:
    name: str
    signal: str  # bullish | bearish | neutral
    score: float
    detail: str


def _body(o: float, c: float) -> float:
    return abs(c - o)


def _range(h: float, l: float) -> float:
    return max(h - l, 1e-9)


def _upper_wick(o: float, c: float, h: float) -> float:
    return h - max(o, c)


def _lower_wick(o: float, c: float, l: float) -> float:
    return min(o, c) - l


def _is_bullish(o: float, c: float) -> bool:
    return c > o


def _prior_trend(df: pd.DataFrame, index: int, lookback: int = 5) -> str:
    """Varsity Ch 4: pattern meaning depends on trend context."""
    start = max(0, index - lookback)
    if start >= index:
        return "neutral"
    segment = df.iloc[start:index]["Close"]
    if len(segment) < 2:
        return "neutral"
    change = float(segment.iloc[-1]) - float(segment.iloc[0])
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "neutral"


def detect_patterns_at(df: pd.DataFrame, index: int = -1) -> list[PatternHit]:
    """Detect Varsity single & multi-candle patterns at a given bar."""
    if index < 0:
        index = len(df) + index
    if index < 1 or index >= len(df):
        return []

    signals: list[PatternHit] = []
    row = df.iloc[index]
    prev = df.iloc[index - 1]
    o, h, l, c = float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"])
    po, ph, pl, pc = float(prev["Open"]), float(prev["High"]), float(prev["Low"]), float(prev["Close"])

    rng = _range(h, l)
    body = _body(o, c)
    body_ratio = body / rng
    trend = _prior_trend(df, index)

    # Ch 5 — Marubozu
    if body_ratio > 0.85:
        if _is_bullish(o, c):
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bullish", 0.75,
                "Bullish Marubozu (Ch 5) — strong buying; stop below candle low",
            ))
        else:
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bearish", -0.75,
                "Bearish Marubozu (Ch 5) — strong selling; stop above candle high",
            ))

    # Ch 6 — Doji / Spinning top
    elif body_ratio < 0.08:
        if trend == "up":
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bearish", -0.5,
                "Doji after rally (Ch 6) — indecision; potential reversal down",
            ))
        elif trend == "down":
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bullish", 0.5,
                "Doji after decline (Ch 6) — indecision; potential reversal up",
            ))
        else:
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "neutral", 0.0,
                "Doji (Ch 6) — wait for confirmation candle",
            ))
    elif body_ratio < 0.35 and _upper_wick(o, c, h) > body and _lower_wick(o, c, l) > body:
        signals.append(PatternHit(
            "Candlestick (Varsity)",
            "neutral", 0.0,
            "Spinning top (Ch 6) — hesitation; confirm next candle",
        ))

    # Ch 7 — Hammer / Hanging Man
    lw = _lower_wick(o, c, l)
    uw = _upper_wick(o, c, h)
    if lw >= 2 * body and uw <= body * 0.5 and body_ratio < 0.4:
        if trend == "down":
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bullish", 0.65,
                "Hammer (Ch 7) at support zone — bullish reversal candidate",
            ))
        elif trend == "up":
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bearish", -0.65,
                "Hanging Man (Ch 7) after rally — bearish reversal warning",
            ))

    # Ch 8 — Engulfing
    if not _is_bullish(po, pc) and _is_bullish(o, c):
        if o <= pc and c >= po:
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bullish", 0.7,
                "Bullish Engulfing (Ch 8) — buy signal; confirm with volume",
            ))
    if _is_bullish(po, pc) and not _is_bullish(o, c):
        if o >= pc and c <= po:
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bearish", -0.7,
                "Bearish Engulfing (Ch 8) — sell signal; confirm with volume",
            ))

    # Ch 9 — Harami
    if _body(po, pc) > body * 2:
        if max(o, c) <= max(po, pc) and min(o, c) >= min(po, pc):
            bias = "bullish" if not _is_bullish(po, pc) and _is_bullish(o, c) else "bearish"
            if not _is_bullish(po, pc):
                signals.append(PatternHit(
                    "Candlestick (Varsity)",
                    "bullish", 0.4,
                    "Bullish Harami (Ch 9) — momentum pause; needs confirmation",
                ))
            elif _is_bullish(po, pc):
                signals.append(PatternHit(
                    "Candlestick (Varsity)",
                    "bearish", -0.4,
                    "Bearish Harami (Ch 9) — momentum pause; needs confirmation",
                ))

    # Ch 10 — Morning / Evening Star (3-candle)
    if index >= 2:
        p2 = df.iloc[index - 2]
        o2, c2 = float(p2["Open"]), float(p2["Close"])
        small_mid = body / rng < 0.35 if rng else True
        if not _is_bullish(o2, c2) and small_mid and _is_bullish(o, c) and c > o2:
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bullish", 0.8,
                "Morning Star (Ch 10) — three-candle bullish reversal",
            ))
        if _is_bullish(o2, c2) and small_mid and not _is_bullish(o, c) and c < o2:
            signals.append(PatternHit(
                "Candlestick (Varsity)",
                "bearish", -0.8,
                "Evening Star (Ch 10) — three-candle bearish reversal",
            ))

    return signals


def detect_patterns(df: pd.DataFrame) -> list[PatternHit]:
    return detect_patterns_at(df, index=-1)
