"""Compute technical indicators on OHLCV data."""

from __future__ import annotations

import pandas as pd

from analyzer import ta


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators to an OHLCV dataframe."""
    out = df.copy()

    out["SMA_20"] = ta.sma(out["Close"], length=20)
    out["SMA_50"] = ta.sma(out["Close"], length=50)
    out["SMA_200"] = ta.sma(out["Close"], length=200)
    out["EMA_12"] = ta.ema(out["Close"], length=12)
    out["EMA_26"] = ta.ema(out["Close"], length=26)

    macd = ta.macd(out["Close"], fast=12, slow=26, signal=9)
    if macd is not None:
        out = out.join(macd)

    out["RSI_14"] = ta.rsi(out["Close"], length=14)

    bbands = ta.bbands(out["Close"], length=20, std=2)
    if bbands is not None:
        out = out.join(bbands)

    stoch = ta.stoch(out["High"], out["Low"], out["Close"], k=14, d=3)
    if stoch is not None:
        out = out.join(stoch)

    adx = ta.adx(out["High"], out["Low"], out["Close"], length=14)
    if adx is not None:
        out = out.join(adx)

    out["ATR_14"] = ta.atr(out["High"], out["Low"], out["Close"], length=14)
    out["OBV"] = ta.obv(out["Close"], out["Volume"])
    out["VOL_SMA_20"] = ta.sma(out["Volume"], length=20)

    return out
