"""Intraday indicators and session trading signals."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer import ta


@dataclass
class IntradaySignal:
    name: str
    bias: str  # bullish | bearish | neutral
    detail: str


@dataclass
class IntradayAnalysis:
    ticker: str
    interval: str
    last_price: float
    vwap: float
    opening_range_high: float
    opening_range_low: float
    rsi: float | None
    session_bias: str  # BULLISH | BEARISH | NEUTRAL
    trade_setup: str  # BUY | SELL | WAIT
    entry: float | None
    stop_loss: float | None
    target: float | None
    signals: list[IntradaySignal] = field(default_factory=list)
    note: str = ""


def add_intraday_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """VWAP, fast EMAs, RSI for intraday."""
    out = df.copy()
    typical = (out["High"] + out["Low"] + out["Close"]) / 3
    cum_vol = out["Volume"].cumsum()
    cum_pv = (typical * out["Volume"]).cumsum()
    out["VWAP"] = cum_pv / cum_vol.replace(0, pd.NA)

    out["EMA_9"] = ta.ema(out["Close"], length=9)
    out["EMA_21"] = ta.ema(out["Close"], length=21)
    out["RSI_7"] = ta.rsi(out["Close"], length=7)
    out["VOL_SMA"] = ta.sma(out["Volume"], length=10)
    return out


def _opening_range(df: pd.DataFrame, bars: int = 3) -> tuple[float, float]:
    """First N candles = opening range (15 min on 5m chart)."""
    head = df.head(min(bars, len(df)))
    return float(head["High"].max()), float(head["Low"].min())


def analyze_intraday(df: pd.DataFrame, ticker: str, interval: str) -> IntradayAnalysis:
    """Generate intraday trade setup from session candles."""
    if len(df) < 5:
        raise ValueError("Not enough intraday bars yet. Wait for market to open.")

    df = add_intraday_indicators(df)
    row = df.iloc[-1]
    price = float(row["Close"])
    vwap = float(row["VWAP"]) if not pd.isna(row["VWAP"]) else price
    rsi = float(row["RSI_7"]) if not pd.isna(row.get("RSI_7")) else None
    or_high, or_low = _opening_range(df)
    ema9 = float(row["EMA_9"]) if not pd.isna(row.get("EMA_9")) else price
    ema21 = float(row["EMA_21"]) if not pd.isna(row.get("EMA_21")) else price

    signals: list[IntradaySignal] = []
    score = 0

    # VWAP — institutional reference for the day
    if price > vwap * 1.001:
        signals.append(IntradaySignal("VWAP", "bullish", f"Price ₹{price:.2f} above VWAP ₹{vwap:.2f} — buyers in control"))
        score += 1
    elif price < vwap * 0.999:
        signals.append(IntradaySignal("VWAP", "bearish", f"Price below VWAP ₹{vwap:.2f} — sellers in control"))
        score -= 1
    else:
        signals.append(IntradaySignal("VWAP", "neutral", f"Price at VWAP ₹{vwap:.2f} — equilibrium"))

    # Opening range breakout
    if price > or_high:
        signals.append(IntradaySignal("Opening Range", "bullish", f"Breakout above OR high ₹{or_high:.2f}"))
        score += 2
    elif price < or_low:
        signals.append(IntradaySignal("Opening Range", "bearish", f"Breakdown below OR low ₹{or_low:.2f}"))
        score -= 2
    else:
        signals.append(IntradaySignal("Opening Range", "neutral", f"Inside range ₹{or_low:.2f}–₹{or_high:.2f}"))

    # EMA crossover
    if ema9 > ema21:
        signals.append(IntradaySignal("EMA 9/21", "bullish", "Fast EMA above slow — short-term momentum up"))
        score += 1
    else:
        signals.append(IntradaySignal("EMA 9/21", "bearish", "Fast EMA below slow — short-term momentum down"))
        score -= 1

    # RSI
    if rsi is not None:
        if rsi < 30:
            signals.append(IntradaySignal("RSI (7)", "bullish", f"RSI {rsi:.0f} oversold — bounce play"))
            score += 1
        elif rsi > 70:
            signals.append(IntradaySignal("RSI (7)", "bearish", f"RSI {rsi:.0f} overbought — fade risk"))
            score -= 1
        elif rsi > 55:
            signals.append(IntradaySignal("RSI (7)", "bullish", f"RSI {rsi:.0f} — bullish momentum"))
            score += 0.5
        elif rsi < 45:
            signals.append(IntradaySignal("RSI (7)", "bearish", f"RSI {rsi:.0f} — weak momentum"))
            score -= 0.5
        else:
            signals.append(IntradaySignal("RSI (7)", "neutral", f"RSI {rsi:.0f} neutral"))

    # Volume
    vol = float(row["Volume"])
    vol_sma = float(row["VOL_SMA"]) if not pd.isna(row.get("VOL_SMA")) else vol
    if vol > vol_sma * 1.5:
        direction = "bullish" if float(row["Close"]) >= float(row["Open"]) else "bearish"
        signals.append(IntradaySignal("Volume", direction, f"Volume spike {vol/vol_sma:.1f}x average"))
        score += 1 if direction == "bullish" else -1

    if score >= 2:
        session_bias = "BULLISH"
        trade_setup = "BUY"
    elif score <= -2:
        session_bias = "BEARISH"
        trade_setup = "SELL"
    else:
        session_bias = "NEUTRAL"
        trade_setup = "WAIT"

    # Levels computed after Decision Engine maps trade_setup
    entry = stop = target = None

    result = IntradayAnalysis(
        ticker=ticker,
        interval=interval,
        last_price=price,
        vwap=vwap,
        opening_range_high=or_high,
        opening_range_low=or_low,
        rsi=rsi,
        session_bias=session_bias,
        trade_setup=trade_setup,
        entry=entry,
        stop_loss=stop,
        target=target,
        signals=signals,
        note="Intraday only — square off before 3:20 PM IST. Data may lag 15–20 min via Yahoo.",
    )
    from analyzer.decision_engine.verdict_bridge import attach_decision_to_intraday

    attach_decision_to_intraday(result)
    trade_setup = result.trade_setup
    if trade_setup == "BUY":
        entry = price
        stop = min(or_low, vwap) * 0.998
        risk = entry - stop
        target = entry + risk * 1.5 if risk > 0 else price * 1.005
        result.entry = round(entry, 2)
        result.stop_loss = round(stop, 2)
        result.target = round(target, 2)
    elif trade_setup == "SELL":
        entry = price
        stop = max(or_high, vwap) * 1.002
        risk = stop - entry
        target = entry - risk * 1.5 if risk > 0 else price * 0.995
        result.entry = round(entry, 2)
        result.stop_loss = round(stop, 2)
        result.target = round(target, 2)
    return result


def compute_trade_levels(
    intraday: IntradayAnalysis,
    action: str,
) -> tuple[float | None, float | None, float | None]:
    """Entry/stop/target aligned with equity verdict (BUY/SELL/WAIT)."""
    if action in ("WAIT", "ERROR"):
        return None, None, None

    aligned = (
        (action in ("STRONG BUY", "BUY") and intraday.trade_setup == "BUY")
        or (action in ("STRONG SELL", "SELL") and intraday.trade_setup == "SELL")
    )
    if aligned and intraday.entry is not None:
        return intraday.entry, intraday.stop_loss, intraday.target

    price = intraday.last_price
    vwap = intraday.vwap
    or_h, or_l = intraday.opening_range_high, intraday.opening_range_low

    if action in ("STRONG BUY", "BUY"):
        entry = price
        stop = min(or_l, vwap) * 0.998
        risk = entry - stop
        target = entry + risk * 1.5 if risk > 0 else price * 1.005
        return round(entry, 2), round(stop, 2), round(target, 2)

    if action in ("STRONG SELL", "SELL"):
        entry = price
        stop = max(or_h, vwap) * 1.002
        risk = stop - entry
        target = entry - risk * 1.5 if risk > 0 else price * 0.995
        return round(entry, 2), round(stop, 2), round(target, 2)

    return None, None, None
