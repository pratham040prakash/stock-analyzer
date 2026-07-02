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
from analyzer.global_impact import build_india_impact_report
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


def _today_action(
    combined_rec: str,
    tech: float,
    fund: float,
    pnl: float | None,
    weight: float | None,
    intraday_action: str | None,
    session_bias: str | None,
) -> tuple[str, str, int]:
    """Return (action, reason, priority 1-5)."""
    overweight = weight is not None and weight > 12

    if combined_rec in ("STRONG SELL", "SELL"):
        reason = "Bearish combined signal"
        if pnl is not None and pnl > 15:
            return "TRIM — book profits", f"{reason}; you're up {pnl:+.1f}%", 1
        if pnl is not None and pnl < -10:
            return "EXIT — cut loss", f"{reason}; down {pnl:.1f}% — protect capital", 1
        return "REDUCE position", reason, 2

    if overweight and tech < 0:
        return "TRIM — overweight", f"Position ~{weight:.0f}% of portfolio with weak momentum", 2

    if session_bias == "BEARISH" and tech < -15:
        if pnl is not None and pnl < -8:
            return "REVIEW stop-loss", "Intraday + swing bearish while in loss", 1
        return "DO NOT add today", "Weak session — hold core only if long-term strong", 3

    if combined_rec in ("STRONG BUY", "BUY") and tech > 15:
        if pnl is not None and pnl < -8 and fund > 10:
            return "ADD in tranches", f"Quality name in pullback ({pnl:+.1f}% vs avg)", 2
        return "HOLD / add small", "Bullish momentum — trail stop below SMA-20", 4

    if fund > 15 and tech < 5:
        return "HOLD — long view", "Strong fundamentals; ignore short-term noise", 5

    if intraday_action == "BUY" and tech > 5:
        return "OK to add (small)", "Intraday buy setup with positive trend", 3

    if pnl is not None and pnl > 25 and tech < 10:
        return "PARTIAL book profit", f"Large gain ({pnl:+.1f}%) — momentum fading", 2

    return "HOLD — no urgency", "Mixed signals; wait for clearer edge", 5


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
        today, reason, priority = _today_action(
            combined.combined_recommendation,
            tech,
            fund,
            pnl,
            weight_pct,
            intraday_action,
            session_bias,
        )

        return HoldingDailyAdvice(
            kite_symbol=h.kite_symbol,
            name=info.get("name", h.tradingsymbol),
            yahoo_symbol=info["symbol"],
            quantity=h.quantity,
            last_price=last,
            avg_price=h.average_price,
            pnl_pct=pnl,
            portfolio_weight_pct=weight_pct,
            today_action=today,
            today_reason=reason,
            short_term=_short_term_label(tech, intraday_action, session_bias),
            long_term=_long_term_label(fund, combined.combined_recommendation),
            combined_score=combined.combined_score,
            technical_score=tech,
            fundamental_score=fund,
            priority=priority,
        )
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
    """Full daily report for portfolio + market ideas."""
    now = _now_ist()
    holdings = import_result.holdings
    weights = _portfolio_weights(holdings)
    errors: list[str] = list(import_result.errors)

    holding_advices: list[HoldingDailyAdvice] = []
    for h in holdings:
        w = weights.get(h.yahoo_symbol or h.kite_symbol)
        holding_advices.append(analyze_holding(h, period=period, weight_pct=w))

    holding_advices.sort(key=lambda x: (x.priority, -abs(x.combined_score)))

    owned = {h.yahoo_symbol.replace(".NS", "").replace(".BO", "") for h in holdings}
    owned |= {h.tradingsymbol.upper() for h in holdings}

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

    global_bias = "NEUTRAL"
    try:
        impact = build_india_impact_report()
        global_bias = impact.predicted_nifty_bias
    except Exception:
        pass

    priority: list[str] = []
    for h in holding_advices:
        if h.error or h.priority > 2:
            continue
        pnl_s = f" (P&L {h.pnl_pct:+.1f}%)" if h.pnl_pct is not None else ""
        priority.append(f"**{h.kite_symbol}** — {h.today_action}{pnl_s}: {h.today_reason}")

    if not priority and holding_advices:
        priority.append("No urgent actions — maintain discipline and review at close.")

    valid = [h for h in holding_advices if not h.error]
    trim = [h for h in valid if "TRIM" in h.today_action or "EXIT" in h.today_action]
    add = [h for h in valid if "ADD" in h.today_action]

    summary_parts = [
        f"**{now.strftime('%A, %d %b %Y')}** — {len(valid)} holdings reviewed.",
        f"Market: **{market_verdict}** · Global bias: **{global_bias}**.",
    ]
    if trim:
        summary_parts.append(f"**Review today:** {', '.join(h.kite_symbol for h in trim[:5])}.")
    if add:
        summary_parts.append(f"**Add candidates (in portfolio):** {', '.join(h.kite_symbol for h in add[:3])}.")
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
        holdings_count=len(holdings),
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
