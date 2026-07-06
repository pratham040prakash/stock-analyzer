"""ETF-specific metrics — TER, AUM, benchmark, tracking notes."""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.asset_class import classify_asset


@dataclass
class ETFProfile:
    symbol: str
    name: str
    is_etf: bool
    expense_ratio_pct: float | None = None
    aum: float | None = None
    category: str = ""
    underlying_index: str = ""
    tracking_error_note: str = ""
    yield_pct: float | None = None
    notes: list[str] = field(default_factory=list)


def _fmt_inr(val: float | None) -> str:
    if val is None:
        return "N/A"
    if val >= 1e7:
        return f"₹{val/1e7:.1f} Cr"
    return f"₹{val:,.0f}"


def build_etf_profile(symbol: str, info: dict) -> ETFProfile | None:
    ac = classify_asset(symbol, info)
    if ac.asset_class != "etf":
        return None

    ter = info.get("annualReportExpenseRatio") or info.get("expenseRatio")
    if ter is not None and ter < 1:
        ter = ter * 100  # yahoo sometimes returns decimal

    aum = info.get("totalAssets") or info.get("marketCap")
    category = info.get("category") or info.get("fundFamily") or "ETF"
    benchmark = (
        info.get("benchmark")
        or info.get("indexName")
        or info.get("fundInception")
        or info.get("longName", "")
    )
    # Infer index from name
    name = info.get("longName") or info.get("shortName") or symbol
    upper = name.upper()
    if "NIFTY 50" in upper or "NIFTY50" in upper:
        underlying = "Nifty 50"
    elif "BANK" in upper and "NIFTY" in upper:
        underlying = "Nifty Bank"
    elif "S&P 500" in upper or "SPY" in symbol.upper():
        underlying = "S&P 500"
    elif "NASDAQ" in upper or "QQQ" in symbol.upper():
        underlying = "Nasdaq 100"
    elif "GOLD" in upper:
        underlying = "Gold"
    elif "LIQUID" in upper:
        underlying = "Money market / liquid"
    else:
        underlying = str(benchmark)[:80] if benchmark else "See fund factsheet"

    notes: list[str] = []
    if ter is not None:
        notes.append(f"TER {ter:.2f}% — compare to direct index + taxes.")
    else:
        notes.append("TER not in feed — check AMC factsheet.")

    tracking = (
        "Tracking error not computed — compare 1Y/3Y return vs index manually."
    )
    if aum is not None:
        notes.append(f"AUM {_fmt_inr(aum) if symbol.endswith('.NS') else f'${aum:,.0f}'}")

    return ETFProfile(
        symbol=symbol,
        name=name,
        is_etf=True,
        expense_ratio_pct=float(ter) if ter is not None else None,
        aum=float(aum) if aum is not None else None,
        category=str(category),
        underlying_index=underlying,
        tracking_error_note=tracking,
        yield_pct=info.get("dividendYield"),
        notes=notes,
    )


def format_etf_markdown(profile: ETFProfile) -> str:
    lines = [
        f"**ETF mode** — {profile.name}",
        f"**Underlying:** {profile.underlying_index}",
        f"**Category:** {profile.category}",
        f"**Expense ratio (TER):** {profile.expense_ratio_pct:.2f}%" if profile.expense_ratio_pct else "**TER:** N/A in feed",
        f"**AUM:** {profile.aum:,.0f}" if profile.aum else "**AUM:** N/A",
        f"**Tracking:** {profile.tracking_error_note}",
    ]
    for n in profile.notes:
        lines.append(f"- {n}")
    lines.append("_Stock DCF/moat sections reduced — evaluate cost, tracking, and index fit._")
    return "\n".join(lines)
