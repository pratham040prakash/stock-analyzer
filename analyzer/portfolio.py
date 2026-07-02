"""Analyze Zerodha holdings with technical + fundamental signals."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.combined import analyze_combined
from analyzer.data import fetch_stock_data
from analyzer.indicators import add_indicators


@dataclass
class PortfolioRow:
    kite_symbol: str
    yahoo_symbol: str
    name: str
    quantity: float
    avg_price: float | None
    last_price: float | None
    pnl: float | None
    recommendation: str
    score: float
    technical_score: float
    fundamental_score: float
    confidence: str
    error: str | None = None


def analyze_portfolio(
    import_result,
    period: str = "1y",
) -> list[PortfolioRow]:
    """Run combined analysis on each Zerodha holding."""
    rows: list[PortfolioRow] = []

    for h in import_result.holdings:
        try:
            df, info = fetch_stock_data(h.yahoo_symbol, period=period, market="india", enrich_nse=False)
            df = add_indicators(df)
            combined = analyze_combined(df, info["symbol"], yf_info=info)
            last = combined.technical.current_price
            rows.append(
                PortfolioRow(
                    kite_symbol=h.kite_symbol,
                    yahoo_symbol=info["symbol"],
                    name=info["name"],
                    quantity=h.quantity,
                    avg_price=h.average_price,
                    last_price=h.last_price or last,
                    pnl=h.pnl,
                    recommendation=combined.combined_recommendation,
                    score=combined.combined_score,
                    technical_score=combined.technical.composite_score,
                    fundamental_score=combined.fundamental.composite_score,
                    confidence=combined.technical.confidence,
                )
            )
        except Exception as exc:
            rows.append(
                PortfolioRow(
                    kite_symbol=h.kite_symbol,
                    yahoo_symbol=h.yahoo_symbol,
                    name=h.tradingsymbol,
                    quantity=h.quantity,
                    avg_price=h.average_price,
                    last_price=h.last_price,
                    pnl=h.pnl,
                    recommendation="ERROR",
                    score=0.0,
                    technical_score=0.0,
                    fundamental_score=0.0,
                    confidence="low",
                    error=str(exc),
                )
            )

    rows.sort(key=lambda r: (r.error is not None, -r.score))
    return rows
