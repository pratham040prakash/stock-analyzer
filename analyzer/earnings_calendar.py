"""Upcoming earnings and corporate events for watchlist / holdings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class CorporateEvent:
    symbol: str
    name: str
    event_type: str
    date: str
    detail: str


def fetch_corporate_events(symbols: list[str], market: str = "india") -> list[CorporateEvent]:
    """Best-effort earnings dates from Yahoo Finance."""
    from analyzer.markets import resolve_ticker

    events: list[CorporateEvent] = []
    for raw in symbols[:25]:
        try:
            candidates = resolve_ticker(raw, market)
            sym = candidates[0] if candidates else raw
            t = yf.Ticker(sym)
            info = t.info or {}
            name = info.get("shortName") or info.get("longName") or sym

            cal = getattr(t, "calendar", None)
            if cal is not None and not (hasattr(cal, "empty") and cal.empty):
                if isinstance(cal, dict):
                    ed = cal.get("Earnings Date") or cal.get("earningsDate")
                    if ed:
                        if isinstance(ed, (list, tuple)) and ed:
                            ed = ed[0]
                        events.append(CorporateEvent(
                            symbol=sym,
                            name=name,
                            event_type="Earnings",
                            date=str(ed)[:10],
                            detail="Upcoming results (Yahoo)",
                        ))
                elif hasattr(cal, "index"):
                    for idx in cal.index:
                        events.append(CorporateEvent(
                            symbol=sym,
                            name=name,
                            event_type=str(idx),
                            date=datetime.now(IST).strftime("%Y-%m-%d"),
                            detail=str(cal.loc[idx].values[0])[:80],
                        ))

            ex_div = info.get("exDividendDate")
            if ex_div:
                events.append(CorporateEvent(
                    symbol=sym,
                    name=name,
                    event_type="Ex-dividend",
                    date=str(ex_div)[:10],
                    detail="Ex-dividend date",
                ))
        except Exception:
            continue

    events.sort(key=lambda e: e.date)
    return events
