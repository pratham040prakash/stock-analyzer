"""Indian market ticker resolution, aliases, indices, and search."""

from __future__ import annotations

import re

# Yahoo Finance index symbols for Indian benchmarks
INDIAN_INDICES = {
    "nifty50": {"symbol": "^NSEI", "name": "Nifty 50"},
    "sensex": {"symbol": "^BSESN", "name": "BSE Sensex"},
    "banknifty": {"symbol": "^NSEBANK", "name": "Nifty Bank"},
    "niftyit": {"symbol": "^CNXIT", "name": "Nifty IT"},
    "niftymidcap": {"symbol": "^NSEMDCP50", "name": "Nifty Midcap 50"},
    "indiavix": {"symbol": "^INDIAVIX", "name": "India VIX"},
}

# Common names / broker labels → NSE symbol (without .NS)
INDIAN_ALIASES: dict[str, str] = {
  # Popular shortcuts
    "SBI": "SBIN",
    "L&T": "LT",
    "LT": "LT",
    "HUL": "HINDUNILVR",
    "HDFC": "HDFCBANK",
    "HDFCBANK": "HDFCBANK",
    "HDFC BANK": "HDFCBANK",
    "ICICI": "ICICIBANK",
    "ICICI BANK": "ICICIBANK",
    "BAJAJ AUTO": "BAJAJ-AUTO",
    "BAJAJAUTO": "BAJAJ-AUTO",
    "M&M": "M&M",
    "MM": "M&M",
    "TATA MOTORS": "TMPV",
    "TATAMOTORS": "TMPV",
    "TATAMOTOR": "TMPV",
    "TATA STEEL": "TATASTEEL",
    "RELIANCE": "RELIANCE",
    "INFOSYS": "INFY",
    "INFY": "INFY",
    "TCS": "TCS",
    "WIPRO": "WIPRO",
    "HCL": "HCLTECH",
    "ADANI": "ADANIENT",
    "ADANI PORTS": "ADANIPORTS",
    "SUN PHARMA": "SUNPHARMA",
    "DR REDDY": "DRREDDY",
    "DRREDDYS": "DRREDDY",
    "ASIAN PAINTS": "ASIANPAINT",
    "MARUTI SUZUKI": "MARUTI",
    "HERO": "HEROMOTOCO",
    "HERO MOTOCORP": "HEROMOTOCO",
    "ULTRATECH": "ULTRACEMCO",
    "NTPC LTD": "NTPC",
    "POWER GRID": "POWERGRID",
    "COAL INDIA": "COALINDIA",
    "TITAN COMPANY": "TITAN",
    "AXIS": "AXISBANK",
    "KOTAK": "KOTAKBANK",
    "INDUSIND": "INDUSINDBK",
    "SHRIRAM": "SHRIRAMFIN",
    "BHEL": "BHEL",
}

# Post-demerger / renamed NSE symbols → current Yahoo ticker (base, no suffix)
NSE_SYMBOL_REDIRECT: dict[str, str] = {
    "TATAMOTORS": "TMPV",
    "TATAMOTOR": "TMPV",
    "TATA MOTORS": "TMPV",
}

# Nifty 50 constituents (NSE symbols, no suffix)
NIFTY_50 = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BHARTIARTL", "BEL",
    "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT",
    "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO",
    "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC", "INDUSINDBK",
    "INFY", "JSWSTEEL", "KOTAKBANK", "LT", "M&M",
    "MARUTI", "NTPC", "NESTLEIND", "ONGC", "POWERGRID",
    "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA", "TCS",
    "TATACONSUM", "TMPV", "TATASTEEL", "TECHM", "TITAN",
    "TRENT", "ULTRACEMCO", "WIPRO", "SHRIRAMFIN", "JIOFIN",
]

# Popular Indian ETFs on NSE
INDIAN_ETFS = [
    "NIFTYBEES.NS", "BANKBEES.NS", "JUNIORBEES.NS", "ITBEES.NS",
    "GOLDBEES.NS", "LIQUIDBEES.NS", "SETFNIF50.NS",
]

# BSE scrip code → NSE symbol (for users who have BSE codes from BSE website)
BSE_SCRIP_TO_NSE: dict[str, str] = {
    "500325": "RELIANCE",
    "532540": "TCS",
    "500209": "INFY",
    "500180": "HDFCBANK",
    "532174": "ICICIBANK",
    "500112": "SBIN",
    "500875": "ITC",
    "532454": "BHARTIARTL",
    "500247": "KOTAKBANK",
    "500510": "LT",
    "500696": "HINDUNILVR",
    "532500": "MARUTI",
    "500820": "ASIANPAINT",
    "532215": "AXISBANK",
    "500570": "TMPV",
    "533096": "ADANIENT",
    "532755": "TECHM",
}

# NSE series suffixes to strip (EQ = equity regular, BE = trade-to-trade, etc.)
_NSE_SERIES_RE = re.compile(r"-(EQ|BE|BL|BZ|SM|ST|IV|RR|GD|GS)$", re.IGNORECASE)
_EXCHANGE_PREFIX_RE = re.compile(r"^(NSE|BSE|NSEI|IN|INE|INR)[:\s]+", re.IGNORECASE)
_BSE_NUMERIC_RE = re.compile(r"^\d{6}$")


def is_indian_ticker(ticker: str) -> bool:
    """Return True if ticker looks like an Indian NSE/BSE symbol."""
    t = ticker.strip().upper()
    if t.endswith(".NS") or t.endswith(".BO"):
        return True
    if t.startswith("^") and t in {v["symbol"] for v in INDIAN_INDICES.values()}:
        return True
    if _BSE_NUMERIC_RE.match(t):
        return True
    if t in INDIAN_ALIASES or t in NIFTY_50:
        return True
  # Index shortcuts
    if t in INDIAN_INDICES or t.replace(" ", "") in {"NIFTY50", "SENSEX", "BANKNIFTY"}:
        return True
    return False


def _clean_raw_input(ticker: str) -> str:
    """Normalize user input: strip exchange prefixes, series suffixes, whitespace."""
    t = ticker.strip().upper()
    t = _EXCHANGE_PREFIX_RE.sub("", t)
    t = t.replace(" ", "")
    # RELIANCENS → RELIANCE.NS style (some users type without dot)
    if t.endswith("NS") and not t.endswith(".NS") and len(t) > 2:
        t = t[:-2] + ".NS"
    elif t.endswith("BO") and not t.endswith(".BO") and len(t) > 2:
        t = t[:-2] + ".BO"
    t = _NSE_SERIES_RE.sub("", t)
    return t


def _resolve_index(ticker: str) -> str | None:
    key = ticker.lower().replace(" ", "").replace("^", "")
    mapping = {
        "nifty50": "nifty50", "nifty": "nifty50",
        "sensex": "sensex",
        "banknifty": "banknifty", "niftybank": "banknifty",
        "niftyit": "niftyit",
        "niftymidcap": "niftymidcap",
    }
    if key in mapping:
        return INDIAN_INDICES[mapping[key]]["symbol"]
    if ticker.startswith("^"):
        return ticker
    return None


def resolve_indian_candidates(ticker: str, market: str = "india") -> list[str]:
    """
    Build an ordered list of Yahoo Finance symbols to try for Indian stocks.

    market: 'india' (NSE then BSE), 'nse', 'bse'
    """
    raw = _clean_raw_input(ticker)
    if not raw:
        return []

    # Index
    idx = _resolve_index(raw)
    if idx:
        return [idx]

    candidates: list[str] = []

    # Already fully qualified
    if raw.endswith(".NS") or raw.endswith(".BO"):
        candidates.append(raw)
        base = raw.rsplit(".", 1)[0]
    elif raw.startswith("^"):
        return [raw]
    elif _BSE_NUMERIC_RE.match(raw):
        # BSE scrip code — try mapped NSE first, then .BO
        nse_sym = BSE_SCRIP_TO_NSE.get(raw)
        if nse_sym:
            candidates.append(f"{nse_sym}.NS")
        candidates.append(f"{raw}.BO")
        return _dedupe(candidates)
    else:
        base = raw

    # Apply alias map
    base = INDIAN_ALIASES.get(base, base)
    base = NSE_SYMBOL_REDIRECT.get(base, base)

    if market == "bse":
        candidates.append(f"{base}.BO")
        if base in BSE_SCRIP_TO_NSE.values():
            for code, sym in BSE_SCRIP_TO_NSE.items():
                if sym == base:
                    candidates.append(f"{code}.BO")
    elif market == "nse":
        candidates.append(f"{base}.NS")
    else:
        # india auto: NSE preferred (better liquidity & data on Yahoo)
        candidates.append(f"{base}.NS")
        candidates.append(f"{base}.BO")
        # BSE scrip fallback
        for code, sym in BSE_SCRIP_TO_NSE.items():
            if sym == base:
                candidates.append(f"{code}.BO")

    return _dedupe(candidates)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def detect_market_from_ticker(ticker: str) -> str:
    """Auto-detect market: us | nse | bse | india."""
    t = ticker.strip().upper()
    if t.endswith(".NS") or t in NIFTY_50 or t in INDIAN_ALIASES:
        return "nse" if t.endswith(".NS") or not t.endswith(".BO") else "india"
    if t.endswith(".BO") or _BSE_NUMERIC_RE.match(t):
        return "bse"
    if is_indian_ticker(ticker):
        return "india"
    if t.startswith("^") and t in {v["symbol"] for v in INDIAN_INDICES.values()}:
        return "india"
    return "us"


def search_indian_stocks(query: str, max_results: int = 10) -> list[dict]:
    """
    Search Indian stocks by company name or symbol using Yahoo Finance.
    Returns list of {symbol, name, exchange}.
    """
    try:
        from yfinance import Search

        results = Search(query, max_results=max_results * 3)
        out: list[dict] = []
        for q in results.quotes:
            symbol = q.get("symbol", "")
            if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
                continue
            out.append(
                {
                    "symbol": symbol,
                    "name": q.get("shortname") or q.get("longname") or symbol,
                    "exchange": "NSE" if symbol.endswith(".NS") else "BSE",
                }
            )
            if len(out) >= max_results:
                break
        return out
    except Exception:
        return []


def indian_ticker_help() -> str:
    """Return user-facing help for Indian ticker formats."""
    return """
**Supported Indian ticker formats (Yahoo Finance):**

| How you type it | Resolved to |
|-----------------|-------------|
| `RELIANCE` | `RELIANCE.NS` (NSE, preferred) |
| `RELIANCE.NS` | NSE directly |
| `RELIANCE.BO` | BSE directly |
| `SBI` | `SBIN.NS` (alias) |
| `L&T` or `LT` | `LT.NS` |
| `M&M` | `M&M.NS` |
| `BAJAJ AUTO` | `BAJAJ-AUTO.NS` |
| `NSE:RELIANCE` | `RELIANCE.NS` (prefix stripped) |
| `RELIANCE-EQ` | `RELIANCE.NS` (series stripped) |
| `500325` (BSE code) | `RELIANCE.NS` or `500325.BO` |
| `NIFTY50` / `^NSEI` | Nifty 50 index |
| `SENSEX` / `^BSESN` | BSE Sensex index |

**Tips for Indian investing:**
- **NSE (`.NS`)** is preferred — better data & liquidity on Yahoo Finance
- Use **Search** in the sidebar to find symbols by company name
- BSE scrip codes (6 digits) work for some stocks but NSE symbols are more reliable
- Market mode **India (Auto)** tries NSE first, then BSE
"""
