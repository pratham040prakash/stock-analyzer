"""Screener.in-style automated red flag rules — evidence from feeds only."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.india_enrichment import EnrichedFundamentals


@dataclass
class RedFlagHit:
    rule: str
    severity: str  # High | Medium
    detail: str


def detect_red_flags(
    raw: dict,
    *,
    tech_score: float,
    fund_score: float,
    enriched: EnrichedFundamentals | None = None,
    promoter_pct: float | None = None,
) -> list[str]:
    """Return human-readable red flag messages; empty if none triggered."""
    hits: list[RedFlagHit] = []

    margin = raw.get("profit_margin")
    if margin is not None and margin < 0:
        hits.append(RedFlagHit("Loss-making", "High", f"Net margin {margin*100:.1f}% — negative earnings."))

    de = raw.get("debt_to_equity")
    if de is not None and de > 1.5:
        hits.append(RedFlagHit("High leverage", "High", f"Debt/equity {de:.2f} — balance sheet stress."))
    elif de is not None and de > 1.0:
        hits.append(RedFlagHit("Elevated debt", "Medium", f"Debt/equity {de:.2f}."))

    roe = raw.get("roe")
    if roe is not None and roe < 0.10:
        v = roe * 100 if roe <= 1 else roe
        hits.append(RedFlagHit("Weak ROE", "Medium", f"ROE {v:.1f}% below 10% quality threshold."))

    rev_g = raw.get("revenue_growth")
    if rev_g is not None and rev_g < -0.05:
        hits.append(RedFlagHit("Revenue decline", "High", f"Trailing revenue growth {rev_g*100:.1f}%."))

    pe = raw.get("pe_trailing")
    eg = raw.get("earnings_growth")
    if pe and pe > 50 and (eg is None or eg < 0.10):
        hits.append(RedFlagHit("Rich valuation", "Medium", f"P/E {pe:.1f} without strong earnings growth."))

    fcf = raw.get("free_cashflow")
    if fcf is not None and fcf < 0:
        hits.append(RedFlagHit("Negative FCF", "High", "Free cash flow negative — funding risk."))

    if enriched and enriched.interest_coverage is not None and enriched.interest_coverage < 2:
        hits.append(
            RedFlagHit("Interest stress", "High", f"Interest coverage {enriched.interest_coverage:.1f}x < 2x.")
        )

    if enriched and enriched.cash_conversion_pct is not None and enriched.cash_conversion_pct < 50:
        hits.append(
            RedFlagHit("Poor cash conversion", "Medium", f"FCF/NI {enriched.cash_conversion_pct:.0f}% — earnings quality risk.")
        )

    if promoter_pct is not None and promoter_pct < 0.30:
        hits.append(RedFlagHit("Low promoter hold", "Medium", f"Promoter {promoter_pct*100:.1f}% — governance check."))

    if tech_score < -20 and fund_score < -10:
        hits.append(RedFlagHit("Weak TA + fundamentals", "High", "Both technical and fundamental scores weak."))

    if not hits:
        return []

    order = {"High": 0, "Medium": 1}
    hits.sort(key=lambda h: order.get(h.severity, 2))
    return [f"[{h.severity}] {h.rule}: {h.detail}" for h in hits]
