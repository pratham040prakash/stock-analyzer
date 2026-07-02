"""Scan multiple tickers and rank by signal strength."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from analyzer.combined import analyze_combined
from analyzer.data import fetch_stock_data
from analyzer.indicators import add_indicators


@dataclass
class WatchlistRow:
    ticker: str
    name: str
    price: float
    recommendation: str  # combined recommendation
    score: float  # combined score
    technical_score: float
    fundamental_score: float
    confidence: str
    error: str | None = None


def _scan_one(ticker: str, period: str, market: str, enrich_nse: bool = False) -> WatchlistRow:
    try:
        df, info = fetch_stock_data(ticker, period=period, market=market, enrich_nse=enrich_nse)
        df = add_indicators(df)
        combined = analyze_combined(df, info["symbol"], yf_info=info)
        return WatchlistRow(
            ticker=info["symbol"],
            name=info["name"],
            price=combined.technical.current_price,
            recommendation=combined.combined_recommendation,
            score=combined.combined_score,
            technical_score=combined.technical.composite_score,
            fundamental_score=combined.fundamental.composite_score,
            confidence=combined.technical.confidence,
        )
    except Exception as exc:
        return WatchlistRow(
            ticker=ticker,
            name=ticker,
            price=0.0,
            recommendation="ERROR",
            score=0.0,
            technical_score=0.0,
            fundamental_score=0.0,
            confidence="low",
            error=str(exc),
        )


def scan_watchlist(
    tickers: list[str],
    period: str = "1y",
    market: str = "us",
    max_workers: int = 6,
) -> list[WatchlistRow]:
    """Analyze multiple tickers with technical + fundamental scoring (parallel)."""
    if not tickers:
        return []

    rows: list[WatchlistRow] = []
    workers = min(max_workers, max(1, len(tickers)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_scan_one, t, period, market): t for t in tickers}
        for fut in as_completed(futures):
            rows.append(fut.result())

    rows.sort(key=lambda r: (r.error is not None, -r.score))
    return rows
