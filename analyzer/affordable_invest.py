"""Top investment picks under a price cap — uses live Market Pulse scan data."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.market_pulse_scan import (
    BUY_ACTIONS_LONG,
    BUY_ACTIONS_SHORT,
    StockPulseEntry,
)

DEFAULT_MAX_INVEST_PRICE_INR = 3000.0
BUY_COMBINED = frozenset({"STRONG BUY", "BUY"})


@dataclass
class AffordableInvestPick:
    nse_symbol: str
    name: str
    price: float
    ltp_source: str
    combined_rec: str
    combined_score: float
    long_action: str
    long_score: float
    short_action: str
    short_score: float
    invest_score: float
    rank: int
    reason: str
    entry_hint: str
    stop_hint: str
    target_hint: str
    price_change_pct: float | None = None


def _invest_score(stock: StockPulseEntry) -> float:
    if stock.error or not stock.long_term or not stock.short_term:
        return -999.0
    score = (
        stock.combined_score * 0.45
        + stock.long_term.score * 0.40
        + stock.short_term.score * 0.15
    )
    if stock.long_term.action in BUY_ACTIONS_LONG:
        score += 10.0
    if stock.combined_rec in BUY_COMBINED:
        score += 6.0
    if stock.short_term.action in BUY_ACTIONS_SHORT:
        score += 3.0
    if stock.long_term.action in ("SELL", "AVOID", "REDUCE"):
        score -= 25.0
    if stock.combined_rec in ("STRONG SELL", "SELL"):
        score -= 30.0
    return round(score, 1)


def _reason(stock: StockPulseEntry) -> str:
    parts: list[str] = []
    if stock.long_term.action in BUY_ACTIONS_LONG:
        parts.append(f"Long-term **{stock.long_term.action}** ({stock.long_term.score:+.0f})")
    if stock.combined_rec in BUY_COMBINED:
        parts.append(f"Combined **{stock.combined_rec}** ({stock.combined_score:+.0f})")
    if stock.short_term.action in BUY_ACTIONS_SHORT:
        parts.append(f"Swing **{stock.short_term.action}** ({stock.short_term.score:+.0f})")
    if stock.ltp_source == "Kite":
        parts.append("Live **Kite LTP**")
    if not parts:
        parts.append(stock.what_to_do or "Best relative quality under ₹3,000 in today's scan")
    return " · ".join(parts[:4])


def rank_affordable_investments(
    stocks: list[StockPulseEntry],
    *,
    max_price_inr: float = DEFAULT_MAX_INVEST_PRICE_INR,
    limit: int = 5,
) -> list[AffordableInvestPick]:
    """
  Rank Nifty names under max_price_inr for delivery/SIP-style investing.
  Uses prices from the live Market Pulse scan (Kite LTP when connected).
    """
    eligible: list[tuple[float, StockPulseEntry]] = []
    for stock in stocks:
        if stock.error or stock.price <= 0 or stock.price > max_price_inr:
            continue
        if not stock.long_term or not stock.short_term:
            continue
        if stock.combined_rec in ("STRONG SELL", "SELL"):
            continue
        if stock.long_term.action in ("SELL", "AVOID"):
            continue
        inv = _invest_score(stock)
        if inv <= 0:
            continue
        eligible.append((inv, stock))

    eligible.sort(key=lambda x: (-x[0], -x[1].combined_score))
    picks: list[AffordableInvestPick] = []
    for rank, (inv, stock) in enumerate(eligible[:limit], start=1):
        lt = stock.long_term
        picks.append(
            AffordableInvestPick(
                nse_symbol=stock.nse_symbol,
                name=stock.name,
                price=stock.price,
                ltp_source=stock.ltp_source,
                combined_rec=stock.combined_rec,
                combined_score=stock.combined_score,
                long_action=lt.action,
                long_score=lt.score,
                short_action=stock.short_term.action,
                short_score=stock.short_term.score,
                invest_score=inv,
                rank=rank,
                reason=_reason(stock),
                entry_hint=lt.entry_hint,
                stop_hint=lt.stop_hint,
                target_hint=lt.target_hint,
                price_change_pct=stock.price_change_pct,
            )
        )
    return picks


def affordable_from_pulse_report(report, limit: int = 5) -> list[AffordableInvestPick]:
    """Build top picks from a MarketPulseReport (uses full Nifty 50 stock_map)."""
    stocks = list(getattr(report, "stock_map", {}).values())
    if not stocks and getattr(report, "top_stocks", None):
        stocks = list(report.top_stocks)
    return rank_affordable_investments(stocks, limit=limit)


def affordable_invest_summary(picks: list[AffordableInvestPick], max_price: float) -> str:
    if not picks:
        return (
            f"No strong delivery picks under **₹{max_price:,.0f}** in the current scan. "
            "Try after market open for live LTP, or refresh the pulse."
        )
    names = ", ".join(f"**{p.nse_symbol}**" for p in picks[:3])
    live = sum(1 for p in picks if p.ltp_source == "Kite")
    src = f"**{live}** with live Kite LTP" if live else "Yahoo/NSE delayed prices"
    return (
        f"Top **{len(picks)}** invest ideas under **₹{max_price:,.0f}** from Nifty 50 — {names}. "
        f"Prices: {src}. Favor **delivery / SIP**, not MIS."
    )
