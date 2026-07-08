"""Live Kite portfolio + watchlist — LTP refresh, sync, streaming."""

from __future__ import annotations

from analyzer.kite_stream import get_kite_ltp_cached, start_kite_ticker_for_holdings
from analyzer.kite_watchlist_store import load_kite_watchlist
from analyzer.portfolio_store import enrich_holding_pnl, portfolio_profile_key
from analyzer.providers.router import is_kite_live
from analyzer.zerodha import (
    ZerodhaHolding,
    ZerodhaImportResult,
    fetch_holdings_from_kite,
    kite_to_yahoo,
    load_env_credentials,
)


def _holding_key(h: ZerodhaHolding) -> str:
    return h.kite_symbol.upper().strip()


def refresh_holdings_ltp(
    imp: ZerodhaImportResult,
    *,
    max_age_sec: float = 5.0,
) -> ZerodhaImportResult:
    """Update last_price and P&L from Kite LTP cache / REST."""
    if not imp.holdings:
        return imp
    symbols = [h.kite_symbol for h in imp.holdings if h.kite_symbol]
    ltps = get_kite_ltp_cached(symbols, max_age_sec=max_age_sec)
    enriched: list[ZerodhaHolding] = []
    for h in imp.holdings:
        key = _holding_key(h)
        ltp = ltps.get(key)
        enriched.append(enrich_holding_pnl(h, ltp))
    return ZerodhaImportResult(
        holdings=enriched,
        errors=list(imp.errors),
        source=imp.source,
    )


def sync_holdings_from_kite() -> tuple[ZerodhaImportResult | None, str]:
    """Fetch delivery holdings from Kite API."""
    creds = load_env_credentials()
    if not creds.get("api_key") or not creds.get("access_token"):
        return None, "Connect Kite in the sidebar first."
    imp = fetch_holdings_from_kite(creds["api_key"], creds["access_token"])
    if imp.errors and not imp.holdings:
        return None, imp.errors[0]
    imp = refresh_holdings_ltp(imp)
    imp.source = "kite"
    return imp, ""


def watchlist_as_holdings(profile: str | None = None) -> list[ZerodhaHolding]:
    """Watchlist-only rows (qty 0) for analysis."""
    rows: list[ZerodhaHolding] = []
    for kite_sym in load_kite_watchlist(profile):
        base = kite_sym.split(":")[-1].replace("-EQ", "")
        rows.append(
            ZerodhaHolding(
                kite_symbol=kite_sym,
                tradingsymbol=base,
                exchange="NSE",
                quantity=0,
                yahoo_symbol=kite_to_yahoo(kite_sym),
            )
        )
    return rows


def merge_holdings_and_watchlist(
    imp: ZerodhaImportResult | None,
    *,
    profile: str | None = None,
) -> ZerodhaImportResult:
    """Holdings first; watchlist symbols not already held appear as watch-only."""
    holdings = list(imp.holdings) if imp and imp.holdings else []
    held = {_holding_key(h) for h in holdings}
    for w in watchlist_as_holdings(profile):
        if _holding_key(w) not in held:
            holdings.append(w)
            held.add(_holding_key(w))
    return ZerodhaImportResult(
        holdings=holdings,
        errors=list(imp.errors) if imp else [],
        source=imp.source if imp else "watchlist",
    )


def all_tracked_kite_symbols(
    imp: ZerodhaImportResult | None,
    *,
    profile: str | None = None,
) -> list[str]:
    merged = merge_holdings_and_watchlist(imp, profile=profile)
    return list(dict.fromkeys(h.kite_symbol for h in merged.holdings if h.kite_symbol))


def ensure_kite_stream_for_tracked(
    imp: ZerodhaImportResult | None = None,
    *,
    profile: str | None = None,
) -> bool:
    """Subscribe WebSocket to portfolio + watchlist symbols."""
    if not is_kite_live():
        return False
    syms = all_tracked_kite_symbols(imp, profile=profile)
    if not syms:
        return False
    return start_kite_ticker_for_holdings(syms)


def load_tracked_portfolio(
    imp: ZerodhaImportResult | None = None,
    *,
    profile: str | None = None,
    refresh_ltp: bool = True,
) -> ZerodhaImportResult:
    """Merged holdings + watchlist with optional live LTP."""
    prof = profile or portfolio_profile_key()
    merged = merge_holdings_and_watchlist(imp, profile=prof)
    if refresh_ltp and merged.holdings and is_kite_live():
        merged = refresh_holdings_ltp(merged)
    return merged
