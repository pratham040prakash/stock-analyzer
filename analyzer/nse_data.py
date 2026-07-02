"""NSE India official quote API — supplements Yahoo Finance for Indian stocks."""

from __future__ import annotations

import re

from analyzer.nse_session import is_nse_available, nse_fetch_json


def _nse_symbol(yahoo_symbol: str) -> str:
    """RELIANCE.NS -> RELIANCE"""
    s = yahoo_symbol.upper()
    return re.sub(r"\.(NS|BO)$", "", s)


def fetch_nse_quote(yahoo_symbol: str) -> dict | None:
    """
    Fetch live quote from NSE India official API.
    Returns dict with price, change, pe, sector, etc. or None on failure.
    """
    if not is_nse_available():
        return None

    symbol = _nse_symbol(yahoo_symbol)
    if symbol.startswith("^") or not symbol:
        return None

    data = nse_fetch_json(f"quote-equity?symbol={symbol}")
    if not data:
        return None

    price_info = data.get("priceInfo", {})
    metadata = data.get("metadata", {})
    security = data.get("info", {})

    return {
        "symbol": symbol,
        "source": "NSE India",
        "last_price": price_info.get("lastPrice"),
        "change_pct": price_info.get("pChange"),
        "open": price_info.get("open"),
        "high": price_info.get("intraDayHighLow", {}).get("max"),
        "low": price_info.get("intraDayHighLow", {}).get("min"),
        "previous_close": price_info.get("previousClose"),
        "year_high": price_info.get("weekHighLow", {}).get("max"),
        "year_low": price_info.get("weekHighLow", {}).get("min"),
        "sector": metadata.get("pdSectorInd") or security.get("industry"),
        "industry": metadata.get("pdIndustryInd") or security.get("industry"),
        "isin": security.get("isin"),
        "company_name": security.get("companyName"),
    }


def enrich_info_with_nse(info: dict) -> dict:
    """Merge NSE live data into stock info dict when available."""
    if not info.get("symbol", "").endswith(".NS"):
        return info

    nse = fetch_nse_quote(info["symbol"])
    if not nse:
        return info

    enriched = dict(info)
    enriched["data_sources"] = ["Yahoo Finance", "NSE India"]
    if nse.get("last_price"):
        enriched["nse_last_price"] = nse["last_price"]
    if nse.get("change_pct") is not None:
        enriched["nse_change_pct"] = nse["change_pct"]
    if nse.get("sector") and enriched.get("sector") in ("N/A", None):
        enriched["sector"] = nse["sector"]
    if nse.get("company_name") and not enriched.get("name"):
        enriched["name"] = nse["company_name"]
    if nse.get("year_high"):
        enriched["fifty_two_week_high"] = enriched.get("fifty_two_week_high") or nse["year_high"]
    if nse.get("year_low"):
        enriched["fifty_two_week_low"] = enriched.get("fifty_two_week_low") or nse["year_low"]
    return enriched
