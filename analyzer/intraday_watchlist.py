"""
Pre-market intraday watchlist — prepare one session ahead.

Nightly routine: market trend, sector strength, liquidity, ATR, RSI/MACD,
pivot S/R levels, news flag, lean shortlist with entry/stop/target written down.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.intraday_trade_plan import build_intraday_trade_plan

MIN_ATR_PCT = 1.5
MIN_VOLUME_RATIO = 1.0
RSI_BULL_MIN = 55.0
RSI_BULL_MAX = 65.0
RSI_BEAR_MIN = 35.0
RSI_BEAR_MAX = 45.0
MAX_WATCHLIST = 8


def _gates() -> dict:
    """Learned screening gates (updated daily from target-hit history)."""
    from analyzer.watchlist_learning import get_watchlist_strategy

    return get_watchlist_strategy()


@dataclass
class PivotLevels:
    pivot: float
    r1: float
    r2: float
    s1: float
    s2: float


@dataclass
class ProChecklist:
    volume_ok: bool
    atr_ok: bool
    rsi_macd_ok: bool
    levels_ok: bool
    news_ok: bool
    passed: int
    total: int = 5
    notes: list[str] = field(default_factory=list)


@dataclass
class IntradayWatchlistPick:
    rank: int
    nse_symbol: str
    name: str
    price: float
    sector: str
    prep_score: float
    market_bias: str
    checklist: ProChecklist
    entry: float
    stop_loss: float
    target: float
    pivot: PivotLevels | None
    support: float | None
    resistance: float | None
    atr_pct: float | None
    rsi: float | None
    macd_bullish: bool
    volume_ratio: float | None
    sector_tailwind: bool
    breakout_note: str
    news_note: str
    can_enter: bool
    plan_summary: str
    side: str = "LONG"
    confidence_pct: float | None = None
    intelligence_score: float = 0.0


@dataclass
class IntradayWatchlistReport:
    market_bias: str
    sector_leader: str
    sector_laggard: str
    routine_note: str
    picks: list[IntradayWatchlistPick] = field(default_factory=list)


def floor_pivot_levels(high: float, low: float, close: float) -> PivotLevels:
    """Classic floor pivot from previous session H/L/C."""
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    return PivotLevels(
        pivot=round(pivot, 2),
        r1=round(r1, 2),
        r2=round(r2, 2),
        s1=round(s1, 2),
        s2=round(s2, 2),
    )


def _macd_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    macd_line = signal_line = None
    for col in df.columns:
        if col.startswith("MACD_") and "MACDs" not in col and "MACDh" not in col:
            macd_line = col
        elif "MACDs" in col:
            signal_line = col
    return macd_line, signal_line


def macd_bearish_aligned(df: pd.DataFrame) -> bool:
    """MACD line below signal on latest bar."""
    if len(df) < 2:
        return False
    macd_col, sig_col = _macd_columns(df)
    if not macd_col or not sig_col:
        return False
    cur_m = df[macd_col].iloc[-1]
    cur_s = df[sig_col].iloc[-1]
    if pd.isna(cur_m) or pd.isna(cur_s):
        return False
    return float(cur_m) < float(cur_s)


def macd_bullish_aligned(df: pd.DataFrame) -> bool:
    """MACD line above signal on latest bar."""
    if len(df) < 2:
        return False
    macd_col, sig_col = _macd_columns(df)
    if not macd_col or not sig_col:
        return False
    cur_m = df[macd_col].iloc[-1]
    cur_s = df[sig_col].iloc[-1]
    if pd.isna(cur_m) or pd.isna(cur_s):
        return False
    return float(cur_m) > float(cur_s)


def macd_bearish_cross(df: pd.DataFrame) -> bool:
    """Fresh bearish cross: MACD crossed below signal on latest bar."""
    if len(df) < 3:
        return False
    macd_col, sig_col = _macd_columns(df)
    if not macd_col or not sig_col:
        return False
    cur_m = df[macd_col].iloc[-1]
    cur_s = df[sig_col].iloc[-1]
    prev_m = df[macd_col].iloc[-2]
    prev_s = df[sig_col].iloc[-2]
    if pd.isna(cur_m) or pd.isna(cur_s):
        return False
    return float(cur_m) < float(cur_s) and float(prev_m) >= float(prev_s)


def macd_bullish_cross(df: pd.DataFrame) -> bool:
    """Fresh bullish cross: MACD crossed above signal on latest bar."""
    if len(df) < 3:
        return False
    macd_col, sig_col = _macd_columns(df)
    if not macd_col or not sig_col:
        return False
    cur_m = df[macd_col].iloc[-1]
    cur_s = df[sig_col].iloc[-1]
    prev_m = df[macd_col].iloc[-2]
    prev_s = df[sig_col].iloc[-2]
    if pd.isna(cur_m) or pd.isna(cur_s):
        return False
    if float(cur_m) > float(cur_s) and float(prev_m) <= float(prev_s):
        return True
    return False


def compute_prep_metrics(df: pd.DataFrame) -> dict:
    """ATR%, RSI, MACD, pivots, 20d S/R from daily OHLCV."""
    if df is None or len(df) < 21:
        return {}
    row = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(row["Close"])
    atr = row.get("ATR_14")
    atr_pct = round(float(atr) / price * 100, 2) if atr is not None and not pd.isna(atr) and price else None
    rsi_val = row.get("RSI_14")
    rsi = round(float(rsi_val), 1) if rsi_val is not None and not pd.isna(rsi_val) else None
    tail = df.tail(20)
    resistance = round(float(tail["High"].max()), 2)
    support = round(float(tail["Low"].min()), 2)
    pivots = floor_pivot_levels(
        float(prev["High"]), float(prev["Low"]), float(prev["Close"]),
    )
    breakout = price >= resistance * 0.995
    return {
        "atr_pct": atr_pct,
        "rsi": rsi,
        "macd_bullish": macd_bullish_aligned(df),
        "macd_bullish_cross": macd_bullish_cross(df),
        "macd_bearish": macd_bearish_aligned(df),
        "macd_bearish_cross": macd_bearish_cross(df),
        "pivot": pivots,
        "support": support,
        "resistance": resistance,
        "breakout": breakout,
    }


def _sector_tailwind(sector: str, sector_leader: str) -> bool:
    if not sector or not sector_leader:
        return False
    s = sector.lower()
    lead = sector_leader.lower()
    tokens = ("bank", "it", "auto", "fmcg", "pharma", "metal", "realty", "energy")
    for tok in tokens:
        if tok in lead and tok in s:
            return True
    return lead.split()[0] in s if lead else False


def _market_bias_from_report(report) -> str:
    regime = getattr(report, "regime", None)
    if regime and "Bullish" in getattr(regime, "regime", ""):
        return "BULLISH"
    if regime and "Bearish" in getattr(regime, "regime", ""):
        return "BEARISH"
    for idx in getattr(report, "indices", []) or []:
        if getattr(idx, "symbol", "") in ("^NSEI",) or "Nifty 50" in getattr(idx, "name", ""):
            sc = getattr(idx, "score", 0) or 0
            if sc >= 10:
                return "BULLISH"
            if sc <= -10:
                return "BEARISH"
    return "NEUTRAL"


def _news_note(event) -> tuple[str, bool]:
    if not event:
        return "No flagged corporate event in next 2 weeks.", True
    days = getattr(event, "days_until", None)
    band = getattr(event, "risk_band", "clear")
    detail = getattr(event, "detail", "") or getattr(event, "event_type", "Event")
    if days is not None and 0 <= days <= 1:
        return f"**Catalyst:** {detail} in {days}d — expect volatility; size down.", True
    if band in ("critical", "elevated"):
        return f"**News:** {detail} ({band}) — review before MIS.", True
    return f"Event: {detail} — noted.", True


def _plan_long_levels(
    price: float,
    pivots: PivotLevels,
    support: float,
    resistance: float,
    breakout: bool,
    bias: str,
) -> tuple[float, float, float, str]:
    if bias == "BEARISH":
        entry = min(price, pivots.pivot)
        stop = pivots.r1
        target = pivots.s1
        note = "Bearish market bias — fade toward S1; stop above R1."
    elif breakout:
        entry = max(price, resistance)
        stop = max(pivots.s1, support)
        target = pivots.r2
        note = "Breakout setup — entry above resistance; stop below S1/support."
    else:
        entry = max(price, pivots.pivot)
        stop = pivots.s1
        target = pivots.r1
        note = "Pivot plan — hold above central pivot; target R1."
    return round(entry, 2), round(stop, 2), round(target, 2), note


def _build_checklist(
    stock,
    metrics: dict,
    event,
    sector_tailwind: bool,
    *,
    market_bias: str = "NEUTRAL",
) -> ProChecklist:
    gates = _gates()
    min_vol = float(gates["min_volume_ratio"])
    min_atr = float(gates["min_atr_pct"])
    notes: list[str] = []
    vol_ratio = getattr(stock, "volume_ratio", None)
    volume_ok = vol_ratio is not None and vol_ratio >= min_vol
    if volume_ok:
        notes.append(f"✔ Volume **{vol_ratio:.1f}×** avg (≥ {min_vol}×)")
    else:
        notes.append(f"✘ Volume below average ({vol_ratio or '—'}×)")

    atr_pct = metrics.get("atr_pct") or getattr(stock, "atr_pct", None)
    atr_ok = atr_pct is not None and atr_pct >= min_atr
    if atr_ok:
        notes.append(f"✔ ATR **{atr_pct:.1f}%** (≥ {min_atr}% movement)")
    else:
        notes.append(f"✘ ATR too low ({atr_pct or '—'}%) — flat stock")

    rsi = metrics.get("rsi") or getattr(stock, "rsi_14", None)
    bearish_day = market_bias == "BEARISH"
    if bearish_day:
        macd_cross = metrics.get("macd_bearish_cross")
        macd_aligned = metrics.get("macd_bearish")
        if macd_aligned is None:
            macd_aligned = macd_bearish_aligned(stock.short_chart_df) if getattr(
                stock, "short_chart_df", None
            ) is not None else not metrics.get("macd_bullish", getattr(stock, "macd_bullish", False))
        rsi_min = RSI_BEAR_MIN
        rsi_max = RSI_BEAR_MAX
        rsi_ok = rsi is not None and rsi_min <= rsi <= rsi_max
        macd_ok = bool(macd_cross or macd_aligned)
        rsi_macd_ok = rsi_ok and macd_ok
        if rsi_macd_ok:
            if macd_cross:
                notes.append(f"✔ RSI **{rsi:.0f}** + MACD bearish cross")
            else:
                notes.append(f"✔ RSI **{rsi:.0f}** + MACD bearish (below signal)")
        elif rsi_ok:
            notes.append(f"◐ RSI **{rsi:.0f}** in zone; MACD not confirmed bearish")
        else:
            notes.append(f"✘ RSI/MACD not aligned for short (RSI {rsi or '—'})")
    else:
        macd_cross = metrics.get("macd_bullish_cross")
        macd_aligned = metrics.get("macd_bullish", getattr(stock, "macd_bullish", False))
        rsi_min = float(gates["rsi_bull_min"])
        rsi_max = float(gates["rsi_bull_max"])
        rsi_ok = rsi is not None and rsi_min <= rsi <= rsi_max
        macd_ok = bool(macd_cross or macd_aligned)
        rsi_macd_ok = rsi_ok and macd_ok
        if rsi_macd_ok:
            if macd_cross:
                notes.append(f"✔ RSI **{rsi:.0f}** + MACD bullish cross")
            else:
                notes.append(f"✔ RSI **{rsi:.0f}** + MACD bullish (above signal)")
        elif rsi_ok:
            notes.append(f"◐ RSI **{rsi:.0f}** in zone; MACD not confirmed")
        else:
            notes.append(f"✘ RSI/MACD not aligned (RSI {rsi or '—'})")

    pivots = metrics.get("pivot")
    if pivots is None and getattr(stock, "pivot_p", None):
        pivots = PivotLevels(
            pivot=stock.pivot_p,
            r1=stock.pivot_r1 or stock.pivot_p,
            r2=stock.pivot_r2 or stock.pivot_p,
            s1=stock.pivot_s1 or stock.pivot_p,
            s2=stock.pivot_s2 or stock.pivot_p,
        )
    levels_ok = pivots is not None
    if levels_ok:
        notes.append(f"✔ Pivots mapped — P **₹{pivots.pivot:,.0f}** · R1 **₹{pivots.r1:,.0f}** · S1 **₹{pivots.s1:,.0f}**")
    else:
        notes.append("✘ Pivot levels unavailable")

    news_note, news_ok = _news_note(event)
    notes.append(f"{'✔' if news_ok else '✘'} {news_note}")

    if sector_tailwind:
        if market_bias == "BEARISH":
            notes.append("✔ Sector tailwind — weak/lagging sector for shorts")
        else:
            notes.append("✔ Sector tailwind — leading sector yesterday")

    passed = sum([volume_ok, atr_ok, rsi_macd_ok, levels_ok, news_ok])
    return ProChecklist(
        volume_ok=volume_ok,
        atr_ok=atr_ok,
        rsi_macd_ok=rsi_macd_ok,
        levels_ok=levels_ok,
        news_ok=news_ok,
        passed=passed,
        notes=notes,
    )


def prep_routine_summary() -> str:
    return (
        "**Prepare tonight, trade tomorrow:** check Nifty trend → leading sector → "
        "volume + ATR filter → RSI/MACD → pivot S/R → news. "
        "Only stocks with **entry, stop, and target** make the list. **Quality over quantity** (max 8)."
    )


def build_intraday_watchlist(report, *, limit: int | None = None) -> IntradayWatchlistReport:
    """Build lean pre-session MIS watchlist from Market Pulse scan data."""
    gates = _gates()
    limit = limit if limit is not None else int(gates["max_watchlist"])
    min_passed = int(gates["min_checklist_passed"])
    min_prep = float(gates["min_prep_score"])
    require_macd = bool(gates["require_rsi_macd"])
    require_tailwind = bool(gates["require_sector_tailwind"])
    min_atr = float(gates["min_atr_pct"])
    macro = getattr(report, "macro", None)
    sector_leader = getattr(macro, "sector_leader", "") if macro else ""
    sector_laggard = getattr(macro, "sector_laggard", "") if macro else ""
    market_bias = _market_bias_from_report(report)
    earn_map = getattr(report, "earnings_by_nse", {}) or {}

    candidates: list[tuple[float, IntradayWatchlistPick]] = []

    for stock in getattr(report, "stock_map", {}).values():
        if stock.error or stock.price <= 0:
            continue

        metrics: dict = {}
        if stock.short_chart_df is not None:
            metrics = compute_prep_metrics(stock.short_chart_df)
        elif stock.long_chart_df is not None:
            metrics = compute_prep_metrics(stock.long_chart_df)
        else:
            metrics = {
                "atr_pct": stock.atr_pct,
                "rsi": stock.rsi_14,
                "macd_bullish": stock.macd_bullish,
                "support": stock.support_20d,
                "resistance": stock.resistance_20d,
                "breakout": (
                    stock.resistance_20d is not None
                    and stock.price >= stock.resistance_20d * 0.995
                ),
            }
            if stock.pivot_p is not None:
                metrics["pivot"] = PivotLevels(
                    pivot=stock.pivot_p,
                    r1=stock.pivot_r1 or stock.pivot_p,
                    r2=stock.pivot_r2 or stock.pivot_p,
                    s1=stock.pivot_s1 or stock.pivot_p,
                    s2=stock.pivot_s2 or stock.pivot_p,
                )

        pivots = metrics.get("pivot")
        sector = getattr(stock, "sector", "") or ""
        sector_ref = sector_laggard if market_bias == "BEARISH" else sector_leader
        tailwind = _sector_tailwind(sector, sector_ref)
        event = earn_map.get(stock.nse_symbol.upper())
        checklist = _build_checklist(stock, metrics, event, tailwind, market_bias=market_bias)

        if checklist.passed < min_passed or not checklist.atr_ok:
            continue
        if require_macd and not checklist.rsi_macd_ok:
            continue
        if require_tailwind and not tailwind:
            continue

        support = metrics.get("support") or getattr(stock, "support_20d", None)
        resistance = metrics.get("resistance") or getattr(stock, "resistance_20d", None)
        if not pivots or support is None or resistance is None:
            continue

        entry, stop, target, breakout_note = _plan_long_levels(
            stock.price,
            pivots,
            support,
            resistance,
            metrics.get("breakout", False),
            market_bias,
        )
        action = "BUY" if market_bias != "BEARISH" else "SELL"
        side = "SHORT" if action == "SELL" else "LONG"
        bearish_day = market_bias == "BEARISH"
        plan = build_intraday_trade_plan(action, entry, stop, target)

        prep_score = (
            checklist.passed * 12
            + (10 if tailwind else 0)
            + (stock.combined_score * 0.15 if stock.combined_score else 0)
        )
        intraday_action = None
        if stock.intraday:
            intraday_action = stock.intraday.action
            if bearish_day and stock.intraday.action in ("STRONG SELL", "SELL"):
                prep_score += 8
            elif not bearish_day and stock.intraday.action in ("STRONG BUY", "BUY"):
                prep_score += 8
        if prep_score < min_prep:
            continue
        if (metrics.get("atr_pct") or 0) < min_atr:
            continue

        from analyzer.suggestion_features import (
            build_session_profile,
            build_suggestion_features,
            score_suggestion,
        )

        session_prof = build_session_profile(getattr(stock, "intraday_df", None))
        feats = build_suggestion_features(
            metrics=metrics,
            checklist=checklist,
            sector_tailwind=tailwind,
            market_bias=market_bias,
            combined_score=float(stock.combined_score or 0),
            volume_ratio=stock.volume_ratio,
            intraday_action=intraday_action,
            session=session_prof,
            prep_score_base=prep_score,
        )
        intel_score, confidence = score_suggestion(feats)
        rank_score = prep_score * 0.4 + intel_score * 0.6

        news_note, _ = _news_note(event)
        pick = IntradayWatchlistPick(
            rank=0,
            nse_symbol=stock.nse_symbol,
            name=stock.name,
            price=stock.price,
            sector=sector or "—",
            prep_score=round(prep_score, 1),
            market_bias=market_bias,
            checklist=checklist,
            entry=entry,
            stop_loss=stop,
            target=target,
            pivot=pivots,
            support=support,
            resistance=resistance,
            atr_pct=metrics.get("atr_pct") or getattr(stock, "atr_pct", None),
            rsi=metrics.get("rsi") or getattr(stock, "rsi_14", None),
            macd_bullish=metrics.get("macd_bullish", getattr(stock, "macd_bullish", False)),
            volume_ratio=stock.volume_ratio,
            sector_tailwind=tailwind,
            breakout_note=breakout_note,
            news_note=news_note,
            can_enter=plan.can_enter,
            plan_summary=plan.summary,
            side=side,
            confidence_pct=confidence,
            intelligence_score=intel_score,
        )
        candidates.append((rank_score, pick))

    candidates.sort(key=lambda x: -x[0])
    picks = []
    for rank, (_, pick) in enumerate(candidates[:limit], start=1):
        pick.rank = rank
        picks.append(pick)

    return IntradayWatchlistReport(
        market_bias=market_bias,
        sector_leader=sector_leader or "—",
        sector_laggard=sector_laggard or "—",
        routine_note=prep_routine_summary(),
        picks=picks,
    )
