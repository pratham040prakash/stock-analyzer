"""Live Kite portfolio + watchlist — LTP refresh, sync, streaming."""

from __future__ import annotations

from analyzer.kite_stream import get_kite_ltp_cached, start_kite_ticker_for_holdings
from analyzer.kite_watchlist_store import load_kite_watchlist, merge_kite_watchlist
from analyzer.portfolio_store import enrich_holding_pnl, portfolio_profile_key, save_portfolio
from analyzer.providers.router import get_live_ltp, is_kite_live
from analyzer.zerodha import (
    ZerodhaHolding,
    ZerodhaImportResult,
    fetch_holdings_from_kite,
    fetch_kite_activity_symbols,
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
        ltp = ltps.get(key) or h.last_price
        if ltp is None and h.yahoo_symbol:
            ltp, _ = get_live_ltp(h.yahoo_symbol, market="india")
        enriched.append(enrich_holding_pnl(h, ltp))
    return ZerodhaImportResult(
        holdings=enriched,
        errors=list(imp.errors),
        source=imp.source,
    )


def sync_watchlist_from_kite_activity(
    *,
    profile: str | None = None,
    holdings: ZerodhaImportResult | None = None,
) -> tuple[int, int, list[str]]:
    """
    Pull symbols from Kite positions/orders into the saved watchlist mirror.
    Skips symbols already in delivery holdings.
    """
    prof = profile or portfolio_profile_key()
    activity, errors = fetch_kite_activity_symbols()
    held = set()
    if holdings and holdings.holdings:
        held = {_holding_key(h) for h in holdings.holdings if h.quantity > 0}
    elif holdings is None:
        imp, _ = sync_holdings_from_kite()
        if imp and imp.holdings:
            held = {_holding_key(h) for h in imp.holdings if h.quantity > 0}

    new_symbols = [s for s in activity if s.upper().strip() not in held]
    added, total = merge_kite_watchlist(new_symbols, profile=prof)
    return added, total, errors


def post_kite_login_sync(*, profile: str | None = None) -> dict:
    """
    After OAuth redirect — verify profile and pull delivery holdings.
    Watchlist is not available via Kite API; use watchlist mirror in My Portfolio.
    """
    from analyzer.zerodha import fetch_kite_profile

    prof = profile or portfolio_profile_key()
    result: dict = {
        "user_name": "",
        "user_id": "",
        "holdings_count": 0,
        "holdings": None,
        "watchlist_added": 0,
        "watchlist_total": 0,
        "error": "",
        "watchlist_errors": [],
    }
    profile_data = fetch_kite_profile()
    if profile_data:
        result["user_name"] = str(profile_data.get("user_name") or "")
        result["user_id"] = str(profile_data.get("user_id") or "")
    elif load_env_credentials().get("access_token"):
        result["error"] = "Could not read Kite profile — token may be invalid."

    imp, err = sync_holdings_from_kite()
    if err and not imp:
        result["error"] = err if not result["error"] else f"{result['error']} {err}"
    elif imp:
        result["holdings"] = imp
        result["holdings_count"] = len(imp.holdings)
        if imp.holdings:
            save_portfolio(imp, profile=prof)
        added, total, wl_errors = sync_watchlist_from_kite_activity(profile=prof, holdings=imp)
        result["watchlist_added"] = added
        result["watchlist_total"] = total
        result["watchlist_errors"] = wl_errors
    return result


def sync_holdings_from_kite() -> tuple[ZerodhaImportResult | None, str]:
    """Fetch delivery holdings from Kite API."""
    creds = load_env_credentials()
    if not creds.get("api_key") or not creds.get("access_token"):
        return None, "Sign in to Zerodha to sync holdings."
    imp = fetch_holdings_from_kite(creds["api_key"], creds["access_token"])
    if imp.errors and not imp.holdings:
        return None, imp.errors[0]
    imp = refresh_holdings_ltp(imp)
    imp.source = "kite"
    return imp, ""


def hydrate_portfolio_from_kite(profile: str | None = None) -> tuple[ZerodhaImportResult | None, str]:
    """Fetch holdings from Kite and persist when logged in."""
    prof = profile or portfolio_profile_key()
    imp, err = sync_holdings_from_kite()
    if imp and imp.holdings:
        save_portfolio(imp, profile=prof)
        return imp, ""
    return None, err or "No holdings returned from Kite."


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
    if refresh_ltp and merged.holdings:
        merged = refresh_holdings_ltp(merged)
    return merged
