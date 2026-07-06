"""Alpha AI portfolio mode — impact of a new position on saved holdings."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from analyzer.portfolio_store import load_saved_portfolio
from analyzer.watchlist_sector import sector_concentration_warning
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
    sector_breakdown: dict[str, float] = field(default_factory=dict)
    summary: str = ""
    warnings: list[str] = field(default_factory=list)


class _SectorPick:
    __slots__ = ("sector",)

    def __init__(self, sector: str) -> None:
        self.sector = sector


def _holding_value(h: ZerodhaHolding) -> float:
    px = h.last_price or h.average_price or 0
    return max(0, px * h.quantity)


def _lookup_sector(symbol: str, market: str = "india") -> str:
    try:
        from analyzer.data import fetch_stock_data

        _, info = fetch_stock_data(symbol, period="5d", market=market)
        return (info.get("sector") or "Unknown").strip() or "Unknown"
    except Exception:
        return "Unknown"


def _portfolio_sector_weights(
    holdings: list[ZerodhaHolding],
    *,
    market: str = "india",
) -> dict[str, float]:
    total = sum(_holding_value(h) for h in holdings)
    if total <= 0:
        return {}
    by_sector: dict[str, float] = defaultdict(float)
    for h in holdings[:12]:
        sym = h.yahoo_symbol or h.tradingsymbol
        if not sym:
            continue
        sector = _lookup_sector(sym, market=market)
        by_sector[sector] += _holding_value(h) / total * 100
    return dict(by_sector)


def analyze_portfolio_impact(
    candidate_symbol: str,
    candidate_sector: str,
    candidate_value: float | None = None,
    *,
    profile: str | None = None,
    market: str = "india",
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

    sector_weights = _portfolio_sector_weights(holdings, market=market)
    cand_sector = (candidate_sector or "Unknown").strip()

    overlap: list[str] = []
    cand_base = candidate_symbol.replace(".NS", "").upper()
    sector_val = 0.0
    for h in holdings:
        sym = (h.yahoo_symbol or h.tradingsymbol or "").replace(".NS", "").upper()
        if sym == cand_base:
            overlap.append(sym)
        h_sector = _lookup_sector(h.yahoo_symbol or h.tradingsymbol or "", market=market)
        if h_sector == cand_sector:
            sector_val += _holding_value(h)

    before_pct = (sector_val / total * 100) if total > 0 else 0
    after_weights = {k: v * (total / new_total) for k, v in sector_weights.items()} if new_total else dict(sector_weights)
    after_weights[cand_sector] = after_weights.get(cand_sector, 0) + (add / new_total * 100)
    after_pct = after_weights.get(cand_sector, before_pct)

    if after_pct > 25:
        warnings.append(
            f"**{cand_sector}** exposure would reach ~{after_pct:.0f}% of portfolio (limit 25%)."
        )
    top_sector, top_pct = max(after_weights.items(), key=lambda x: x[1], default=("", 0))
    if top_pct > 30 and top_sector:
        warnings.append(f"Largest sector **{top_sector}** at ~{top_pct:.0f}% after add.")

    pseudo_picks = [_SectorPick(s) for s, pct in after_weights.items() for _ in range(max(1, int(pct / 10)))]
    pseudo_picks.append(_SectorPick(cand_sector))
    sector_warn = sector_concentration_warning(pseudo_picks, threshold=3)
    if sector_warn:
        warnings.append(sector_warn.replace("**", ""))

    if overlap:
        warnings.append(f"Already hold {overlap[0]} — adding increases single-name concentration.")

    breakdown = ", ".join(f"{s} {p:.0f}%" for s, p in sorted(after_weights.items(), key=lambda x: -x[1])[:5])
    summary = (
        f"Portfolio **{len(holdings)}** holdings · **₹{total:,.0f}** total.\n"
        f"Adding **₹{add:,.0f}** in **{candidate_symbol}** ({cand_sector}) → "
        f"sector weight **{before_pct:.1f}%** → **{after_pct:.1f}%**.\n"
        f"Sector mix (after add, est.): {breakdown or '—'}."
    )

    return PortfolioImpactAnalysis(
        holdings_count=len(holdings),
        total_value=total,
        candidate_symbol=candidate_symbol,
        candidate_sector=cand_sector,
        sector_before_pct=round(before_pct, 1),
        sector_after_pct=round(after_pct, 1),
        overlap_symbols=overlap,
        sector_breakdown={k: round(v, 1) for k, v in after_weights.items()},
        summary=summary,
        warnings=warnings,
    )


def format_portfolio_impact_block(analysis: PortfolioImpactAnalysis) -> str:
    lines = [analysis.summary]
    for w in analysis.warnings:
        lines.append(f"- ⚠️ {w}")
    return "\n\n".join(lines)
