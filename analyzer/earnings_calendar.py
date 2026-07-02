"""Upcoming earnings and corporate events — risk bands and trading guidance."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import yfinance as yf

from analyzer.cache_utils import cached_compute

IST = ZoneInfo("Asia/Kolkata")
EARNINGS_CACHE_TTL = 86_400  # 24h — dates change slowly


@dataclass
class CorporateEvent:
    symbol: str
    nse_symbol: str
    name: str
    event_type: str
    date: str  # YYYY-MM-DD
    detail: str
    days_until: int | None = None
    risk_band: str = "unknown"  # critical | elevated | watch | clear | past
    guidance: str = ""


def _today_ist() -> date:
    return datetime.now(IST).date()


def _parse_event_date(raw) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw, tz=IST).date()
        except (OSError, ValueError, OverflowError):
            return None
    text = str(raw).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _days_until(event_date: date | None) -> int | None:
    if event_date is None:
        return None
    return (event_date - _today_ist()).days


def _risk_band(days: int | None, event_type: str) -> str:
    if days is None:
        return "unknown"
    if days < 0:
        return "past"
    if event_type.lower().startswith("ex-div"):
        return "watch" if days <= 7 else "clear"
    if days == 0:
        return "critical"
    if days <= 3:
        return "critical"
    if days <= 7:
        return "elevated"
    if days <= 14:
        return "watch"
    return "clear"


def trading_guidance(days: int | None, horizon: str = "all") -> str:
    """Plain-language guidance for long-term / swing / options."""
    if days is None:
        return "Earnings date unknown — verify on NSE/BSE before sizing up."
    if days < 0:
        return "Results recently reported — read outcome before adding size."
    if days == 0:
        return "Results today — avoid new intraday/options; long-term wait for clarity."
    if days <= 3:
        if horizon == "intraday":
            return f"Results in {days}d — skip MIS; gap risk and IV crush."
        if horizon == "options":
            return f"Results in {days}d — IV elevated; prefer spreads or wait."
        if horizon == "long":
            return f"Results in {days}d — wait for report; add after trend confirms."
        return f"Results in {days}d — reduce size; avoid new swing/options entries."
    if days <= 7:
        if horizon == "options":
            return f"Results in {days}d — IV may rise; avoid naked long premium."
        return f"Results in {days}d — tighten stops; plan entry after event."
    if days <= 14:
        return f"Results in {days}d — on radar; check consensus estimates."
    return f"Results in {days}d — no immediate event risk."


def _enrich(event: CorporateEvent) -> CorporateEvent:
    ed = _parse_event_date(event.date)
    days = _days_until(ed)
    band = _risk_band(days, event.event_type)
    date_str = ed.isoformat() if ed else event.date
    return CorporateEvent(
        symbol=event.symbol,
        nse_symbol=event.nse_symbol,
        name=event.name,
        event_type=event.event_type,
        date=date_str,
        detail=event.detail,
        days_until=days,
        risk_band=band,
        guidance=trading_guidance(days),
    )


def _extract_earnings_date(t: yf.Ticker, info: dict) -> date | None:
    for key in ("earningsTimestamp", "earningsTimestampStart", "earningsTimestampEnd"):
        d = _parse_event_date(info.get(key))
        if d and d >= _today_ist() - timedelta(days=1):
            return d

    cal = getattr(t, "calendar", None)
    if cal is not None:
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date") or cal.get("earningsDate")
            if isinstance(ed, (list, tuple)) and ed:
                ed = ed[0]
            d = _parse_event_date(ed)
            if d:
                return d
        elif hasattr(cal, "index") and "Earnings Date" in cal.index:
            d = _parse_event_date(cal.loc["Earnings Date"])
            if d:
                return d

    try:
        earnings_dates = t.get_earnings_dates(limit=4)
        if earnings_dates is not None and not earnings_dates.empty:
            for idx in earnings_dates.index:
                d = _parse_event_date(idx)
                if d and d >= _today_ist() - timedelta(days=1):
                    return d
    except Exception:
        pass
    return None


def fetch_corporate_event(raw_symbol: str, market: str = "india") -> CorporateEvent | None:
    """Next earnings or ex-dividend event for one symbol."""
    from analyzer.markets import resolve_ticker

    try:
        candidates = resolve_ticker(raw_symbol.strip(), market)
        sym = candidates[0] if candidates else raw_symbol.strip().upper()
        nse = sym.replace(".NS", "").replace(".BO", "").upper()
        t = yf.Ticker(sym)
        info = t.info or {}
        name = info.get("shortName") or info.get("longName") or nse

        earnings_d = _extract_earnings_date(t, info)
        if earnings_d:
            return _enrich(CorporateEvent(
                symbol=sym,
                nse_symbol=nse,
                name=name,
                event_type="Earnings",
                date=earnings_d.isoformat(),
                detail="Quarterly results (Yahoo/NSE)",
            ))

        ex_div = _parse_event_date(info.get("exDividendDate"))
        if ex_div and (du := _days_until(ex_div)) is not None and du >= 0:
            return _enrich(CorporateEvent(
                symbol=sym,
                nse_symbol=nse,
                name=name,
                event_type="Ex-dividend",
                date=ex_div.isoformat(),
                detail="Ex-dividend date",
            ))
    except Exception:
        return None
    return None


def fetch_corporate_events(symbols: list[str], market: str = "india") -> list[CorporateEvent]:
    """Batch fetch — best-effort earnings dates."""
    events: list[CorporateEvent] = []
    seen: set[str] = set()
    for raw in symbols[:30]:
        nse = raw.replace(".NS", "").replace(".BO", "").upper()
        if nse in seen:
            continue
        seen.add(nse)
        ev = fetch_corporate_event(raw, market)
        if ev:
            events.append(ev)

    events.sort(key=lambda e: (e.days_until is None, e.days_until or 9999, e.date))
    return events


def _fetch_universe_events(universe: list[str], market: str) -> list[CorporateEvent]:
    events: list[CorporateEvent] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(fetch_corporate_event, sym, market): sym for sym in universe}
        for fut in as_completed(futs):
            ev = fut.result()
            if ev:
                events.append(ev)
    events.sort(key=lambda e: (e.days_until is None, e.days_until or 9999, e.date))
    return events


def fetch_nifty50_earnings(
    universe: list[str] | None = None,
    market: str = "india",
) -> list[CorporateEvent]:
    """Cached earnings calendar for Nifty 50 universe."""
    from analyzer.india import NIFTY_50

    symbols = universe or list(NIFTY_50)
    key = f"earnings_{market}_{len(symbols)}"
    return cached_compute(key, EARNINGS_CACHE_TTL, lambda: _fetch_universe_events(symbols, market))


def events_by_nse(events: list[CorporateEvent]) -> dict[str, CorporateEvent]:
    return {e.nse_symbol.upper(): e for e in events}


def upcoming_within_days(events: list[CorporateEvent], days: int = 14) -> list[CorporateEvent]:
    return [
        e for e in events
        if e.days_until is not None and 0 <= e.days_until <= days and e.event_type == "Earnings"
    ]


def earnings_note_for_pick(event: CorporateEvent | None, horizon: str) -> str:
    if not event or event.event_type != "Earnings":
        return ""
    if event.days_until is None:
        return ""
    if event.days_until < 0:
        return ""
    if event.days_until <= 7:
        return trading_guidance(event.days_until, horizon)
    return ""


def should_skip_pick(
    event: CorporateEvent | None,
    horizon: str,
    *,
    skip_earnings_week: bool,
) -> bool:
    if not skip_earnings_week or not event or event.event_type != "Earnings":
        return False
    if event.days_until is None:
        return False
    if horizon == "intraday":
        return event.days_until <= 3
    if horizon == "short":
        return event.days_until <= 5
    return False


def event_to_dict(e: CorporateEvent) -> dict:
    return {
        "symbol": e.symbol,
        "nse_symbol": e.nse_symbol,
        "name": e.name,
        "event_type": e.event_type,
        "date": e.date,
        "detail": e.detail,
        "days_until": e.days_until,
        "risk_band": e.risk_band,
        "guidance": e.guidance,
    }


def event_from_dict(d: dict) -> CorporateEvent:
    return CorporateEvent(**d)
