"""Market presets, ticker normalization, and currency formatting."""

from __future__ import annotations

from analyzer.india import (
    INDIAN_ETFS,
    INDIAN_INDICES,
    NIFTY_50,
    detect_market_from_ticker,
    indian_ticker_help,
    is_indian_ticker,
    resolve_indian_candidates,
    search_indian_stocks,
)

MARKETS = {
    "us": {
        "label": "US (NYSE / NASDAQ)",
        "suffix": "",
        "currency": "USD",
        "symbol": "$",
    },
    "india": {
        "label": "India (Auto — NSE preferred)",
        "suffix": "",
        "currency": "INR",
        "symbol": "₹",
    },
    "nse": {
        "label": "India — NSE only",
        "suffix": ".NS",
        "currency": "INR",
        "symbol": "₹",
    },
    "bse": {
        "label": "India — BSE only",
        "suffix": ".BO",
        "currency": "INR",
        "symbol": "₹",
    },
}

PRESET_WATCHLISTS: dict[str, list[str]] = {
    "us_mega": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    "us_tech": ["AAPL", "MSFT", "NVDA", "AMD", "CRM", "ADBE", "ORCL"],
    "nse_nifty": [f"{s}.NS" for s in NIFTY_50[:15]],
    "nse_nifty_full": [f"{s}.NS" for s in NIFTY_50],
    "nse_it": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTIM.NS"],
    "nse_banks": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS",
        "AXISBANK.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS",
    ],
    "nse_pharma": [
        "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
        "APOLLOHOSP.NS", "LUPIN.NS", "TORNTPHARM.NS",
    ],
    "india_etfs": INDIAN_ETFS,
    "india_indices": [v["symbol"] for v in INDIAN_INDICES.values()],
}


def is_india_market(market: str) -> bool:
    return market in ("india", "nse", "bse")


def normalize_ticker(ticker: str, market: str = "us") -> str:
    """
    Normalize ticker for the selected market.
    For India modes, returns the first candidate (use resolve_ticker for fallback).
    """
    symbol = ticker.strip().upper()
    if not symbol:
        return symbol

    if is_india_market(market) or is_indian_ticker(symbol):
        candidates = resolve_indian_candidates(symbol, market if is_india_market(market) else "india")
        return candidates[0] if candidates else symbol

    suffix = MARKETS.get(market, MARKETS["us"])["suffix"]
    if suffix and not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        symbol = f"{symbol}{suffix}"
    return symbol


def resolve_ticker(ticker: str, market: str = "us") -> list[str]:
    """Return ordered list of Yahoo symbols to try."""
    symbol = ticker.strip().upper()
    if not symbol:
        return []

    if is_india_market(market) or is_indian_ticker(symbol):
        m = market if is_india_market(market) else detect_market_from_ticker(symbol)
        return resolve_indian_candidates(symbol, m if is_india_market(m) else "india")

    return [normalize_ticker(symbol, market)]


def parse_tickers(text: str, market: str = "us") -> list[str]:
    """Parse comma/newline-separated tickers into a normalized list."""
    raw = text.replace("\n", ",").split(",")
    seen: set[str] = set()
    result: list[str] = []
    for item in raw:
        symbol = normalize_ticker(item, market)
        if symbol and symbol not in seen:
            seen.add(symbol)
            result.append(symbol)
    return result


def currency_for_ticker(ticker: str) -> dict:
    """Infer currency display info from ticker suffix."""
    if ticker.endswith(".NS") or ticker.endswith(".BO") or ticker.startswith("^"):
        if ticker.startswith("^") and ticker not in {v["symbol"] for v in INDIAN_INDICES.values()}:
            return MARKETS["us"]
        return MARKETS["nse"]
    return MARKETS["us"]


def format_price(value: float | None, ticker: str) -> str:
    if value is None:
        return "N/A"
    cur = currency_for_ticker(ticker)
    sym = cur["symbol"]
    return f"{sym}{value:,.2f}"


def format_market_cap(value: float | None, ticker: str) -> str:
    if not value:
        return "N/A"
    cur = currency_for_ticker(ticker)
    sym = cur["symbol"]
    if value >= 1e12:
        return f"{sym}{value / 1e12:.2f}T"
    if value >= 1e9:
        return f"{sym}{value / 1e9:.2f}B"
    if value >= 1e7:  # Indian cos often in Cr — 1 Cr = 10M
        return f"{sym}{value / 1e7:.2f} Cr"
    if value >= 1e6:
        return f"{sym}{value / 1e6:.2f}M"
    return f"{sym}{value:,.0f}"
