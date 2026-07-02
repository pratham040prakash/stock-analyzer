"""Intraday scan for small portfolios (≤10 stocks) — focused MIS guidance."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from analyzer.candle_narrative import LiveChartVerdict, analyze_live_chart
from analyzer.intraday_data import fetch_intraday
from analyzer.intraday_signals import add_intraday_indicators, compute_trade_levels
from analyzer.live_charts_grid import ACTION_RANK, build_hypothesis
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult

MAX_SMALL_TRADER_STOCKS = 10

BUY_ACTIONS = frozenset({"STRONG BUY", "BUY"})
SELL_ACTIONS = frozenset({"STRONG SELL", "SELL"})


@dataclass
class SmallTraderHoldingRow:
    nse_symbol: str
    name: str
    quantity: float
    avg_price: float | None
    pnl_pct: float | None
    price: float
    vwap: float
    above_vwap: bool
    action: str
    confidence: str
    score: float
    entry: float | None
    stop_loss: float | None
    target: float | None
    hypothesis: str
    owner_note: str
    error: str | None = None
    verdict: LiveChartVerdict | None = None
    chart_df=None


@dataclass
class SmallTraderIntradayReport:
    holdings_count: int
    interval: str
    updated_at: str
    rows: list[SmallTraderHoldingRow] = field(default_factory=list)
    buy_count: int = 0
    sell_count: int = 0
    wait_count: int = 0
    focus_symbols: list[str] = field(default_factory=list)
    session_open: bool = True


def _pnl_pct(h: ZerodhaHolding, last_price: float | None) -> float | None:
    if h.average_price is None or not h.average_price or not last_price:
        return None
    return (last_price - h.average_price) / h.average_price * 100


def _owner_note(h: ZerodhaHolding, action: str, pnl_pct: float | None) -> str:
    qty = int(h.quantity)
    if action in BUY_ACTIONS:
        if pnl_pct is not None and pnl_pct < -8:
            return (
                f"You hold {qty} shares ({pnl_pct:+.1f}% vs avg) — "
                "intraday buy is risky; avoid averaging down on MIS."
            )
        if pnl_pct is not None and pnl_pct > 15:
            return f"You hold {qty} shares (+{pnl_pct:.1f}%) — OK to add small MIS only with tight stop."
        return f"You hold {qty} shares — MIS long only if liquid (Nifty 50 / high volume)."
    if action in SELL_ACTIONS:
        if pnl_pct is not None and pnl_pct > 10:
            return f"You hold {qty} shares (+{pnl_pct:.1f}%) — consider partial profit on weakness."
        if pnl_pct is not None and pnl_pct < -5:
            return f"You hold {qty} shares ({pnl_pct:+.1f}%) — don't panic-sell delivery; wait for OR reclaim."
        return f"You hold {qty} shares — intraday fade is separate from your delivery position."
    return f"You hold {qty} shares — no clear MIS edge; manage delivery with Daily Advisor."


def _scan_holding(h: ZerodhaHolding, interval: str, market: str) -> SmallTraderHoldingRow:
    sym = (h.yahoo_symbol or h.tradingsymbol).replace(".NS", "").replace(".BO", "").upper()
    name = h.tradingsymbol
    try:
        df, _meta = fetch_intraday(sym, interval=interval, market=market)
        verdict = analyze_live_chart(df, sym, interval)
        df_ind = add_intraday_indicators(df)
        intra = verdict.intraday
        price = intra.last_price if intra else float(df["Close"].iloc[-1])
        vwap = intra.vwap if intra else price
        pnl = _pnl_pct(h, price)
        entry, stop, target = (
            compute_trade_levels(intra, verdict.action) if intra else (None, None, None)
        )
        return SmallTraderHoldingRow(
            nse_symbol=sym,
            name=name,
            quantity=h.quantity,
            avg_price=h.average_price,
            pnl_pct=pnl,
            price=price,
            vwap=vwap,
            above_vwap=price > vwap * 1.001,
            action=verdict.action,
            confidence=verdict.confidence,
            score=verdict.directional_score,
            entry=entry or verdict.entry,
            stop_loss=stop or verdict.stop_loss,
            target=target or verdict.target,
            hypothesis=build_hypothesis(verdict),
            owner_note=_owner_note(h, verdict.action, pnl),
            verdict=verdict,
            chart_df=df_ind,
        )
    except Exception as exc:
        return SmallTraderHoldingRow(
            nse_symbol=sym,
            name=name,
            quantity=h.quantity,
            avg_price=h.average_price,
            pnl_pct=_pnl_pct(h, h.last_price),
            price=h.last_price or 0.0,
            vwap=0.0,
            above_vwap=False,
            action="ERROR",
            confidence="low",
            score=0.0,
            entry=None,
            stop_loss=None,
            target=None,
            hypothesis="",
            owner_note="Could not load intraday data.",
            error=str(exc),
        )


def scan_small_trader_portfolio(
    import_result: ZerodhaImportResult,
    *,
    interval: str = "5m",
    market: str = "india",
    max_stocks: int = MAX_SMALL_TRADER_STOCKS,
) -> SmallTraderIntradayReport | None:
    """Scan each holding for live intraday action — for portfolios with ≤10 names."""
    holdings = import_result.holdings[:max_stocks]
    if not holdings or len(import_result.holdings) > max_stocks:
        return None

    from datetime import datetime
    from zoneinfo import ZoneInfo

    from analyzer.intraday_data import market_session_status

    session = market_session_status()
    rows: list[SmallTraderHoldingRow] = []
    workers = min(6, len(holdings))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_scan_holding, h, interval, market): h for h in holdings}
        for fut in as_completed(futs):
            rows.append(fut.result())

    rows.sort(key=lambda r: (ACTION_RANK.get(r.action, 0), r.score), reverse=True)

    focus = [
        r.nse_symbol
        for r in rows
        if r.action in BUY_ACTIONS | SELL_ACTIONS and not r.error
    ][:3]

    buy = sum(1 for r in rows if r.action in BUY_ACTIONS)
    sell = sum(1 for r in rows if r.action in SELL_ACTIONS)
    wait = sum(1 for r in rows if r.action == "WAIT")

    ist = ZoneInfo("Asia/Kolkata")
    return SmallTraderIntradayReport(
        holdings_count=len(holdings),
        interval=interval,
        updated_at=datetime.now(ist).strftime("%H:%M:%S IST"),
        rows=rows,
        buy_count=buy,
        sell_count=sell,
        wait_count=wait,
        focus_symbols=focus,
        session_open=bool(session.get("is_open")),
    )


def small_trader_intraday_tips(report: SmallTraderIntradayReport) -> str:
    """Plain-language rules for traders with a small watchlist."""
    lines = [
        "**Small trader rules (≤10 stocks)**",
        "- Trade **1–2 setups max** per day — don't chase every green signal.",
        "- Risk **≤1% of capital** per MIS trade; use the stop levels shown.",
        "- **Square off MIS before 3:20 PM IST** — avoid auto square-off penalties.",
        "- Prefer **liquid names** (Nifty 50, high volume); thin stocks slip on MIS.",
        "- You already own these — intraday is **optional**. Delivery decisions live in **Daily Advisor**.",
    ]
    if not report.session_open:
        lines.append(
            "- Market **closed** — levels are from the last session; plan entries at tomorrow's open."
        )
    elif report.focus_symbols:
        lines.append(
            f"- **Focus today:** {', '.join(report.focus_symbols)} "
            f"({report.buy_count} buy · {report.sell_count} sell · {report.wait_count} wait)."
        )
    else:
        lines.append("- **No strong MIS edge** across your holdings — sitting out is fine.")
    return "\n".join(lines)
