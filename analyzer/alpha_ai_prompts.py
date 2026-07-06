"""Report-mode prompts — ETF, penny, large-cap framing."""

from __future__ import annotations

from analyzer.asset_class import classify_asset
from analyzer.india import NIFTY_50
from analyzer.markets import is_india_market

PENNY_PRICE_INR = 50.0
LARGE_CAP_INR = 50_000_000_000  # ₹5000 Cr market cap heuristic


def detect_report_mode(
    symbol: str,
    info: dict,
    price: float | None,
    market: str,
) -> str:
    """etf | penny | large_cap | mid_cap"""
    ac = classify_asset(symbol, info)
    if ac.asset_class == "etf":
        return "etf"

    base = symbol.replace(".NS", "").replace(".BO", "").upper()
    if is_india_market(market) and price is not None and price < PENNY_PRICE_INR:
        return "penny"
    if base in NIFTY_50:
        return "large_cap"

    mcap = info.get("market_cap")
    if mcap and mcap >= LARGE_CAP_INR:
        return "large_cap"
    if price and price < PENNY_PRICE_INR:
        return "penny"
    return "mid_cap"


def mode_framing(mode: str) -> dict[str, str]:
    """Section-specific guidance text per asset mode."""
    if mode == "etf":
        return {
            "business": "_ETF focus: index fit, TER, tracking error — not business moat._",
            "valuation": "_Value = cost + tracking vs holding stocks directly._",
            "moat": "_Moat section N/A for passive ETF — evaluate AMC and liquidity._",
            "risk": "_Primary risks: tracking error, TER drag, index composition changes._",
        }
    if mode == "penny":
        return {
            "business": "_Penny/small-cap: higher fraud, liquidity, and delisting risk — size small._",
            "valuation": "_Multiples volatile — verify pledge, auditor, and cash flows in AR._",
            "moat": "_Moat often weak — momentum and news-driven._",
            "risk": "_High risk: circuit limits, low delivery, manipulation risk._",
        }
    if mode == "large_cap":
        return {
            "business": "_Large-cap: focus on ROE, governance, and competitive moat sustainability._",
            "valuation": "_Compare vs sector median and historical own P/E band._",
            "moat": "_Institutional quality bar — sustained ROE and cash conversion._",
            "risk": "_Macro, regulation, and index weight flows dominate._",
        }
    return {
        "business": "_Mid-cap: balance growth vs execution risk; liquidity in stress._",
        "valuation": "_Growth premium must be earned quarterly._",
        "moat": "_Moat still forming — verify market share trends._",
        "risk": "_Earnings miss can de-rate sharply._",
    }
