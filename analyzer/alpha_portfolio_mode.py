"""Alpha AI portfolio mode — impact of a new position on saved holdings."""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.portfolio_store import load_saved_portfolio
from analyzer.zerodha import ZerodhaHolding


@dataclass
class PortfolioImpactAnalysis:
    holdings_count: int
    total_value: float
    candidate_symbol: str
    candidate_sector: str
    sector_before_pct: float
    sector_after_pct: float
    overlap_symbols: list[str] = field(default_factory=list)
    summary: str = ""
    warnings: list[str] = field(default_factory=list)


def _holding_value(h: ZerodhaHolding) -> float:
    px = h.last_price or h.average_price or 0
    return max(0, px * h.quantity)


def analyze_portfolio_impact(
    candidate_symbol: str,
    candidate_sector: str,
    candidate_value: float | None = None,
    *,
    profile: str | None = None,
) -> PortfolioImpactAnalysis:
    """Compare candidate against saved portfolio (My Portfolio tab data)."""
    imp = load_saved_portfolio(profile)
    holdings = imp.holdings if imp else []
    warnings: list[str] = []

    if not holdings:
        return PortfolioImpactAnalysis(
            holdings_count=0,
            total_value=0,
            candidate_symbol=candidate_symbol,
            candidate_sector=candidate_sector,
            sector_before_pct=0,
            sector_after_pct=100 if candidate_value else 0,
            summary="No saved portfolio — import holdings in **My Portfolio** first.",
            warnings=["Portfolio empty"],
        )

    total = sum(_holding_value(h) for h in holdings)
    add = candidate_value or (total * 0.05 if total > 0 else 100_000)
    new_total = total + add

    # Sector weights — sector from yahoo symbol match only (simplified)
    sector_val = 0.0
    overlap: list[str] = []
    cand_base = candidate_symbol.replace(".NS", "").upper()
    for h in holdings:
        sym = (h.yahoo_symbol or h.tradingsymbol or "").replace(".NS", "").upper()
        if sym == cand_base:
            overlap.append(sym)
        # Without per-holding sector in store, use symbol match as overlap proxy
        if sym == cand_base:
            sector_val += _holding_value(h)

    before_pct = (sector_val / total * 100) if total > 0 else 0
    after_pct = ((sector_val + add) / new_total * 100) if new_total > 0 else 0

    if after_pct > 25:
        warnings.append(f"Sector/correlated exposure would reach ~{after_pct:.0f}% (limit 25%).")
    if overlap:
        warnings.append(f"Already hold {overlap[0]} — adding increases concentration.")

    summary = (
        f"Portfolio **{len(holdings)}** holdings · **₹{total:,.0f}** total.\n"
        f"Adding **₹{add:,.0f}** in **{candidate_symbol}** ({candidate_sector}) → "
        f"correlated weight ~**{before_pct:.1f}%** → **{after_pct:.1f}%**."
    )

    return PortfolioImpactAnalysis(
        holdings_count=len(holdings),
        total_value=total,
        candidate_symbol=candidate_symbol,
        candidate_sector=candidate_sector,
        sector_before_pct=round(before_pct, 1),
        sector_after_pct=round(after_pct, 1),
        overlap_symbols=overlap,
        summary=summary,
        warnings=warnings,
    )


def format_portfolio_impact_block(analysis: PortfolioImpactAnalysis) -> str:
    lines = [analysis.summary]
    for w in analysis.warnings:
        lines.append(f"- ⚠️ {w}")
    return "\n\n".join(lines)
