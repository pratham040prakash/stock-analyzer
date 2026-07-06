"""Simple DCF and reverse-DCF with sensitivity table."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class DCFSensitivityCell:
    growth_pct: float
    discount_pct: float
    fair_value: float


@dataclass
class DCFResult:
    symbol: str
    current_price: float | None
    fair_value: float | None
    margin_of_safety_pct: float | None
    assumptions: dict[str, float] = field(default_factory=dict)
    sensitivity: list[DCFSensitivityCell] = field(default_factory=list)
    disclaimer: str = "ESTIMATE — 5-stage FCF model simplified; verify in AR."


def _dcf_fair_value(
    fcf: float,
    growth: float,
    terminal_growth: float,
    discount: float,
    years: int = 5,
) -> float | None:
    if fcf <= 0 or discount <= terminal_growth:
        return None
    pv = 0.0
    cf = fcf
    for y in range(1, years + 1):
        cf *= 1 + growth
        pv += cf / ((1 + discount) ** y)
    terminal = cf * (1 + terminal_growth) / (discount - terminal_growth)
    pv += terminal / ((1 + discount) ** years)
    return pv


def build_dcf(
    symbol: str,
    *,
    free_cashflow: float | None,
    shares_outstanding: float | None,
    earnings_growth: float | None,
    current_price: float | None,
    discount_rate: float = 0.12,
    terminal_growth: float = 0.04,
) -> DCFResult:
    """Two-stage DCF per share; reverse implied growth if FCF missing."""
    assumptions: dict[str, float] = {
        "discount_rate": discount_rate,
        "terminal_growth": terminal_growth,
        "projection_years": 5,
    }
    growth = earnings_growth if earnings_growth is not None else 0.08
    if growth > 0.25:
        growth = 0.25
    if growth < 0:
        growth = 0.02
    assumptions["near_term_growth"] = growth

    fair_per_share = None
    if free_cashflow and shares_outstanding and shares_outstanding > 0:
        fcf_ps = free_cashflow / shares_outstanding
        total_fv = _dcf_fair_value(fcf_ps, growth, terminal_growth, discount_rate)
        fair_per_share = total_fv

    mos = None
    if fair_per_share and current_price and current_price > 0:
        mos = ((fair_per_share - current_price) / fair_per_share) * 100

    sensitivity: list[DCFSensitivityCell] = []
    if free_cashflow and shares_outstanding and shares_outstanding > 0:
        fcf_ps = free_cashflow / shares_outstanding
        for g in (0.05, 0.08, 0.12, 0.15):
            for d in (0.10, 0.12, 0.14):
                fv = _dcf_fair_value(fcf_ps, g, terminal_growth, d)
                if fv:
                    sensitivity.append(DCFSensitivityCell(g * 100, d * 100, round(fv, 2)))

    return DCFResult(
        symbol=symbol,
        current_price=current_price,
        fair_value=round(fair_per_share, 2) if fair_per_share else None,
        margin_of_safety_pct=round(mos, 1) if mos is not None else None,
        assumptions=assumptions,
        sensitivity=sensitivity,
    )


def format_dcf_markdown(dcf: DCFResult, currency: str = "₹") -> str:
    if dcf.fair_value is None:
        return (
            "**DCF / intrinsic value:** Cannot compute — missing FCF or share count in feed. "
            "Use reverse DCF manually from AR cash flows."
        )
    lines = [
        f"**DCF fair value (ESTIMATE):** {currency}{dcf.fair_value:,.2f} vs price {currency}{dcf.current_price or 0:,.2f}",
    ]
    if dcf.margin_of_safety_pct is not None:
        lines.append(f"**Margin of safety:** {dcf.margin_of_safety_pct:+.1f}%")
    lines.append(
        f"_Assumptions: growth {dcf.assumptions.get('near_term_growth', 0)*100:.0f}%, "
        f"discount {dcf.assumptions.get('discount_rate', 0.12)*100:.0f}%, "
        f"terminal {dcf.assumptions.get('terminal_growth', 0.04)*100:.0f}%_"
    )
    if dcf.sensitivity:
        lines.append("\n**Sensitivity (fair value per share):**")
        lines.append("| Growth \\ Discount | 10% | 12% | 14% |")
        lines.append("|------------------|-----|-----|-----|")
        for g in (5, 8, 12, 15):
            row = f"| {g}% |"
            for d in (10, 12, 14):
                cell = next((c for c in dcf.sensitivity if c.growth_pct == g and c.discount_pct == d), None)
                row += f" {cell.fair_value if cell else '—'} |"
            lines.append(row)
    lines.append(f"\n_{dcf.disclaimer}_")
    return "\n".join(lines)


def sensitivity_dataframe(dcf: DCFResult) -> pd.DataFrame:
    if not dcf.sensitivity:
        return pd.DataFrame()
    rows = []
    for c in dcf.sensitivity:
        rows.append({"Growth %": c.growth_pct, "Discount %": c.discount_pct, "Fair value": c.fair_value})
    return pd.DataFrame(rows)
