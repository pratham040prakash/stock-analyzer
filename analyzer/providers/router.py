"""Route data requests: Kite (live) → Yahoo (fallback)."""

from __future__ import annotations

import pandas as pd

from analyzer.providers.kite import fetch_kite_intraday, fetch_kite_ltp, is_kite_configured
from analyzer.providers.types import IntradayMeta
from analyzer.providers.yahoo import fetch_yahoo_intraday
from analyzer.zerodha import load_env_credentials


def is_kite_live() -> bool:
    return is_kite_configured()


def data_source_status() -> dict:
    creds = load_env_credentials()
    kite_ok = is_kite_configured()
    return {
        "kite_configured": kite_ok,
        "kite_api_key_set": bool(creds.get("api_key")),
        "kite_token_set": bool(creds.get("access_token")),
        "primary_intraday": "Kite" if kite_ok else "Yahoo Finance",
        "primary_ltp": "Kite WebSocket/REST" if kite_ok else "Yahoo Finance",
        "upgrade_hint": (
            "Add ZERODHA_API_KEY + ZERODHA_ACCESS_TOKEN to .env for live candles & LTP."
            if not kite_ok
            else "Kite live data active — intraday uses exchange candles when available."
        ),
    }


def fetch_intraday_bars(
    ticker: str,
    interval: str = "5m",
    market: str = "india",
    prefer_kite: bool = True,
) -> tuple[pd.DataFrame, IntradayMeta]:
    """
    Intraday OHLCV with automatic source selection.
    India + Kite token → Kite historical candles; else Yahoo.
    """
    if market == "india" and prefer_kite and is_kite_configured():
        kite_result = fetch_kite_intraday(ticker, interval)
        if kite_result is not None:
            return kite_result

    df, meta = fetch_yahoo_intraday(ticker, interval, market=market)
    return df, meta


def get_live_ltp(ticker: str, market: str = "india") -> tuple[float | None, str]:
    """Best available last price. Returns (price, source label)."""
    if market == "india" and is_kite_configured():
        ltp = fetch_kite_ltp(ticker)
        if ltp is not None:
            return ltp, "Kite"
    try:
        df, meta = fetch_yahoo_intraday(ticker, "5m", market=market)
        return float(df["Close"].iloc[-1]), meta.source
    except Exception:
        return None, "unavailable"
