"""Fundamental analysis — valuation, profitability, growth, and financial health."""

from __future__ import annotations

from dataclasses import dataclass, field

import yfinance as yf


@dataclass
class FundamentalMetric:
    name: str
    value: str
    signal: str  # bullish | bearish | neutral
    score: float
    detail: str


@dataclass
class FundamentalResult:
    ticker: str
    recommendation: str
    composite_score: float  # -100 to +100
    metrics: list[FundamentalMetric] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


def _fmt_pct(val: float | None) -> str:
    if val is None:
        return "N/A"
    return f"{val * 100:.1f}%"


def _fmt_num(val: float | None, suffix: str = "") -> str:
    if val is None:
        return "N/A"
    return f"{val:,.2f}{suffix}"


def _pe_signal(pe: float | None) -> FundamentalMetric:
    if pe is None:
        return FundamentalMetric("P/E Ratio", "N/A", "neutral", 0.0, "No P/E data")
    if pe < 0:
        return FundamentalMetric("P/E Ratio", _fmt_num(pe), "bearish", -0.7, "Negative earnings — company is loss-making")
    if pe < 12:
        return FundamentalMetric("P/E Ratio", _fmt_num(pe), "bullish", 0.6, "Low P/E — potential value (verify quality)")
    if pe < 22:
        return FundamentalMetric("P/E Ratio", _fmt_num(pe), "neutral", 0.1, "P/E in reasonable range")
    if pe < 35:
        return FundamentalMetric("P/E Ratio", _fmt_num(pe), "bearish", -0.3, "Elevated P/E — growth must justify premium")
    return FundamentalMetric("P/E Ratio", _fmt_num(pe), "bearish", -0.6, "High P/E — expensive valuation")


def _roe_signal(roe: float | None) -> FundamentalMetric:
    if roe is None:
        return FundamentalMetric("ROE", "N/A", "neutral", 0.0, "No ROE data")
    pct = roe * 100
    if pct >= 20:
        return FundamentalMetric("ROE", f"{pct:.1f}%", "bullish", 0.8, "Strong return on equity")
    if pct >= 12:
        return FundamentalMetric("ROE", f"{pct:.1f}%", "bullish", 0.4, "Healthy ROE")
    if pct >= 5:
        return FundamentalMetric("ROE", f"{pct:.1f}%", "neutral", 0.0, "Average ROE")
    return FundamentalMetric("ROE", f"{pct:.1f}%", "bearish", -0.5, "Weak ROE — low capital efficiency")


def _debt_signal(de: float | None) -> FundamentalMetric:
    if de is None:
        return FundamentalMetric("Debt/Equity", "N/A", "neutral", 0.0, "No leverage data")
    if de < 0.3:
        return FundamentalMetric("Debt/Equity", _fmt_num(de), "bullish", 0.6, "Low debt — strong balance sheet")
    if de < 1.0:
        return FundamentalMetric("Debt/Equity", _fmt_num(de), "neutral", 0.1, "Moderate debt levels")
    if de < 2.0:
        return FundamentalMetric("Debt/Equity", _fmt_num(de), "bearish", -0.4, "High debt — monitor interest coverage")
    return FundamentalMetric("Debt/Equity", _fmt_num(de), "bearish", -0.7, "Very high leverage — financial risk")


def _growth_signal(label: str, growth: float | None) -> FundamentalMetric:
    if growth is None:
        return FundamentalMetric(label, "N/A", "neutral", 0.0, f"No {label.lower()} data")
    pct = growth * 100
    if pct >= 15:
        return FundamentalMetric(label, f"{pct:+.1f}%", "bullish", 0.7, f"Strong {label.lower()}")
    if pct >= 5:
        return FundamentalMetric(label, f"{pct:+.1f}%", "bullish", 0.3, f"Positive {label.lower()}")
    if pct >= -5:
        return FundamentalMetric(label, f"{pct:+.1f}%", "neutral", 0.0, f"Flat {label.lower()}")
    return FundamentalMetric(label, f"{pct:+.1f}%", "bearish", -0.5, f"Declining {label.lower()}")


def _margin_signal(margin: float | None) -> FundamentalMetric:
    if margin is None:
        return FundamentalMetric("Profit Margin", "N/A", "neutral", 0.0, "No margin data")
    pct = margin * 100
    if pct >= 20:
        return FundamentalMetric("Profit Margin", f"{pct:.1f}%", "bullish", 0.6, "High profitability")
    if pct >= 10:
        return FundamentalMetric("Profit Margin", f"{pct:.1f}%", "bullish", 0.3, "Good margins")
    if pct >= 0:
        return FundamentalMetric("Profit Margin", f"{pct:.1f}%", "neutral", 0.0, "Thin margins")
    return FundamentalMetric("Profit Margin", f"{pct:.1f}%", "bearish", -0.7, "Loss-making operations")


def _score_to_rec(score: float) -> str:
    if score >= 40:
        return "STRONG BUY"
    if score >= 15:
        return "BUY"
    if score <= -40:
        return "STRONG SELL"
    if score <= -15:
        return "SELL"
    return "HOLD"


def extract_raw_fundamentals(info: dict) -> dict:
    """Normalize fundamental fields from yfinance info dict."""
    return {
        "pe_trailing": info.get("trailingPE") or info.get("pe_trailing"),
        "pe_forward": info.get("forwardPE") or info.get("pe_forward"),
        "peg": info.get("pegRatio") or info.get("peg"),
        "roe": info.get("returnOnEquity") or info.get("roe"),
        "roa": info.get("returnOnAssets") or info.get("roa"),
        "debt_to_equity": info.get("debtToEquity") or info.get("debt_to_equity"),
        "profit_margin": info.get("profitMargins") or info.get("profit_margin"),
        "operating_margin": info.get("operatingMargins") or info.get("operating_margin"),
        "revenue_growth": info.get("revenueGrowth") or info.get("revenue_growth"),
        "earnings_growth": info.get("earningsGrowth") or info.get("earnings_growth"),
        "dividend_yield": info.get("dividendYield") or info.get("dividend_yield"),
        "price_to_book": info.get("priceToBook") or info.get("price_to_book"),
        "eps_trailing": info.get("trailingEps") or info.get("eps_trailing"),
        "eps_forward": info.get("forwardEps") or info.get("eps_forward"),
        "free_cashflow": info.get("freeCashflow") or info.get("free_cashflow"),
        "total_revenue": info.get("totalRevenue") or info.get("total_revenue"),
        "book_value": info.get("bookValue") or info.get("book_value"),
    }


def analyze_fundamentals(ticker: str, info: dict | None = None) -> FundamentalResult:
    """Score fundamentals from yfinance info (fetches if not provided)."""
    if info is None:
        info = yf.Ticker(ticker).info
    elif not info.get("trailingPE") and not info.get("pe_trailing"):
        # Partial info dict — fetch full fundamentals from Yahoo
        info = {**info, **yf.Ticker(ticker).info}

    raw = extract_raw_fundamentals(info)
    metrics = [
        _pe_signal(raw["pe_trailing"]),
        _roe_signal(raw["roe"]),
        _debt_signal(raw["debt_to_equity"]),
        _margin_signal(raw["profit_margin"]),
        _growth_signal("Revenue Growth", raw["revenue_growth"]),
        _growth_signal("Earnings Growth", raw["earnings_growth"]),
    ]

    if raw["peg"] is not None and raw["peg"] > 0:
        peg = raw["peg"]
        if peg < 1:
            m = FundamentalMetric("PEG Ratio", _fmt_num(peg), "bullish", 0.5, "PEG < 1 — growth at reasonable price")
        elif peg < 2:
            m = FundamentalMetric("PEG Ratio", _fmt_num(peg), "neutral", 0.0, "PEG in fair range")
        else:
            m = FundamentalMetric("PEG Ratio", _fmt_num(peg), "bearish", -0.4, "PEG > 2 — paying premium for growth")
        metrics.append(m)

    weights = {
        "P/E Ratio": 1.2,
        "ROE": 1.3,
        "Debt/Equity": 1.1,
        "Profit Margin": 1.0,
        "Revenue Growth": 1.2,
        "Earnings Growth": 1.2,
        "PEG Ratio": 1.0,
    }
    total_w = sum(weights.get(m.name, 1.0) for m in metrics)
    score = sum(m.score * weights.get(m.name, 1.0) for m in metrics) / total_w * 100

    return FundamentalResult(
        ticker=ticker,
        recommendation=_score_to_rec(score),
        composite_score=round(score, 1),
        metrics=metrics,
        raw=raw,
    )
