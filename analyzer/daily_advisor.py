"""Daily briefing — holdings actions, short-term swings, long-term quality picks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.candle_narrative import analyze_live_chart
from analyzer.chart_horizon import analyze_long_term_chart, analyze_short_term_chart
from analyzer.combined import analyze_combined
from analyzer.data import fetch_stock_data
from analyzer.indicators import add_indicators
from analyzer.intraday_data import fetch_intraday
from analyzer.market_pulse import india_market_pulse, overall_market_verdict
from analyzer.market_pulse_scan import MARKET_PULSE_TOP_10
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult

IST = ZoneInfo("Asia/Kolkata")

LONG_TERM_UNIVERSE = list(dict.fromkeys(MARKET_PULSE_TOP_10 + [
    "HCLTECH", "KOTAKBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
    "BAJFINANCE", "WIPRO", "TITAN", "ULTRACEMCO", "NESTLEIND",
]))

SHORT_TERM_UNIVERSE = MARKET_PULSE_TOP_10


@dataclass
class HoldingDailyAdvice:
    kite_symbol: str
    name: str
    yahoo_symbol: str
    quantity: float
    last_price: float | None
    avg_price: float | None
    pnl_pct: float | None
    portfolio_weight_pct: float | None
    today_action: str
    today_reason: str
    short_term: str
    long_term: str
    combined_score: float
    technical_score: float
    fundamental_score: float
    priority: int  # 1 = act today, 5 = no action
    error: str | None = None


@dataclass
class StockPick:
    symbol: str
    name: str
    price: float
    horizon: str  # short | long
    action: str
    score: float
    reason: str


@dataclass
class DailyBriefing:
    date: str
    generated_at: str
    market_verdict: str
    global_bias: str
    holdings_count: int
    watchlist_count: int = 0
    priority_actions: list[str] = field(default_factory=list)
    holdings: list[HoldingDailyAdvice] = field(default_factory=list)
    short_term_picks: list[StockPick] = field(default_factory=list)
    long_term_picks: list[StockPick] = field(default_factory=list)
    summary: str = ""
    errors: list[str] = field(default_factory=list)


def _now_ist() -> datetime:
    return datetime.now(IST)


def _pnl_pct(h: ZerodhaHolding) -> float | None:
    if h.average_price and h.last_price and h.average_price > 0:
        return round((h.last_price / h.average_price - 1) * 100, 2)
    return None


def _portfolio_weights(holdings: list[ZerodhaHolding]) -> dict[str, float]:
    values: dict[str, float] = {}
    total = 0.0
    for h in holdings:
        px = h.last_price or h.average_price or 0
        v = px * h.quantity
        values[h.yahoo_symbol or h.kite_symbol] = v
        total += v
    if total <= 0:
        return {k: 0.0 for k in values}
    return {k: round(v / total * 100, 1) for k, v in values.items()}


def _short_term_label(tech: float, intraday_action: str | None, session_bias: str | None) -> str:
    if tech >= 25:
        return "Swing bullish (2–8 weeks)"
    if tech <= -25:
        return "Swing bearish — avoid new longs"
    if intraday_action in ("BUY", "STRONG BUY"):
        return "Intraday/swing long bias"
    if intraday_action in ("SELL", "STRONG SELL"):
        return "Intraday weak — don't add"
    if session_bias == "BULLISH":
        return "Session positive — hold longs"
    if session_bias == "BEARISH":
        return "Session negative — tight stops"
    return "Neutral short-term — range trade or wait"


def _long_term_label(fund: float, combined_rec: str) -> str:
    if fund >= 20 and combined_rec in ("STRONG BUY", "BUY", "HOLD"):
        return "Core hold (1–3 years)"
    if fund >= 12:
        return "Accumulate on dips (6–18 months)"
    if fund <= -12 or combined_rec in ("STRONG SELL", "SELL"):
        return "Exit on rallies — weak quality"
    if fund >= 5:
        return "Hold & review after earnings"
    return "Under review — mixed fundamentals"


def _holding_reason(action: str, combined, tech: float, pnl: float | None, weight: float | None, session_bias: str | None) -> str:
    if "EXIT" in action or "TRIM" in action:
        return f"Bearish combined signal ({combined.combined_recommendation})"
    if "REDUCE" in action:
        return "Bearish combined signal"
    if "ADD" in action:
        return f"Quality name in pullback ({pnl:+.1f}% vs avg)" if pnl is not None else "Bullish momentum"
    if "overweight" in action.lower():
        return f"Position ~{weight:.0f}% of portfolio with weak momentum" if weight else "Overweight"
    if "DO NOT" in action:
        return "Weak session — hold core only if long-term strong"
    if "PARTIAL" in action:
        return f"Large gain ({pnl:+.1f}%) — momentum fading" if pnl is not None else "Book profits"
    return "Mixed signals; wait for clearer edge"


def _holding_priority(action: str) -> int:
    if any(x in action for x in ("EXIT", "TRIM", "REVIEW")):
        return 1
    if "REDUCE" in action or "PARTIAL" in action:
        return 2
    if "ADD" in action or "OK to add" in action:
        return 3
    if "DO NOT" in action:
        return 3
    return 5


def _watchlist_reason(action: str, combined, tech: float, fund: float, intraday_action: str | None, session_bias: str | None) -> str:
    if "AVOID" in action:
        return "Bearish combined/technical signal — not a buy candidate"
    if "BUY WATCH" in action:
        return "Bullish trend + quality — wait for entry trigger"
    if "INTRADAY" in action:
        return "Live session buy setup — consider small starter"
    if "ACCUMULATE" in action:
        return "Strong fundamentals; buy on dips near support"
    if "WAIT" in action:
        return "Do not initiate longs until session stabilizes"
    if "MONITOR" in action and tech > 10:
        return "Trend positive but no urgent trigger today"
    return "No clear edge; keep on radar"


def _watchlist_priority(action: str) -> int:
    if "BUY WATCH" in action or "INTRADAY" in action:
        return 1
    if "AVOID" in action or "ACCUMULATE" in action:
        return 2
    if "WAIT" in action:
        return 3
    return 4


def analyze_holding(
    h: ZerodhaHolding,
    period: str = "1y",
    weight_pct: float | None = None,
) -> HoldingDailyAdvice:
    sym = h.yahoo_symbol or h.tradingsymbol
    try:
        df, info = fetch_stock_data(sym, period=period, market="india", enrich_nse=False)
        df = add_indicators(df)
        combined = analyze_combined(df, info["symbol"], yf_info=info)
        tech = combined.technical.composite_score
        fund = combined.fundamental.composite_score
        last = h.last_price or combined.technical.current_price

        intraday_action = None
        session_bias = None
        try:
            idf, _ = fetch_intraday(sym, "5m", "india")
            verdict = analyze_live_chart(idf, sym, "5m")
            intraday_action = verdict.action
            session_bias = verdict.session_bias
        except Exception:
            pass

        pnl = _pnl_pct(h)
        if h.quantity <= 0:
            advice = HoldingDailyAdvice(
                kite_symbol=h.kite_symbol,
                name=info.get("name", h.tradingsymbol),
                yahoo_symbol=info["symbol"],
                quantity=h.quantity,
                last_price=last,
                avg_price=h.average_price,
                pnl_pct=pnl,
                portfolio_weight_pct=weight_pct,
                today_action="MONITOR — neutral",
                today_reason="",
                short_term=_short_term_label(tech, intraday_action, session_bias),
                long_term=_long_term_label(fund, combined.combined_recommendation),
                combined_score=combined.combined_score,
                technical_score=tech,
                fundamental_score=fund,
                priority=5,
            )
            from analyzer.decision_engine.verdict_bridge import attach_decision_to_holding_advice

            attach_decision_to_holding_advice(
                advice,
                combined_rec=combined.combined_recommendation,
                tech=tech,
                fund=fund,
                intraday_action=intraday_action,
                session_bias=session_bias,
                is_watchlist=True,
            )
            advice.today_reason = _watchlist_reason(advice.today_action, combined, tech, fund, intraday_action, session_bias)
            advice.priority = _watchlist_priority(advice.today_action)
            return advice

        advice = HoldingDailyAdvice(
            kite_symbol=h.kite_symbol,
            name=info.get("name", h.tradingsymbol),
            yahoo_symbol=info["symbol"],
            quantity=h.quantity,
            last_price=last,
            avg_price=h.average_price,
            pnl_pct=pnl,
            portfolio_weight_pct=weight_pct,
            today_action="HOLD — no urgency",
            today_reason="",
            short_term=_short_term_label(tech, intraday_action, session_bias),
            long_term=_long_term_label(fund, combined.combined_recommendation),
            combined_score=combined.combined_score,
            technical_score=tech,
            fundamental_score=fund,
            priority=5,
        )
        from analyzer.decision_engine.verdict_bridge import attach_decision_to_holding_advice

        attach_decision_to_holding_advice(
            advice,
            combined_rec=combined.combined_recommendation,
            tech=tech,
            fund=fund,
            pnl=pnl,
            weight=weight_pct,
            intraday_action=intraday_action,
            session_bias=session_bias,
            is_watchlist=False,
        )
        advice.today_reason = _holding_reason(advice.today_action, combined, tech, pnl, weight_pct, session_bias)
        advice.priority = _holding_priority(advice.today_action)
        return advice
    except Exception as exc:
        return HoldingDailyAdvice(
            kite_symbol=h.kite_symbol,
            name=h.tradingsymbol,
            yahoo_symbol=sym,
            quantity=h.quantity,
            last_price=h.last_price,
            avg_price=h.average_price,
            pnl_pct=_pnl_pct(h),
            portfolio_weight_pct=weight_pct,
            today_action="—",
            today_reason="Analysis failed",
            short_term="—",
            long_term="—",
            combined_score=0.0,
            technical_score=0.0,
            fundamental_score=0.0,
            priority=5,
            error=str(exc),
        )


def _quick_scan(symbol: str, period: str = "6mo") -> tuple | None:
    try:
        df, info = fetch_stock_data(symbol, period=period, market="india", enrich_nse=False)
        df = add_indicators(df)
        combined = analyze_combined(df, info["symbol"], yf_info=info)
        price = float(info.get("current_price") or df["Close"].iloc[-1])
        return combined, info, price
    except Exception:
        return None


def scan_short_term_picks(
    exclude_symbols: set[str] | None = None,
    period: str = "6mo",
    limit: int = 5,
) -> list[StockPick]:
    exclude = {s.upper().replace(".NS", "") for s in (exclude_symbols or set())}
    picks: list[StockPick] = []

    for sym in SHORT_TERM_UNIVERSE:
        if sym.upper() in exclude:
            continue
        row = _quick_scan(sym, period)
        if not row:
            continue
        combined, info, price = row
        df, _ = fetch_stock_data(sym, period=period, market="india", enrich_nse=False)
        df = add_indicators(df)
        short = analyze_short_term_chart(df)
        tech = short.score
        if tech < 15:
            continue
        intraday_note = ""
        try:
            idf, _ = fetch_intraday(sym, "5m", "india")
            v = analyze_live_chart(idf, sym, "5m")
            intraday_note = f" · Intraday: {v.action}"
        except Exception:
            pass
        picks.append(StockPick(
            symbol=info["symbol"],
            name=info.get("name", sym),
            price=price,
            horizon="short",
            action=short.action,
            score=tech,
            reason=short.summary.replace("**", "") + intraday_note,
        ))

    picks.sort(key=lambda p: -p.score)
    return picks[:limit]


def scan_long_term_picks(
    exclude_symbols: set[str] | None = None,
    period: str = "1y",
    limit: int = 5,
) -> list[StockPick]:
    exclude = {s.upper().replace(".NS", "") for s in (exclude_symbols or set())}
    picks: list[StockPick] = []

    for sym in LONG_TERM_UNIVERSE:
        if sym.upper() in exclude:
            continue
        row = _quick_scan(sym, period)
        if not row:
            continue
        combined, info, price = row
        df, _ = fetch_stock_data(sym, period=period, market="india", enrich_nse=False)
        df = add_indicators(df)
        long = analyze_long_term_chart(df, yf_info=info)
        if long.score < 12:
            continue
        picks.append(StockPick(
            symbol=info["symbol"],
            name=info.get("name", sym),
            price=price,
            horizon="long",
            action=long.action if long.action in ("CORE BUY", "ACCUMULATE") else "WATCHLIST",
            score=long.score,
            reason=long.summary.replace("**", ""),
        ))

    picks.sort(key=lambda p: -p.score)
    return picks[:limit]


def build_daily_briefing(
    import_result: ZerodhaImportResult,
    period: str = "1y",
    include_market_picks: bool = True,
) -> DailyBriefing:
    """Full daily report for portfolio + watchlist + market ideas."""
    now = _now_ist()
    all_rows = import_result.holdings
    held_rows = [h for h in all_rows if h.quantity > 0]
    watch_rows = [h for h in all_rows if h.quantity <= 0]
    weights = _portfolio_weights(held_rows)
    errors: list[str] = list(import_result.errors)

    holding_advices: list[HoldingDailyAdvice] = []
    for h in held_rows:
        w = weights.get(h.yahoo_symbol or h.kite_symbol)
        holding_advices.append(analyze_holding(h, period=period, weight_pct=w))
    for h in watch_rows:
        holding_advices.append(analyze_holding(h, period=period, weight_pct=None))

    holding_advices.sort(key=lambda x: (x.priority, -abs(x.combined_score)))

    owned = {h.yahoo_symbol.replace(".NS", "").replace(".BO", "") for h in all_rows}
    owned |= {h.tradingsymbol.upper() for h in all_rows}

    short_picks: list[StockPick] = []
    long_picks: list[StockPick] = []
    if include_market_picks:
        try:
            short_picks = scan_short_term_picks(exclude_symbols=owned, period="6mo")
        except Exception as exc:
            errors.append(f"Short-term scan: {exc}")
        try:
            long_picks = scan_long_term_picks(exclude_symbols=owned, period=period)
        except Exception as exc:
            errors.append(f"Long-term scan: {exc}")

    try:
        indices = india_market_pulse("6mo")
        market_verdict = overall_market_verdict(indices)
    except Exception:
        market_verdict = "Unknown"

    from analyzer.context_engine import build_context_snapshot

    ctx = build_context_snapshot(period=period, use_cache=True)
    global_bias = str(ctx.global_market_state.get("bias", "NEUTRAL"))

    priority: list[str] = []
    for h in holding_advices:
        if h.error or h.priority > 2:
            continue
        label = f"Watchlist **{h.kite_symbol}**" if h.quantity <= 0 else f"**{h.kite_symbol}**"
        if h.quantity > 0:
            pnl_s = f" (P&L {h.pnl_pct:+.1f}%)" if h.pnl_pct is not None else ""
            priority.append(f"{label} — {h.today_action}{pnl_s}: {h.today_reason}")
        else:
            priority.append(f"{label} — {h.today_action}: {h.today_reason}")

    if not priority and holding_advices:
        priority.append("No urgent actions — maintain discipline and review at close.")

    valid = [h for h in holding_advices if not h.error]
    held_valid = [h for h in valid if h.quantity > 0]
    watch_valid = [h for h in valid if h.quantity <= 0]
    trim = [h for h in held_valid if "TRIM" in h.today_action or "EXIT" in h.today_action]
    add = [h for h in held_valid if "ADD" in h.today_action]
    watch_hot = [h for h in watch_valid if h.priority <= 2]

    summary_parts = [
        f"**{now.strftime('%A, %d %b %Y')}** — {len(held_valid)} holdings"
        + (f", {len(watch_valid)} watchlist" if watch_valid else "")
        + " reviewed.",
        f"Market: **{market_verdict}** · Global bias: **{global_bias}**.",
    ]
    if trim:
        summary_parts.append(f"**Review today:** {', '.join(h.kite_symbol for h in trim[:5])}.")
    if add:
        summary_parts.append(f"**Add candidates (in portfolio):** {', '.join(h.kite_symbol for h in add[:3])}.")
    if watch_hot:
        summary_parts.append(
            f"**Watchlist alerts:** {', '.join(h.kite_symbol for h in watch_hot[:5])}."
        )
    if short_picks:
        summary_parts.append(
            f"**Short-term ideas (not in portfolio):** {', '.join(p.symbol.replace('.NS', '') for p in short_picks[:3])}."
        )
    if long_picks:
        summary_parts.append(
            f"**Long-term ideas:** {', '.join(p.symbol.replace('.NS', '') for p in long_picks[:3])}."
        )

    return DailyBriefing(
        date=now.strftime("%Y-%m-%d"),
        generated_at=now.strftime("%Y-%m-%d %H:%M IST"),
        market_verdict=market_verdict,
        global_bias=global_bias,
        holdings_count=len(held_rows),
        watchlist_count=len(watch_rows),
        priority_actions=priority[:8],
        holdings=holding_advices,
        short_term_picks=short_picks,
        long_term_picks=long_picks,
        summary="\n\n".join(summary_parts),
        errors=errors,
    )


def briefing_data_dir() -> Path:
    d = Path(__file__).resolve().parent.parent / "data"
    d.mkdir(exist_ok=True)
    return d


def save_briefing(briefing: DailyBriefing) -> Path:
    path = briefing_data_dir() / f"daily_briefing_{briefing.date}.json"
    payload = {
        "date": briefing.date,
        "generated_at": briefing.generated_at,
        "market_verdict": briefing.market_verdict,
        "global_bias": briefing.global_bias,
        "summary": briefing.summary,
        "priority_actions": briefing.priority_actions,
        "holdings": [asdict(h) for h in briefing.holdings],
        "short_term_picks": [asdict(p) for p in briefing.short_term_picks],
        "long_term_picks": [asdict(p) for p in briefing.long_term_picks],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        from analyzer.suggestion_journal import record_from_daily_briefing
        record_from_daily_briefing(briefing)
    except Exception:
        pass
    return path


def load_today_briefing() -> dict | None:
    today = _now_ist().strftime("%Y-%m-%d")
    path = briefing_data_dir() / f"daily_briefing_{today}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
