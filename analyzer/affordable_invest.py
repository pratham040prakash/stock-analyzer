"""Top investment picks under a price cap — uses live Market Pulse scan data."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from analyzer.market_pulse_scan import (
    BUY_ACTIONS_INTRADAY,
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
    intraday_action: str = "—"
    intraday_score: float = 0.0
    intraday_entry: str = "—"
    intraday_stop: str = "—"
    intraday_target: str = "—"
    intraday_summary: str = ""
    options_action: str = "NO TRADE"
    options_ce_pick: str = "—"
    options_pe_pick: str = "—"
    options_chain_note: str = ""
    options_error: str | None = None


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
    if stock.intraday and stock.intraday.action in BUY_ACTIONS_INTRADAY:
        parts.append(f"Intraday **{stock.intraday.action}** ({stock.intraday.score:+.0f})")
    if stock.ltp_source == "Kite":
        parts.append("Live **Kite LTP**")
    if not parts:
        parts.append(stock.what_to_do or "Best relative quality under ₹3,000 in today's scan")
    return " · ".join(parts[:5])


def _options_action_from_stock(stock: StockPulseEntry) -> str:
    if stock.intraday_verdict and stock.intraday_verdict.options:
        return stock.intraday_verdict.options.action
    if stock.intraday_verdict:
        action = stock.intraday_verdict.action
        if action in BUY_ACTIONS_INTRADAY:
            return "BUY CE"
        if action in ("SELL", "STRONG SELL"):
            return "BUY PE"
    if stock.intraday:
        if stock.intraday.action in BUY_ACTIONS_INTRADAY:
            return "BUY CE"
        if stock.intraday.action in ("SELL", "STRONG SELL"):
            return "BUY PE"
    return "NO TRADE"


def _intraday_fields(stock: StockPulseEntry) -> dict:
    intra = stock.intraday
    verdict = stock.intraday_verdict
    if not intra:
        return {
            "intraday_action": "—",
            "intraday_score": 0.0,
            "intraday_entry": "—",
            "intraday_stop": "—",
            "intraday_target": "—",
            "intraday_summary": "",
        }
    entry = intra.entry_hint
    stop = intra.stop_hint
    target = intra.target_hint
    if verdict:
        if verdict.entry is not None:
            entry = f"₹{verdict.entry:,.2f}"
        if verdict.stop_loss is not None:
            stop = f"₹{verdict.stop_loss:,.2f}"
        if verdict.target is not None:
            target = f"₹{verdict.target:,.2f}"
    return {
        "intraday_action": intra.action,
        "intraday_score": intra.score,
        "intraday_entry": entry,
        "intraday_stop": stop,
        "intraday_target": target,
        "intraday_summary": intra.summary,
    }


def _format_option_pick(pick) -> str:
    if not pick:
        return "—"
    leg = pick.leg
    iv = f" · IV {leg.iv:.1f}%" if leg.iv else ""
    return (
        f"**{leg.option_type} {leg.strike:g}** · LTP ₹{leg.ltp or 0:,.2f} · "
        f"OI {leg.open_interest:,} · Vol {leg.volume:,}{iv}"
    )


def enrich_pick_options(pick: AffordableInvestPick) -> AffordableInvestPick:
    """Fetch NSE chain and attach top CE + PE strike ideas."""
    from analyzer.nse_options import (
        chain_summary_markdown,
        fetch_option_chain,
        recommend_nse_strikes,
    )

    try:
        chain = fetch_option_chain(pick.nse_symbol)
        ce_picks = recommend_nse_strikes(chain, "BUY CE")
        pe_picks = recommend_nse_strikes(chain, "BUY PE")
        pick.options_ce_pick = _format_option_pick(ce_picks[0] if ce_picks else None)
        pick.options_pe_pick = _format_option_pick(pe_picks[0] if pe_picks else None)
        pick.options_chain_note = chain_summary_markdown(chain)
    except Exception as exc:
        pick.options_error = str(exc)
    return pick


def _stock_to_pick(rank: int, inv: float, stock: StockPulseEntry) -> AffordableInvestPick:
    lt = stock.long_term
    assert lt is not None and stock.short_term is not None
    intra = _intraday_fields(stock)
    return AffordableInvestPick(
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
        options_action=_options_action_from_stock(stock),
        **intra,
    )


def rank_affordable_investments(
    stocks: list[StockPulseEntry],
    *,
    max_price_inr: float = DEFAULT_MAX_INVEST_PRICE_INR,
    limit: int = 5,
    enrich_options: bool = False,
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
    picks = [_stock_to_pick(rank, inv, stock) for rank, (inv, stock) in enumerate(eligible[:limit], start=1)]

    if enrich_options and picks:
        with ThreadPoolExecutor(max_workers=min(5, len(picks))) as pool:
            futs = {pool.submit(enrich_pick_options, p): p for p in picks}
            enriched: list[AffordableInvestPick] = []
            for fut in as_completed(futs):
                enriched.append(fut.result())
            enriched.sort(key=lambda p: p.rank)
            return enriched
    return picks


def affordable_from_pulse_report(
    report,
    limit: int = 5,
    *,
    enrich_options: bool = False,
) -> list[AffordableInvestPick]:
    """Build top picks from a MarketPulseReport (uses full Nifty 50 stock_map)."""
    stocks = list(getattr(report, "stock_map", {}).values())
    if not stocks and getattr(report, "top_stocks", None):
        stocks = list(report.top_stocks)
    return rank_affordable_investments(stocks, limit=limit, enrich_options=enrich_options)


def affordable_invest_summary(picks: list[AffordableInvestPick], max_price: float) -> str:
    if not picks:
        return (
            f"No strong picks under **₹{max_price:,.0f}** in the current scan. "
            "Try after market open for live LTP + intraday, or refresh the pulse."
        )
    names = ", ".join(f"**{p.nse_symbol}**" for p in picks[:3])
    live = sum(1 for p in picks if p.ltp_source == "Kite")
    src = f"**{live}** with live Kite LTP" if live else "Yahoo/NSE delayed prices"
    return (
        f"Top **{len(picks)}** ideas under **₹{max_price:,.0f}** — {names}. "
        f"Includes **delivery**, **intraday MIS**, and **NSE CE/PE** strikes. Prices: {src}."
    )
