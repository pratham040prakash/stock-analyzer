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
        f"Includes **delivery**, **intraday MIS**, **Nifty/Bank Nifty CE/PE**, and stock options. Prices: {src}."
    )


# Nifty 50 & Bank Nifty for index options under premium cap
INDEX_AFFORDABLE_TARGETS = [
    ("NIFTY", "Nifty 50", "^NSEI"),
    ("BANKNIFTY", "Nifty Bank", "^NSEBANK"),
]


@dataclass
class AffordableIndexPick:
    fno_symbol: str
    name: str
    spot: float
    expiry: str
    index_bias: str
    options_action: str
    intraday_note: str
    ce_pick: str
    ce_ltp: float | None
    pe_pick: str
    pe_ltp: float | None
    recommended: str
    chain_note: str
    error: str | None = None


def _recommended_index_side(action: str, ce_leg, pe_leg, max_premium: float) -> str:
    if "CE" in action and ce_leg:
        return (
            f"**Pick CE** — premium ₹{ce_leg.ltp:,.2f} (under ₹{max_premium:,.0f}) · "
            f"strike {ce_leg.strike:g}"
        )
    if "PE" in action and pe_leg:
        return (
            f"**Pick PE** — premium ₹{pe_leg.ltp:,.2f} (under ₹{max_premium:,.0f}) · "
            f"strike {pe_leg.strike:g}"
        )
    if ce_leg and pe_leg:
        return (
            f"**No strong bias** — affordable **CE** ₹{ce_leg.ltp:,.2f} @ {ce_leg.strike:g} or "
            f"**PE** ₹{pe_leg.ltp:,.2f} @ {pe_leg.strike:g} (hedge only)"
        )
    if ce_leg:
        return f"Affordable **CE** only — ₹{ce_leg.ltp:,.2f} @ {ce_leg.strike:g}"
    if pe_leg:
        return f"Affordable **PE** only — ₹{pe_leg.ltp:,.2f} @ {pe_leg.strike:g}"
    return f"No liquid CE/PE found with premium ≤ ₹{max_premium:,.0f}"


def _scan_affordable_index(
    fno_symbol: str,
    name: str,
    yahoo_symbol: str,
    index_pulse,
    *,
    max_premium: float,
    period: str,
) -> AffordableIndexPick:
    from analyzer.market_pulse_scan import scan_index_options
    from analyzer.nse_options import (
        chain_summary_markdown,
        fetch_option_chain,
        format_affordable_leg,
        pick_affordable_strikes,
    )

    bias = "NEUTRAL"
    if index_pulse:
        bias = getattr(index_pulse, "recommendation", None) or "NEUTRAL"

    try:
        io = scan_index_options(fno_symbol, name, yahoo_symbol, period, index_pulse)
        chain = io.chain
        if not chain:
            chain = fetch_option_chain(fno_symbol)
        ce_leg, pe_leg = pick_affordable_strikes(chain, max_premium=max_premium)
        ce_txt = format_affordable_leg(ce_leg, chain.spot) if ce_leg else "—"
        pe_txt = format_affordable_leg(pe_leg, chain.spot) if pe_leg else "—"
        intra_note = ""
        if io.picks:
            intra_note = io.picks[0].reason
        elif io.options_action not in ("NO TRADE", "WAIT"):
            intra_note = f"Live chart bias: **{io.options_action}**"
        return AffordableIndexPick(
            fno_symbol=fno_symbol,
            name=name,
            spot=chain.spot,
            expiry=chain.expiry,
            index_bias=bias,
            options_action=io.options_action,
            intraday_note=intra_note,
            ce_pick=ce_txt,
            ce_ltp=ce_leg.ltp if ce_leg else None,
            pe_pick=pe_txt,
            pe_ltp=pe_leg.ltp if pe_leg else None,
            recommended=_recommended_index_side(io.options_action, ce_leg, pe_leg, max_premium),
            chain_note=chain_summary_markdown(chain),
            error=io.error,
        )
    except Exception as exc:
        return AffordableIndexPick(
            fno_symbol=fno_symbol,
            name=name,
            spot=0.0,
            expiry="",
            index_bias=bias,
            options_action="NO TRADE",
            intraday_note="",
            ce_pick="—",
            ce_ltp=None,
            pe_pick="—",
            pe_ltp=None,
            recommended="—",
            chain_note="",
            error=str(exc),
        )


def build_affordable_index_options(
    report,
    *,
    max_premium: float = DEFAULT_MAX_INVEST_PRICE_INR,
    period: str = "1y",
) -> list[AffordableIndexPick]:
    """Nifty & Bank Nifty CE/PE with option premium ≤ max_premium."""
    pulse_by_yahoo = {p.symbol: p for p in getattr(report, "indices", [])}
    results: list[AffordableIndexPick] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = {
            pool.submit(
                _scan_affordable_index,
                fno,
                name,
                yahoo,
                pulse_by_yahoo.get(yahoo),
                max_premium=max_premium,
                period=period,
            ): fno
            for fno, name, yahoo in INDEX_AFFORDABLE_TARGETS
        }
        for fut in as_completed(futs):
            results.append(fut.result())
    order = {fno: i for i, (fno, _, _) in enumerate(INDEX_AFFORDABLE_TARGETS)}
    results.sort(key=lambda r: order.get(r.fno_symbol, 99))
    return results
