"""Pure-pandas technical indicators (no numba / pandas-ta dependency)."""

from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).mean()


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False, min_periods=length).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    suffix = f"{fast}_{slow}_{signal}"
    return pd.DataFrame(
        {
            f"MACD_{suffix}": macd_line,
            f"MACDs_{suffix}": signal_line,
            f"MACDh_{suffix}": hist,
        }
    )


def bbands(series: pd.Series, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    mid = sma(series, length)
    dev = series.rolling(length, min_periods=length).std()
    suffix = f"{length}_{std}"
    return pd.DataFrame(
        {
            f"BBL_{suffix}": mid - std * dev,
            f"BBM_{suffix}": mid,
            f"BBU_{suffix}": mid + std * dev,
        }
    )


def stoch(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k: int = 14,
    d: int = 3,
) -> pd.DataFrame:
    lowest = low.rolling(k, min_periods=k).min()
    highest = high.rolling(k, min_periods=k).max()
    denom = (highest - lowest).replace(0, pd.NA)
    stoch_k = 100 * (close - lowest) / denom
    stoch_d = stoch_k.rolling(d, min_periods=d).mean()
    suffix = f"{k}_{d}_{d}"
    return pd.DataFrame({f"STOCHk_{suffix}": stoch_k, f"STOCHd_{suffix}": stoch_d})


def _wilder_smooth(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.DataFrame:
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = _wilder_smooth(tr, length)
    plus_di = 100 * _wilder_smooth(plus_dm, length) / atr.replace(0, pd.NA)
    minus_di = 100 * _wilder_smooth(minus_dm, length) / atr.replace(0, pd.NA)
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA) * 100
    adx_line = _wilder_smooth(dx, length)

    return pd.DataFrame(
        {
            f"ADX_{length}": adx_line,
            f"DMP_{length}": plus_di,
            f"DMN_{length}": minus_di,
        }
    )


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return _wilder_smooth(tr, length).rename(f"ATR_{length}")


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = close.diff().fillna(0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum().rename("OBV")
