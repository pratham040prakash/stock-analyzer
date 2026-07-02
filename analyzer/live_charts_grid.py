"""Parallel live intraday chart scan — per-minute narrative + buy/sell hypothesis."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import pandas as pd

from analyzer.cache_utils import cached_compute, invalidate_memory_cache
from analyzer.candle_narrative import LiveChartVerdict, analyze_live_chart
from analyzer.india import NIFTY_50
from analyzer.intraday_data import fetch_intraday
from analyzer.intraday_signals import add_intraday_indicators, compute_trade_levels

NIFTY_10 = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY",
    "SBIN", "BHARTIARTL", "ITC", "LT", "AXISBANK",
]

INDEX_LIVE = [
    ("NIFTY", "^NSEI"),
    ("BANKNIFTY", "^NSEBANK"),
]

UNIVERSES: dict[str, list[str]] = {
    "Nifty 50": list(NIFTY_50),
    "Nifty 10 (fast)": list(NIFTY_10),
    "Indices": [s for s, _ in INDEX_LIVE],
}

ACTION_RANK = {
    "STRONG BUY": 5,
    "BUY": 4,
    "WAIT": 3,
    "SELL": 2,
    "STRONG SELL": 1,
    "ERROR": 0,
}


@dataclass
class LiveChartRow:
    symbol: str
    nse_symbol: str
    interval: str
    price: float
    action: str
    confidence: str
    score: float
    current_time: str
    candle_type: str
    minute_story: str
    hypothesis: str
    entry: float | None
    stop_loss: float | None
    target: float | None
    session_story: str
    verdict: LiveChartVerdict | None = None
    chart_df: pd.DataFrame | None = None
    error: str | None = None


@dataclass
class LiveChartsGridReport:
    universe: str
    interval: str
    session_date: str
    updated_at: str
    rows: list[LiveChartRow] = field(default_factory=list)
    buy_count: int = 0
    sell_count: int = 0
    wait_count: int = 0
    error_count: int = 0


def build_hypothesis(verdict: LiveChartVerdict) -> str:
    """Plain-language buy/sell hypothesis from live chart verdict."""
    intraday = verdict.intraday
    if not intraday:
        return verdict.summary

    entry, stop, target = compute_trade_levels(intraday, verdict.action)
    vwap = intraday.vwap
    or_h, or_l = intraday.opening_range_high, intraday.opening_range_low

    if verdict.action in ("STRONG BUY", "BUY") and entry is not None:
        return (
            f"**Bullish hypothesis:** Buyers control above VWAP ₹{vwap:,.2f}. "
            f"Consider long near ₹{entry:,.2f} with stop ₹{stop:,.2f} "
            f"(below OR low ₹{or_l:,.2f}). Target ₹{target:,.2f} if momentum continues."
        )
    if verdict.action in ("STRONG SELL", "SELL") and entry is not None:
        return (
            f"**Bearish hypothesis:** Sellers control below VWAP ₹{vwap:,.2f}. "
            f"Consider short/fade near ₹{entry:,.2f} with stop ₹{stop:,.2f} "
            f"(above OR high ₹{or_h:,.2f}). Target ₹{target:,.2f} on continuation."
        )
    return (
        f"**Neutral hypothesis:** Price is chopping between OR ₹{or_l:,.2f}–₹{or_h:,.2f} "
        f"and VWAP ₹{vwap:,.2f}. Wait for a Marubozu, engulfing, or OR breakout before entry."
    )


def _scan_one(symbol: str, interval: str, market: str = "india") -> LiveChartRow:
    nse = symbol.replace(".NS", "").replace(".BO", "").upper()
    try:
        df, meta = fetch_intraday(nse, interval=interval, market=market)
        verdict = analyze_live_chart(df, nse, interval)
        df_ind = add_intraday_indicators(df)
        cur = verdict.current_candle
        price = verdict.intraday.last_price if verdict.intraday else float(df["Close"].iloc[-1])

        return LiveChartRow(
            symbol=meta.get("symbol", f"{nse}.NS"),
            nse_symbol=nse,
            interval=interval,
            price=price,
            action=verdict.action,
            confidence=verdict.confidence,
            score=verdict.directional_score,
            current_time=cur.time if cur else "—",
            candle_type=cur.candle_type if cur else "—",
            minute_story=cur.story if cur else verdict.session_story,
            hypothesis=build_hypothesis(verdict),
            entry=verdict.entry,
            stop_loss=verdict.stop_loss,
            target=verdict.target,
            session_story=verdict.session_story,
            verdict=verdict,
            chart_df=df_ind,
        )
    except Exception as exc:
        return LiveChartRow(
            symbol=f"{nse}.NS",
            nse_symbol=nse,
            interval=interval,
            price=0.0,
            action="ERROR",
            confidence="low",
            score=0.0,
            current_time="—",
            candle_type="—",
            minute_story="",
            hypothesis="",
            entry=None,
            stop_loss=None,
            target=None,
            session_story="",
            error=str(exc),
        )


def _resolve_universe(name: str) -> list[str]:
    if name == "Indices":
        return [s for s, _ in INDEX_LIVE]
    return list(UNIVERSES.get(name, NIFTY_10))


def _yahoo_symbol(nse: str) -> str:
    for sym, yahoo in INDEX_LIVE:
        if sym == nse:
            return yahoo
    return nse


def _scan_parallel(symbols: list[str], interval: str, max_workers: int = 8) -> list[LiveChartRow]:
    rows: list[LiveChartRow] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_scan_one, _yahoo_symbol(s), interval): s
            for s in symbols
        }
        for fut in as_completed(futures):
            rows.append(fut.result())
    rows.sort(key=lambda r: (ACTION_RANK.get(r.action, 0), r.score), reverse=True)
    return rows


def _build_report(universe: str, interval: str) -> LiveChartsGridReport:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    symbols = _resolve_universe(universe)
    rows = _scan_parallel(symbols, interval)
    ist = ZoneInfo("Asia/Kolkata")
    now = datetime.now(ist)

    buy = sum(1 for r in rows if r.action in ("STRONG BUY", "BUY"))
    sell = sum(1 for r in rows if r.action in ("STRONG SELL", "SELL"))
    wait = sum(1 for r in rows if r.action == "WAIT")
    errors = sum(1 for r in rows if r.action == "ERROR")

    session_date = ""
    for r in rows:
        if r.chart_df is not None and len(r.chart_df):
            session_date = str(r.chart_df.index[-1].date())
            break

    return LiveChartsGridReport(
        universe=universe,
        interval=interval,
        session_date=session_date,
        updated_at=now.strftime("%H:%M:%S IST"),
        rows=rows,
        buy_count=buy,
        sell_count=sell,
        wait_count=wait,
        error_count=errors,
    )


def fetch_live_charts_grid(
    universe: str = "Nifty 10 (fast)",
    interval: str = "1m",
    cache_ttl: int = 60,
) -> LiveChartsGridReport:
    """Cached parallel scan (default 60s TTL for ~1 min refresh)."""
    key = f"live_grid_{universe}_{interval}"
    return cached_compute(key, cache_ttl, lambda: _build_report(universe, interval))


def clear_live_charts_cache() -> None:
    invalidate_memory_cache("live_grid_")
