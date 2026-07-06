"""Lightweight Kite / NFO connection status for UI banners."""

from __future__ import annotations

from analyzer.zerodha import fetch_kite_ltp, get_kite_client, load_env_credentials


def kite_connection_status(*, probe: bool = True) -> dict:
    """
    Returns level: ok | missing | no_token | expired
    headline + detail for banners; portfolio_tab for fix link.
    """
    creds = load_env_credentials()
    if not creds.get("api_key"):
        return {
            "level": "missing",
            "headline": "Kite not configured",
            "detail": "Add ZERODHA_API_KEY to `.env` for live candles, LTP & NFO premium charts.",
            "nfo_ok": False,
        }
    if not creds.get("access_token"):
        return {
            "level": "no_token",
            "headline": "Kite login required",
            "detail": "Daily access token missing — live data & option premium charts need a fresh login.",
            "nfo_ok": False,
        }
    if not probe:
        return {
            "level": "ok",
            "headline": "Kite configured",
            "detail": "Token present — live data when market is open.",
            "nfo_ok": True,
        }

    kite = get_kite_client()
    if kite is None:
        return {
            "level": "expired",
            "headline": "Kite token expired",
            "detail": "Refresh login in **My Portfolio** (~10 sec) — needed for live LTP & NFO charts.",
            "nfo_ok": False,
        }

    ltp = fetch_kite_ltp(["NSE:RELIANCE-EQ", "NSE:NIFTY 50"])
    if not ltp:
        return {
            "level": "expired",
            "headline": "Kite token expired",
            "detail": "Refresh login in **My Portfolio** (~10 sec) — needed for live LTP & NFO charts.",
            "nfo_ok": False,
        }

    nfo_ok = False
    try:
        rows = [
            r for r in kite.instruments("NFO")
            if r.get("name") == "NIFTY" and r.get("instrument_type") == "FUT"
        ]
        if rows:
            rows.sort(key=lambda r: r.get("expiry"))
            sym = rows[0]["tradingsymbol"]
            nfo_ok = bool(fetch_kite_ltp([f"NFO:{sym}"]))
    except Exception:
        nfo_ok = False

    return {
        "level": "ok",
        "headline": "Kite live",
        "detail": (
            "Equity LTP active · NFO data OK"
            if nfo_ok
            else "Equity LTP active · NFO charts may use index fallback until market data loads"
        ),
        "nfo_ok": nfo_ok,
    }
