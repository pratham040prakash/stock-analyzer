"""Data feed health — Kite vs Yahoo, stale warnings."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.kite_status import kite_connection_status, probe_kite_market_data
from analyzer.market_session import market_session_status
from analyzer.providers.router import data_source_status
from analyzer.zerodha import load_env_credentials


@dataclass
class DataHealth:
    primary: str
    kite_logged_in: bool
    kite_live: bool
    kite_market_data: str
    warning: str
    ok_for_live_cockpit: bool
    detail: str


def build_data_health(*, probe_kite: bool = False) -> DataHealth:
    ds = data_source_status()
    session = market_session_status()
    creds = load_env_credentials()
    market_data = probe_kite_market_data(force=probe_kite) if creds.get("access_token") else "not_logged_in"
    kite_status = kite_connection_status(probe=probe_kite)

    warning = ""
    ok_live = True
    if session.get("is_open") and not ds.get("kite_live_data"):
        warning = (
            "Live prices may lag **15–20 min** (Yahoo). "
            "Subscribe to Kite market data API for real-time cockpit."
        )
        ok_live = False
    if kite_status.get("level") == "expired":
        warning = "Kite token **expired** — re-login before 9:15 AM IST."
        ok_live = False

    detail = ds.get("upgrade_hint", "")
    if market_data == "no_permission":
        detail = "Kite logged in — enable **market data subscription** (~₹500/mo) for live quotes."

    return DataHealth(
        primary=ds.get("primary_intraday", "Yahoo Finance"),
        kite_logged_in=bool(ds.get("kite_configured")),
        kite_live=bool(ds.get("kite_live_data")),
        kite_market_data=market_data,
        warning=warning,
        ok_for_live_cockpit=ok_live,
        detail=detail,
    )
