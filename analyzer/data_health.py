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

    kite_live = bool(ds.get("kite_live_data"))
    warning = ""
    ok_live = kite_live

    if market_data == "personal_app":
        warning = kite_status.get("detail") or (
            "Personal Kite app cannot fetch live quotes — create a **Connect** app."
        )
        ok_live = False
    elif market_data == "no_permission":
        warning = (
            "Kite login OK but quote API blocked. Use a **Connect** app key "
            "and re-login after subscribing (~₹500/mo)."
        )
        ok_live = False
    elif kite_status.get("level") == "expired":
        warning = "Kite token **expired** — re-login before 9:15 AM IST."
        ok_live = False
    elif session.get("is_open") and not kite_live:
        warning = (
            "Live prices may lag **15–20 min** (Yahoo). "
            "Use a Kite **Connect** app for real-time cockpit."
        )
        ok_live = False
    elif not session.get("is_open") and not kite_live and creds.get("access_token"):
        warning = (
            "Market closed — fix Kite quotes before **9:15 AM** or tomorrow's "
            "cockpit will use Yahoo."
        )
        ok_live = False

    detail = kite_status.get("detail") or ds.get("upgrade_hint", "")

    return DataHealth(
        primary=ds.get("primary_intraday", "Yahoo Finance"),
        kite_logged_in=bool(ds.get("kite_configured")),
        kite_live=kite_live,
        kite_market_data=market_data,
        warning=warning,
        ok_for_live_cockpit=ok_live,
        detail=detail,
    )
