"""Zerodha Kite intraday candles + LTP (exchange-grade when subscribed)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from analyzer.india import NSE_SYMBOL_REDIRECT
from analyzer.market_session import IST, market_session_status
from analyzer.kite_stream import get_ltp_by_kite_symbol, resolve_instrument_tokens
from analyzer.providers.types import IntradayMeta
from analyzer.zerodha import get_kite_client, kite_to_yahoo, yahoo_to_kite

KITE_INTERVAL = {
    "1m": "minute",
    "5m": "5minute",
    "15m": "15minute",
}

_INDEX_TOKEN = {
    "NIFTY": 256265,
    "BANKNIFTY": 260105,
    "FINNIFTY": 257801,
    "MIDCPNIFTY": 288009,
}

def is_kite_configured() -> bool:
    return get_kite_client() is not None


def _normalize_base(ticker: str) -> str:
    base = ticker.upper().strip()
    base = base.replace(".NS", "").replace(".BO", "")
    base = NSE_SYMBOL_REDIRECT.get(base, base)
    return base


_YAHOO_FOR_INDEX = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "^NSEI",
    "MIDCPNIFTY": "^NSEI",
}


_YAHOO_TO_INDEX = {
    "^NSEI": "NIFTY",
    "^NSEBANK": "BANKNIFTY",
}


def _instrument_token(base: str) -> int | None:
    if base in _INDEX_TOKEN:
        return _INDEX_TOKEN[base]
    if base.startswith("^"):
        name = _YAHOO_TO_INDEX.get(base)
        if name:
            return _INDEX_TOKEN.get(name)

    kite_sym = yahoo_to_kite(f"{base}.NS")
    tokens = resolve_instrument_tokens([kite_sym])
    return tokens[0] if tokens else None


def fetch_kite_intraday(
    ticker: str,
    interval: str,
) -> tuple[pd.DataFrame, IntradayMeta] | None:
    """Return intraday OHLCV from Kite historical API, or None if unavailable."""
    if interval not in KITE_INTERVAL:
        return None

    kite = get_kite_client()
    if kite is None:
        return None

    base = _normalize_base(ticker)
    token = _instrument_token(base)
    if token is None:
        return None

    now = datetime.now(IST)
    lookback = timedelta(days=5 if interval == "1m" else 30)
    from_dt = now - lookback

    try:
        raw = kite.historical_data(
            token,
            from_dt.replace(tzinfo=None),
            now.replace(tzinfo=None),
            KITE_INTERVAL[interval],
            continuous=False,
            oi=False,
        )
    except Exception:
        return None

    if not raw:
        return None

    df = pd.DataFrame(raw)
    df = df.rename(
        columns={
            "date": "Datetime",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    if "Datetime" not in df.columns and "date" in df.columns:
        df["Datetime"] = df["date"]

    df["Datetime"] = pd.to_datetime(df["Datetime"])
    if df["Datetime"].dt.tz is None:
        df["Datetime"] = df["Datetime"].dt.tz_localize(IST)
    else:
        df["Datetime"] = df["Datetime"].dt.tz_convert(IST)

    df = df.set_index("Datetime")[["Open", "High", "Low", "Close", "Volume"]]

    today = now.date()
    session = df[df.index.date == today]
    if session.empty:
        last_date = df.index.date[-1]
        session = df[df.index.date == last_date]
        today = last_date

    session = session.between_time("09:15", "15:30")
    if session.empty:
        return None

    yahoo_sym = _YAHOO_FOR_INDEX.get(base, kite_to_yahoo(yahoo_to_kite(f"{base}.NS")))

    meta = IntradayMeta(
        symbol=yahoo_sym,
        interval=interval,
        session_date=str(today),
        bars=len(session),
        source="Kite",
        market=market_session_status(),
        lag_note="Live Kite candles (requires Kite Connect + market data subscription).",
    )
    return session, meta


def fetch_kite_ltp(ticker: str) -> float | None:
    base = _normalize_base(ticker)
    if base in _INDEX_TOKEN:
        kite_sym = "NSE:NIFTY 50" if base == "NIFTY" else f"NSE:{base}"
    else:
        kite_sym = yahoo_to_kite(f"{base}.NS")
    return get_ltp_by_kite_symbol(kite_sym, max_age_sec=2.0)
