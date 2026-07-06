"""Route data requests: Kite (live) → Yahoo (fallback)."""

from __future__ import annotations

import pandas as pd

from analyzer.kite_status import kite_market_data_ok, probe_kite_market_data
from analyzer.providers.kite import fetch_kite_intraday, fetch_kite_ltp, is_kite_configured
from analyzer.providers.types import IntradayMeta
from analyzer.providers.yahoo import fetch_yahoo_intraday
from analyzer.zerodha import load_env_credentials


def is_kite_live() -> bool:
    return is_kite_configured() and kite_market_data_ok()


def data_source_status() -> dict:
    creds = load_env_credentials()
    logged_in = is_kite_configured()
    live = kite_market_data_ok() if logged_in else False
    market = probe_kite_market_data() if logged_in else "not_logged_in"
    return {
        "kite_configured": logged_in,
        "kite_live_data": live,
        "kite_market_data": market,
        "kite_api_key_set": bool(creds.get("api_key")),
        "kite_token_set": bool(creds.get("access_token")),
        "primary_intraday": "Kite" if live else "Yahoo Finance",
        "primary_ltp": "Kite" if live else "Yahoo Finance",
        "upgrade_hint": (
            "Sidebar → **Login with Zerodha** for holdings and orders."
            if not logged_in
            else (
                "Kite live quotes active."
                if live
                else "Kite login OK — prices use Yahoo/NSE (market data API not subscribed)."
            )
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
    if market == "india" and prefer_kite and is_kite_live():
        kite_result = fetch_kite_intraday(ticker, interval)
        if kite_result is not None:
            return kite_result

    df, meta = fetch_yahoo_intraday(ticker, interval, market=market)
    return df, meta


def get_live_ltp(ticker: str, market: str = "india") -> tuple[float | None, str]:
    """Best available last price. Returns (price, source label)."""
    if market == "india" and is_kite_live():
        ltp = fetch_kite_ltp(ticker)
        if ltp is not None:
            return ltp, "Kite"
    try:
        df, meta = fetch_yahoo_intraday(ticker, "5m", market=market)
        return float(df["Close"].iloc[-1]), meta.source
    except Exception:
        return None, "unavailable"
