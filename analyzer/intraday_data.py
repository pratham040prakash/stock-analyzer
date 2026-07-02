"""Fetch intraday OHLCV bars for live charting."""

from __future__ import annotations

from analyzer.market_session import IST, market_session_status
from analyzer.providers.router import fetch_intraday_bars
from analyzer.providers.types import IntradayMeta

INTERVAL_OPTIONS = {
    "1 min": "1m",
    "5 min": "5m",
    "15 min": "15m",
}

INTERVAL_PERIOD = {
    "1m": "5d",
    "5m": "1mo",
    "15m": "1mo",
}


def _meta_to_dict(meta: IntradayMeta) -> dict:
    return {
        "symbol": meta.symbol,
        "interval": meta.interval,
        "session_date": meta.session_date,
        "bars": meta.bars,
        "source": meta.source,
        "lag_note": meta.lag_note,
        "market": meta.market,
    }


def fetch_intraday(
    ticker: str,
    interval: str = "5m",
    market: str = "india",
) -> tuple:
    """
    Fetch intraday candles. Returns (dataframe, meta dict).
    India: Kite when configured, else Yahoo Finance.
    """
    if interval not in INTERVAL_PERIOD:
        raise ValueError(f"Unsupported interval '{interval}'. Use 1m, 5m, or 15m.")

    df, meta = fetch_intraday_bars(ticker, interval=interval, market=market)
    return df, _meta_to_dict(meta)
