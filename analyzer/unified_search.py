"""Unified symbol search — name, ticker, ISIN."""

from __future__ import annotations

import re
from dataclasses import dataclass

from analyzer.india import INDIAN_ALIASES, NIFTY_50, resolve_indian_candidates, search_indian_stocks
from analyzer.markets import normalize_ticker

_ISIN_RE = re.compile(r"^INE[A-Z0-9]{9}$", re.IGNORECASE)


@dataclass
class SearchHit:
    symbol: str
    name: str
    exchange: str
    match_type: str  # symbol | name | isin | alias | tab
    detail: str = ""


TAB_ALIASES: dict[str, str] = {
    "unified": "Home",
    "home": "Home",
    "hub": "Home",
    "wealth": "Home",
    "10cr": "Home",
    "crore": "Home",
    "playbook": "Home",
    "suggestions": "Suggestions",
    "sugg": "Suggestions",
    "mis": "Suggestions",
    "intraday": "Suggestions",
    "track": "Track Record",
    "record": "Track Record",
    "hit": "Track Record",
    "alpha": "Alpha AI",
    "research": "Alpha AI",
    "stock": "Single Stock",
    "single": "Single Stock",
    "compare": "Compare",
    "pulse": "Market Pulse",
    "options": "NSE Options",
    "liveopt": "Live Options Coach",
    "coach": "Live Options Coach",
    "cepe": "Live Options Coach",
    "portfolio": "My Portfolio",
    "kite": "My Portfolio",
    "zerodha": "My Portfolio",
    "sip": "SIP & Goals",
    "risk": "Risk & Goals",
    "screener": "Screener",
    "penny": "Penny Picks",
    "backtest": "Backtest",
    "varsity": "Varsity TA",
    "charts": "Live Charts",
    "advisor": "Daily Advisor",
    "global": "Global Markets",
    "scanner": "Batch Scanner",
}


def match_tab_command(query: str) -> str | None:
    """Return nav tab name if query is a tab alias (optionally 'tab alpha')."""
    q = query.strip().lower()
    if q.startswith(">"):
        q = q[1:].strip()
    if q.startswith("tab "):
        q = q[4:].strip()
    parts = q.split()
    if not parts:
        return None
    return TAB_ALIASES.get(parts[0])


def extract_symbol_from_command(query: str) -> str | None:
    """Parse trailing symbol from 'alpha TCS' or '>single RELIANCE'."""
    q = query.strip()
    if q.startswith(">"):
        q = q[1:].strip()
    parts = q.split()
    if len(parts) < 2:
        return None
    if parts[0].lower() in TAB_ALIASES or parts[0].lower() == "tab":
        sym = parts[-1] if parts[0].lower() != "tab" else (parts[2] if len(parts) > 2 else None)
        return sym
    return None


def _isin_search(isin: str) -> list[SearchHit]:
    isin = isin.upper()
    try:
        from yfinance import Search

        results = Search(isin, max_results=5)
        out: list[SearchHit] = []
        for q in results.quotes:
            symbol = q.get("symbol", "")
            if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
                continue
            out.append(
                SearchHit(
                    symbol=symbol,
                    name=q.get("shortname") or q.get("longname") or symbol,
                    exchange="NSE" if symbol.endswith(".NS") else "BSE",
                    match_type="isin",
                    detail=f"ISIN {isin}",
                )
            )
        return out
    except Exception:
        return []


def unified_search(query: str, *, max_results: int = 10) -> list[SearchHit]:
    """Search stocks by symbol, company name, or ISIN."""
    q = query.strip()
    if not q or len(q) < 2:
        return []

    hits: list[SearchHit] = []
    upper = q.upper().replace(".NS", "").replace(".BO", "")

    if _ISIN_RE.match(q.replace(" ", "")):
        hits.extend(_isin_search(q.replace(" ", "").upper()))

    if upper in INDIAN_ALIASES:
        sym = normalize_ticker(INDIAN_ALIASES[upper], "india")
        hits.append(
            SearchHit(sym, INDIAN_ALIASES[upper], "NSE", "alias", "Known alias")
        )

    if upper in NIFTY_50:
        sym = normalize_ticker(upper, "india")
        hits.append(SearchHit(sym, upper, "NSE", "symbol", "Nifty 50"))

    for r in search_indian_stocks(q, max_results=max_results):
        hits.append(
            SearchHit(
                r["symbol"],
                r["name"],
                r.get("exchange", "NSE"),
                "name",
            )
        )

    # Direct ticker guess
    if len(upper) <= 12 and (upper.replace("&", "").isalnum() or "&" in upper):
        try:
            sym = normalize_ticker(q, "india")
            if sym and not any(h.symbol == sym for h in hits):
                hits.insert(
                    0,
                    SearchHit(sym, upper, "NSE", "symbol", "Direct ticker"),
                )
        except Exception:
            pass

    seen: set[str] = set()
    deduped: list[SearchHit] = []
    for h in hits:
        if h.symbol in seen:
            continue
        seen.add(h.symbol)
        deduped.append(h)
        if len(deduped) >= max_results:
            break
    return deduped
