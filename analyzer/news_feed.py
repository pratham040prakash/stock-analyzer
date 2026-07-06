"""Stock news — NSE corporate announcements + earnings calendar."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from analyzer.cache_utils import cached_compute
from analyzer.earnings_calendar import fetch_corporate_event
from analyzer.nse_session import is_nse_available, nse_fetch_json

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class NewsItem:
    title: str
    date: str
    source: str
    category: str  # FACT | event
    detail: str = ""


@dataclass
class StockNewsBundle:
    symbol: str
    items: list[NewsItem] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    sentiment_note: str = ""
    data_source: str = ""


def _nse_base(symbol: str) -> str:
    return re.sub(r"\.(NS|BO)$", "", symbol.upper().strip())


def _fetch_nse_announcements(nse_symbol: str, *, limit: int = 8) -> list[NewsItem]:
    if not is_nse_available():
        return []
    sym = _nse_base(nse_symbol)
    if not sym or sym.startswith("^"):
        return []

    to_d = datetime.now(IST).strftime("%d-%m-%Y")
    from_d = (datetime.now(IST) - timedelta(days=90)).strftime("%d-%m-%Y")
    data = nse_fetch_json(
        f"corporate-announcements?index=equities&from_date={from_d}&to_date={to_d}&symbol={sym}"
    )
    if not data:
        return []

    rows = data if isinstance(data, list) else data.get("data", data.get("items", []))
    items: list[NewsItem] = []
    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue
        desc = (row.get("desc") or row.get("subject") or row.get("headline") or "").strip()
        if not desc:
            continue
        items.append(
            NewsItem(
                title=desc[:200],
                date=str(row.get("an_dt") or row.get("date") or ""),
                source="NSE India",
                category="FACT",
                detail=str(row.get("attchmntText") or row.get("sm_name") or "")[:300],
            )
        )
    return items


def fetch_stock_news(symbol: str, *, market: str = "india") -> StockNewsBundle:
    """Aggregate verified news/events for a symbol."""
    cache_key = f"stock_news_{_nse_base(symbol)}_{market}"
    return cached_compute(cache_key, 3600, lambda: _build_stock_news(symbol, market=market))


def _build_stock_news(symbol: str, *, market: str) -> StockNewsBundle:
    items: list[NewsItem] = []
    facts: list[str] = []

    try:
        ev = fetch_corporate_event(symbol, market=market)
        if ev:
            facts.append(f"{ev.event_type}: {ev.detail} ({ev.risk_band})")
            items.append(
                NewsItem(
                    title=ev.event_type,
                    date="upcoming",
                    source="Yahoo calendar",
                    category="FACT",
                    detail=ev.detail,
                )
            )
    except Exception:
        pass

    if market in ("india", "nse", "bse") or symbol.upper().endswith((".NS", ".BO")):
        nse_items = _fetch_nse_announcements(symbol)
        items.extend(nse_items)
        for ni in nse_items[:3]:
            facts.append(f"{ni.date}: {ni.title}")

    if not facts:
        facts.append("No verified corporate announcements in the last 90 days (NSE/Yahoo).")

    sentiment = (
        "**Market sentiment (ESTIMATE):** Derived from price trend and index bias — not from news NLP."
        if items else "**Sentiment:** Insufficient news feed — rely on price action and filings."
    )

    sources = []
    if any(i.source == "NSE India" for i in items):
        sources.append("NSE announcements")
    if any(i.source == "Yahoo calendar" for i in items):
        sources.append("Yahoo earnings calendar")

    return StockNewsBundle(
        symbol=symbol,
        items=items,
        facts=facts,
        sentiment_note=sentiment,
        data_source=" · ".join(sources) if sources else "No live feed",
    )


def format_news_markdown(bundle: StockNewsBundle) -> str:
    lines = ["**Facts (verified feed):**"]
    for f in bundle.facts[:6]:
        lines.append(f"- {f}")
    if bundle.items:
        lines.append("\n**Recent announcements:**")
        for item in bundle.items[:5]:
            lines.append(f"- [{item.date}] {item.title} _(source: {item.source})_")
    lines.append(f"\n{bundle.sentiment_note}")
    lines.append("\n**Rumors / social:** Ignore unverified tips — check exchange filings.")
    return "\n".join(lines)
