"""Side-by-side stock comparison for investment decisions."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import pandas as pd

from analyzer.chart_horizon import analyze_long_term_chart, analyze_short_term_chart
from analyzer.combined import analyze_combined
from analyzer.data import fetch_benchmark, fetch_stock_data
from analyzer.delivery_quality import build_delivery_snapshot
from analyzer.indicators import add_indicators
from analyzer.markets import is_india_market
from analyzer.relative_strength import compute_relative_strength


@dataclass
class CompareRow:
    ticker: str
    name: str
    price: float
    combined_rec: str
    combined_score: float
    technical_score: float
    fundamental_score: float
    short_action: str
    short_score: float
    long_action: str
    long_score: float
    rsi: float | None
    pe: float | None
    roe: float | None
    rs_verdict: str
    alpha_3m: float | None
    delivery_pct: float | None
    sector: str
    error: str | None = None


def _safe_float(val) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _compare_one(ticker: str, period: str, market: str, bench_df, bench_info: dict) -> CompareRow:
    try:
        df, info = fetch_stock_data(ticker, period=period, market=market, enrich_nse=True)
        df = add_indicators(df)
        combined = analyze_combined(df, info["symbol"], yf_info=info)
        short_h = analyze_short_term_chart(df)
        long_h = analyze_long_term_chart(df, yf_info=info)

        row = df.iloc[-1]
        price = float(info.get("nse_last_price") or combined.technical.current_price)
        rsi = _safe_float(row.get("RSI_14"))
        raw = combined.fundamental.raw
        pe = _safe_float(raw.get("pe_trailing"))
        roe = _safe_float(raw.get("roe"))

        rs_verdict = "—"
        alpha_3m = None
        if bench_df is not None and len(bench_df) > 30:
            rs = compute_relative_strength(
                df, bench_df,
                benchmark_symbol=bench_info.get("symbol", "^NSEI"),
                benchmark_name=bench_info.get("name", "Benchmark"),
            )
            rs_verdict = rs.verdict
            for p in rs.periods:
                if p.label == "3 Months":
                    alpha_3m = p.alpha_pct
                    break

        delivery_pct = None
        if is_india_market(market) and info["symbol"].endswith(".NS"):
            snap = build_delivery_snapshot(info["symbol"], df=df, fetch_history=False)
            if snap:
                delivery_pct = snap.delivery_pct

        return CompareRow(
            ticker=info["symbol"],
            name=info.get("name", ticker),
            price=price,
            combined_rec=combined.combined_recommendation,
            combined_score=combined.combined_score,
            technical_score=combined.technical.composite_score,
            fundamental_score=combined.fundamental.composite_score,
            short_action=short_h.action,
            short_score=short_h.score,
            long_action=long_h.action,
            long_score=long_h.score,
            rsi=rsi,
            pe=pe,
            roe=roe,
            rs_verdict=rs_verdict,
            alpha_3m=alpha_3m,
            delivery_pct=delivery_pct,
            sector=str(info.get("sector") or ""),
        )
    except Exception as exc:
        return CompareRow(
            ticker=ticker,
            name=ticker,
            price=0.0,
            combined_rec="ERROR",
            combined_score=0.0,
            technical_score=0.0,
            fundamental_score=0.0,
            short_action="—",
            short_score=0.0,
            long_action="—",
            long_score=0.0,
            rsi=None,
            pe=None,
            roe=None,
            rs_verdict="—",
            alpha_3m=None,
            delivery_pct=None,
            sector="",
            error=str(exc),
        )


def compare_stocks(
    tickers: list[str],
    *,
    period: str = "1y",
    market: str = "india",
    max_workers: int = 4,
) -> list[CompareRow]:
    """Compare 2–4 stocks on scores, fundamentals, and relative strength."""
    uniq = list(dict.fromkeys(t.strip() for t in tickers if t.strip()))[:4]
    if not uniq:
        return []

    bench_df = bench_info = None
    try:
        bench_df, bench_info = fetch_benchmark(market, period)
    except Exception:
        pass

    rows: list[CompareRow] = []
    workers = min(max_workers, len(uniq))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {
            pool.submit(_compare_one, t, period, market, bench_df, bench_info or {}): t
            for t in uniq
        }
        for fut in as_completed(futs):
            rows.append(fut.result())

    order = {t: i for i, t in enumerate(uniq)}
    rows.sort(key=lambda r: (r.error is not None, -r.combined_score, order.get(r.ticker, 99)))
    return rows


def pick_winner(rows: list[CompareRow]) -> CompareRow | None:
    valid = [r for r in rows if not r.error]
    return valid[0] if valid else None
