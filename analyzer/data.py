"""Fetch historical stock data via Yahoo Finance."""

from __future__ import annotations

import yfinance as yf
import pandas as pd

from analyzer.fundamentals import extract_raw_fundamentals
from analyzer.markets import currency_for_ticker, is_india_market, resolve_ticker
from analyzer.nse_data import enrich_info_with_nse
from analyzer.asset_class import assert_supported_equity

BENCHMARK_SYMBOLS = {"india": "^NSEI", "us": "^GSPC"}


def _fetch_single(symbol: str, period: str, enrich_nse: bool = True) -> tuple[pd.DataFrame, dict]:
    """Fetch data for one resolved Yahoo symbol."""
    stock = yf.Ticker(symbol)
    df = stock.history(period=period, auto_adjust=True)

    if df.empty:
        raise ValueError(f"No price data for '{symbol}'")

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index)

    raw_info = stock.info
    exchange = raw_info.get("exchange", "")
    if symbol.endswith(".NS"):
        exchange_label = "NSE"
    elif symbol.endswith(".BO"):
        exchange_label = "BSE"
    elif symbol.startswith("^"):
        exchange_label = "Index"
    else:
        exchange_label = exchange or "N/A"

    currency = raw_info.get("currency") or currency_for_ticker(symbol)["currency"]
    fundamentals = extract_raw_fundamentals(raw_info)
    info = {
        "symbol": symbol,
        "name": raw_info.get("longName") or raw_info.get("shortName") or symbol,
        "sector": raw_info.get("sector", "N/A"),
        "industry": raw_info.get("industry", "N/A"),
        "currency": currency,
        "exchange": exchange_label,
        "market_cap": raw_info.get("marketCap"),
        "pe_ratio": raw_info.get("trailingPE"),
        "dividend_yield": raw_info.get("dividendYield"),
        "fifty_two_week_high": raw_info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": raw_info.get("fiftyTwoWeekLow"),
        "isin": raw_info.get("isin"),
        "resolved_from": None,
        "data_sources": ["Yahoo Finance"],
        **fundamentals,
    }
    if symbol.endswith(".NS") and enrich_nse:
        info = enrich_info_with_nse(info)
    info["current_price"] = float(df["Close"].iloc[-1])
    info["quoteType"] = raw_info.get("quoteType")
    info["shares_outstanding"] = raw_info.get("sharesOutstanding")
    info["longName"] = raw_info.get("longName")
    info["shortName"] = raw_info.get("shortName")
    info["description"] = raw_info.get("longBusinessSummary")
    assert_supported_equity(symbol, raw_info)
    return df, info


def fetch_stock_data(
    ticker: str, period: str = "1y", market: str = "us", enrich_nse: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """
    Fetch OHLCV data and company info. For Indian tickers, tries NSE then BSE
  automatically when market is 'india' or ticker is recognized as Indian.
    """
    candidates = resolve_ticker(ticker, market)
    if not candidates:
        raise ValueError("Empty ticker symbol")

    errors: list[str] = []
    for symbol in candidates:
        try:
            df, info = _fetch_single(symbol, period, enrich_nse=enrich_nse)
            if ticker.strip().upper() != symbol:
                info["resolved_from"] = ticker.strip().upper()
            return df, info
        except Exception as exc:
            errors.append(f"{symbol}: {exc}")

    tried = ", ".join(candidates)
    raise ValueError(
        f"No data found for '{ticker}'. Tried: {tried}. "
        f"For Indian stocks use NSE symbol (e.g. RELIANCE, TCS) or suffix .NS/.BO."
    )


def fetch_nifty_context(period: str = "1y") -> tuple[pd.DataFrame, float] | None:
    """Fetch Nifty 50 index for market context. Returns (df, latest_close) or None."""
    try:
        df, _ = _fetch_single("^NSEI", period)
        return df, float(df["Close"].iloc[-1])
    except Exception:
        return None


def fetch_benchmark(market: str, period: str = "1y") -> tuple[pd.DataFrame, dict]:
    """Fetch benchmark index for relative strength (Nifty 50 or S&P 500)."""
    if is_india_market(market):
        sym = BENCHMARK_SYMBOLS["india"]
        name = "Nifty 50"
    else:
        sym = BENCHMARK_SYMBOLS["us"]
        name = "S&P 500"
    df, info = _fetch_single(sym, period)
    info["benchmark_name"] = name
    return df, info
