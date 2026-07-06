"""Asset class detection — block unsupported instruments from equity analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass

from analyzer.india import INDIAN_ETFS

_CRYPTO_BASES = frozenset({
    "BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "BNB", "DOT", "MATIC", "AVAX",
    "SHIB", "LTC", "BCH", "LINK", "UNI", "ATOM",
})

_COMMODITY_PREFIXES = ("GC", "SI", "CL", "NG", "HG", "ZC", "ZW", "ALI")


@dataclass
class AssetClassInfo:
    asset_class: str  # equity | etf | index | crypto | forex | commodity | mutual_fund | unknown
    supported: bool
    message: str = ""


def _base_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    s = re.sub(r"\.(NS|BO)$", "", s)
    return s


def classify_asset(symbol: str, yf_info: dict | None = None) -> AssetClassInfo:
    """Classify ticker; equity and ETF are supported for analysis."""
    sym = symbol.upper().strip()
    base = _base_symbol(sym)
    info = yf_info or {}
    quote_type = (info.get("quoteType") or "").upper()

    if sym.startswith("^") or quote_type == "INDEX":
        return AssetClassInfo("index", True, "Index — technical context only.")

    if sym.endswith("=X") or quote_type == "CURRENCY":
        return AssetClassInfo(
            "forex",
            False,
            "Forex pairs are outside equity research scope. Use a dedicated FX platform.",
        )

    if sym.endswith("=F") or base in _COMMODITY_PREFIXES:
        return AssetClassInfo(
            "commodity",
            False,
            "Commodity futures are outside equity research scope.",
        )

    if "-USD" in sym or "-INR" in sym or base in _CRYPTO_BASES or quote_type == "CRYPTOCURRENCY":
        return AssetClassInfo(
            "crypto",
            False,
            "Cryptocurrency is not supported. Alpha AI covers listed equities and ETFs only.",
        )

    if quote_type == "MUTUALFUND":
        return AssetClassInfo(
            "mutual_fund",
            False,
            "Mutual funds are not fully supported — use the ETF equivalent if listed.",
        )

    etf_names = {e.replace(".NS", "").upper() for e in INDIAN_ETFS}
    if (
        quote_type == "ETF"
        or sym in INDIAN_ETFS
        or base in etf_names
        or "ETF" in (info.get("longName") or info.get("shortName") or "").upper()
    ):
        return AssetClassInfo("etf", True, "ETF — fund metrics apply, not stock DCF.")

    if quote_type in ("EQUITY", "EQUITY") or quote_type == "" or quote_type == "EQUITY":
        return AssetClassInfo("equity", True, "")

    return AssetClassInfo("equity", True, "")


def assert_supported_equity(symbol: str, yf_info: dict | None = None) -> AssetClassInfo:
    """Raise ValueError if asset class is not supported for equity research."""
    ac = classify_asset(symbol, yf_info)
    if not ac.supported:
        raise ValueError(ac.message)
    return ac
