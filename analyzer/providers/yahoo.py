"""Yahoo Finance intraday bars (fallback; ~15–20 min lag on minute data)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import yfinance as yf

from analyzer.market_session import IST, market_session_status
from analyzer.markets import resolve_ticker
from analyzer.providers.types import IntradayMeta

INTERVAL_PERIOD = {
    "1m": "5d",
    "5m": "1mo",
    "15m": "1mo",
}


def fetch_yahoo_intraday(
    ticker: str,
    interval: str,
    market: str = "india",
) -> tuple[pd.DataFrame, IntradayMeta]:
    if interval not in INTERVAL_PERIOD:
        raise ValueError(f"Unsupported interval '{interval}'.")

    candidates = resolve_ticker(ticker, market)
    symbol = candidates[0] if candidates else ticker
    period = INTERVAL_PERIOD[interval]

    stock = yf.Ticker(symbol)
    df = stock.history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No intraday data for '{symbol}'.")

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert(IST)

    today = datetime.now(IST).date()
    session = df[df.index.date == today]
    if session.empty:
        last_date = df.index.date[-1]
        session = df[df.index.date == last_date]
        today = last_date

    session = session.between_time("09:15", "15:30")
    if session.empty:
        raise ValueError(f"No session bars for '{symbol}'.")

    meta = IntradayMeta(
        symbol=symbol,
        interval=interval,
        session_date=str(today),
        bars=len(session),
        source="Yahoo Finance",
        market=market_session_status(),
        lag_note="Yahoo intraday may lag 15–20 min during live session.",
    )
    return session, meta
