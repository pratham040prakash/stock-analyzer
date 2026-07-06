"""Verify all Kite Connect APIs used by the stock analyzer."""

from __future__ import annotations

from datetime import datetime, timedelta

from analyzer.market_session import IST
from analyzer.kite_status import probe_kite_market_data
from analyzer.zerodha import fetch_kite_ltp, fetch_kite_margins, get_kite_client, load_env_credentials


def check_kite_apis() -> dict:
    """
    Test profile, holdings, margins, quotes, historical candles, instruments.
    Returns {ok, checks: [{name, ok, detail}], errors: []}
    """
    creds = load_env_credentials()
    checks: list[dict] = []
    errors: list[str] = []

    if not creds.get("api_key"):
        return {"ok": False, "checks": [], "errors": ["ZERODHA_API_KEY missing in .env"]}
    if not creds.get("api_secret"):
        errors.append("ZERODHA_API_SECRET missing in .env")
    if not creds.get("access_token"):
        errors.append("ZERODHA_ACCESS_TOKEN missing — run: python scripts/kite_auth.py login")

    kite = get_kite_client()
    if kite is None:
        errors.append("Kite client unavailable (invalid or expired access token)")
        return {"ok": False, "checks": checks, "errors": errors}

    def _check(name: str, fn) -> None:
        try:
            detail = fn()
            checks.append({"name": name, "ok": True, "detail": str(detail)})
        except Exception as exc:
            msg = str(exc)
            checks.append({"name": name, "ok": False, "detail": msg[:200]})
            errors.append(f"{name}: {msg[:120]}")

    _check("profile", lambda: kite.profile().get("user_name", "OK"))
    _check("holdings", lambda: f"{len(kite.holdings())} rows")
    _check("margins", lambda: f"available ₹{fetch_kite_margins().get('net', 0):,.0f}" if fetch_kite_margins() else "—")

    ltp = fetch_kite_ltp(["NSE:RELIANCE-EQ", "NSE:NIFTY 50"])
    market = probe_kite_market_data(force=True)
    if ltp:
        checks.append({
            "name": "quote_ltp",
            "ok": True,
            "detail": ", ".join(f"{k}=₹{v:,.2f}" for k, v in ltp.items()),
        })
    elif market == "no_permission":
        checks.append({
            "name": "quote_ltp",
            "ok": False,
            "detail": "Insufficient permission — Kite Connect market data subscription required",
        })
        errors.append("quote_ltp: market data API not subscribed (₹500/mo)")
    else:
        checks.append({"name": "quote_ltp", "ok": False, "detail": "no quotes returned"})
        errors.append("quote_ltp: failed")

    def _historical() -> str:
        now = datetime.now(IST)
        raw = kite.historical_data(738561, now - timedelta(days=2), now, "5minute")
        return f"{len(raw)} bars (RELIANCE 5m)"

    _check("historical_5m", _historical)

    def _instruments() -> str:
        nse = kite.instruments("NSE")
        return f"{len(nse)} NSE instruments"

    _check("instruments_nse", _instruments)

    ok = all(c["ok"] for c in checks) and not errors
    return {"ok": ok, "checks": checks, "errors": errors}
