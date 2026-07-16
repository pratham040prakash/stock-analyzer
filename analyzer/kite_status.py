"""Kite Connect login + market-data permission status for UI and routing."""

from __future__ import annotations

import time

from analyzer.zerodha import fetch_kite_ltp, get_kite_client, load_env_credentials

_MARKET_PROBE_CACHE: tuple[float, str] | None = None
_PROBE_TTL = 300  # seconds

_MARKET_DATA_HINT = (
    "Login works, but **live quotes/candles** need a paid **Connect** app "
    "(₹500/mo at developers.kite.trade). Until then the app uses "
    "**Yahoo Finance** for prices."
)

_PERSONAL_APP_HINT = (
    "Your Kite app is type **Personal** (free). Personal apps can log in and "
    "fetch holdings, but **cannot** call quote/LTP/historical APIs — even if you "
    "added ₹500 credits. Create a **new Connect app** at "
    "[developers.kite.trade](https://developers.kite.trade) → **Create app** → "
    "type **Connect** → update `.env` with the new API key/secret → **Login with Zerodha**."
)


def _kite_basic_session_ok(kite) -> bool:
    try:
        kite.profile()
        return True
    except Exception:
        return False


def probe_kite_market_data(*, force: bool = False) -> str:
    """
    Probe whether quote API works (not just login).

    Returns: ok | personal_app | no_permission | expired | not_logged_in | not_configured
    """
    global _MARKET_PROBE_CACHE
    now = time.time()
    if not force and _MARKET_PROBE_CACHE and now - _MARKET_PROBE_CACHE[0] < _PROBE_TTL:
        return _MARKET_PROBE_CACHE[1]

    creds = load_env_credentials()
    if not creds.get("api_key"):
        status = "not_configured"
    elif not creds.get("access_token"):
        status = "not_logged_in"
    else:
        kite = get_kite_client()
        if kite is None:
            status = "expired"
        else:
            try:
                kite.quote([256265])  # NIFTY 50 index token
                status = "ok"
            except Exception as exc:
                msg = str(exc).lower()
                if "insufficient permission" in msg:
                    status = (
                        "personal_app"
                        if _kite_basic_session_ok(kite)
                        else "no_permission"
                    )
                elif "token" in msg or "session" in msg or "api_key" in msg:
                    status = "expired"
                else:
                    status = "no_permission"

    _MARKET_PROBE_CACHE = (now, status)
    return status


def kite_market_data_ok(*, force: bool = False) -> bool:
    return probe_kite_market_data(force=force) == "ok"


def kite_options_available(*, force: bool = False) -> bool:
    """True only when Kite can return NFO quotes (not login-only)."""
    return kite_market_data_ok(force=force)


def clear_kite_probe_cache() -> None:
    global _MARKET_PROBE_CACHE
    _MARKET_PROBE_CACHE = None


def kite_connection_status(*, probe: bool = True) -> dict:
    """
    Returns level: ok | limited | missing | no_token | expired
    headline + detail for banners; nfo_ok for options charts.
    """
    creds = load_env_credentials()
    if not creds.get("api_key"):
        return {
            "level": "missing",
            "headline": "Kite not configured",
            "detail": "Add ZERODHA_API_KEY to `.env` / Streamlit secrets.",
            "nfo_ok": False,
            "market_data": "not_configured",
        }
    if not creds.get("access_token"):
        return {
            "level": "no_token",
            "headline": "Broker not connected",
            "detail": "Sign in to Zerodha to sync your portfolio.",
            "nfo_ok": False,
            "market_data": "not_logged_in",
        }
    if not probe:
        return {
            "level": "ok",
            "headline": "Kite configured",
            "detail": "Token present.",
            "nfo_ok": False,
            "market_data": "unknown",
        }

    kite = get_kite_client()
    if kite is None:
        return {
            "level": "expired",
            "headline": "Session expired",
            "detail": "Reconnect to Zerodha to refresh your portfolio.",
            "nfo_ok": False,
            "market_data": "expired",
        }

    market = probe_kite_market_data()
    if market == "personal_app":
        return {
            "level": "limited",
            "headline": "Personal API app — no live quotes",
            "detail": _PERSONAL_APP_HINT,
            "nfo_ok": False,
            "market_data": market,
        }
    if market == "no_permission":
        return {
            "level": "limited",
            "headline": "Kite logged in — no market data API",
            "detail": (
                f"{_MARKET_DATA_HINT} If you already paid, **re-login** after subscribing "
                "or confirm the API key is from a **Connect** app (not Personal)."
            ),
            "nfo_ok": False,
            "market_data": market,
        }
    if market != "ok":
        return {
            "level": "expired",
            "headline": "Session expired",
            "detail": "Reconnect to Zerodha to refresh your portfolio.",
            "nfo_ok": False,
            "market_data": market,
        }

    nfo_ok = False
    try:
        from analyzer.kite_options_chain import load_nfo_instruments

        rows = [
            r for r in load_nfo_instruments()
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
            "Equity + NFO quotes active"
            if nfo_ok
            else "Equity quotes active · NFO uses NSE/Yahoo when needed"
        ),
        "nfo_ok": nfo_ok,
        "market_data": "ok",
    }
