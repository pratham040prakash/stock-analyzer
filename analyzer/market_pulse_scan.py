"""Market Pulse — intraday + short + long with regime, macro, cache, Nifty 50."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import pandas as pd

from analyzer.candle_narrative import LiveChartVerdict, analyze_live_chart
from analyzer.chart_horizon import (
    HorizonAnalysis,
    analyze_intraday_horizon,
    analyze_long_term_chart,
    analyze_short_term_chart,
)
from analyzer.combined import analyze_combined
from analyzer.data import fetch_stock_data
from analyzer.india import NIFTY_50
from analyzer.india_macro import IndiaMacroSnapshot
from analyzer.indicators import add_indicators
from analyzer.intraday_data import fetch_intraday
from analyzer.market_regime import MarketRegime, apply_regime_to_action
from analyzer.nse_options import (
    NSEOptionChain,
    NSEOptionPick,
    enrich_with_nse_chain,
)
from analyzer.kite_stream import get_kite_ltp_cached
from analyzer.delivery_quality import (
    delivery_by_nse,
    delivery_note_for_horizon,
    enrich_delivery_with_stocks,
    fetch_delivery_batch,
    should_downgrade_for_delivery,
)
from analyzer.earnings_calendar import (
    earnings_note_for_pick,
    events_by_nse,
    fetch_nifty50_earnings,
    should_skip_pick,
)
from analyzer.threshold_tuning import get_pulse_thresholds
from analyzer.intraday_stock_picker import (
    combined_intraday_rank,
    investopedia_screen_summary,
    screen_intraday_stock,
)

# Re-export top 10 for display table
MARKET_PULSE_TOP_10 = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY",
    "SBIN", "BHARTIARTL", "ITC", "LT", "AXISBANK",
]

MARKET_PULSE_SCAN_UNIVERSE = list(dict.fromkeys(NIFTY_50))

INDEX_FNO_SYMBOLS = [
    ("NIFTY", "Nifty 50", "^NSEI"),
    ("BANKNIFTY", "Nifty Bank", "^NSEBANK"),
]

INTRADAY_MIN_SCORE = 35
SHORT_TERM_MIN_SCORE = 22
LONG_TERM_MIN_SCORE = 28
CACHE_TTL = 900  # 15 min
SCAN_WORKERS = 10

BUY_ACTIONS_INTRADAY = ("STRONG BUY", "BUY")
BUY_ACTIONS_SHORT = ("STRONG BUY", "BUY")
BUY_ACTIONS_LONG = ("CORE BUY", "ACCUMULATE")


@dataclass
class IndexOptionsPulse:
    fno_symbol: str
    name: str
    index_pulse: IndexPulse | None
    options_action: str
    chain: NSEOptionChain | None = None
    picks: list[NSEOptionPick] = field(default_factory=list)
    options_analytics: object | None = None
    error: str | None = None


@dataclass
class ChartStockPick:
    symbol: str
    nse_symbol: str
    name: str
    price: float
    action: str
    score: float
    horizon: str
    timeframe: str
    entry_hint: str
    stop_hint: str
    target_hint: str
    chart_signals: list[str] = field(default_factory=list)
    summary: str = ""
    regime_note: str = ""
    trade_type: str = "Delivery"  # Delivery | MIS
    screen_score: float = 0.0
    screen_notes: list[str] = field(default_factory=list)


@dataclass
class StockPulseEntry:
    symbol: str
    nse_symbol: str
    name: str
    price: float
    combined_rec: str
    combined_score: float
    intraday: HorizonAnalysis | None = None
    short_term: HorizonAnalysis | None = None
    long_term: HorizonAnalysis | None = None
    intraday_verdict: LiveChartVerdict | None = None
    intraday_df: pd.DataFrame | None = None
    short_chart_df: pd.DataFrame | None = None
    long_chart_df: pd.DataFrame | None = None
    what_to_do: str = ""
    ltp_source: str = "Yahoo"
    volume_ratio: float | None = None
    price_change_pct: float | None = None
    avg_daily_volume: float | None = None
    daily_range_pct: float | None = None
    nifty_correlation: float | None = None
    sector: str = ""
    atr_pct: float | None = None
    rsi_14: float | None = None
    macd_bullish: bool = False
    pivot_p: float | None = None
    pivot_r1: float | None = None
    pivot_r2: float | None = None
    pivot_s1: float | None = None
    pivot_s2: float | None = None
    support_20d: float | None = None
    resistance_20d: float | None = None
    error: str | None = None

    @property
    def chart_df(self) -> pd.DataFrame | None:
        return self.short_chart_df


@dataclass
class MarketPulseReport:
    indices: list[IndexPulse]
    market_verdict: str
    index_options: list[IndexOptionsPulse]
    top_stocks: list[StockPulseEntry]
    stock_map: dict[str, StockPulseEntry] = field(default_factory=dict)
    intraday_picks: list[ChartStockPick] = field(default_factory=list)
    short_term_picks: list[ChartStockPick] = field(default_factory=list)
    long_term_picks: list[ChartStockPick] = field(default_factory=list)
    regime: MarketRegime | None = None
    macro: IndiaMacroSnapshot | None = None
    from_cache: bool = False
    strongest_ce: list[str] = field(default_factory=list)
    strongest_pe: list[str] = field(default_factory=list)
    strongest_equity: list[str] = field(default_factory=list)
    earnings_events: list = field(default_factory=list)
    earnings_by_nse: dict = field(default_factory=dict)
    delivery_snapshots: list = field(default_factory=list)
    delivery_by_nse: dict = field(default_factory=dict)


def _index_options_action(pulse: IndexPulse | None, intraday_action: str | None) -> str:
    if intraday_action and intraday_action not in ("NO TRADE", "WAIT", "HOLD"):
        if intraday_action in BUY_ACTIONS_INTRADAY:
            return "BUY CE"
        if "CE" in intraday_action:
            return intraday_action
        if intraday_action in ("SELL", "STRONG SELL") or "PE" in intraday_action:
            return "BUY PE" if "PE" not in intraday_action else intraday_action
    if not pulse:
        return "NO TRADE"
    if pulse.score >= 25:
        return "STRONG CE"
    if pulse.score >= 10:
        return "BUY CE"
    if pulse.score <= -25:
        return "STRONG PE"
    if pulse.score <= -10:
        return "BUY PE"
    return "NO TRADE"


def _what_to_do(
    intraday: HorizonAnalysis | None,
    short: HorizonAnalysis,
    long: HorizonAnalysis,
) -> str:
    parts: list[str] = []
    if intraday:
        parts.append(
            f"**Intraday** ({intraday.timeframe}): **{intraday.action}** ({intraday.score:+.0f})"
        )
    parts.extend([
        f"**Short-term** ({short.timeframe}): **{short.action}** ({short.score:+.0f})",
        f"**Long-term** ({long.timeframe}): **{long.action}** ({long.score:+.0f})",
    ])
    buys = sum(
        1 for h in (intraday, short, long)
        if h and h.action in (*BUY_ACTIONS_INTRADAY, *BUY_ACTIONS_SHORT, *BUY_ACTIONS_LONG)
    )
    if buys >= 2:
        parts.append("→ **Multi-timeframe BUY alignment**")
    return " · ".join(parts)


def _horizon_to_pick(
    nse: str, name: str, sym: str, price: float, h: HorizonAnalysis,
    regime: MarketRegime | None, regime_note: str = "",
    *,
    screen_score: float = 0.0,
    screen_notes: list[str] | None = None,
) -> ChartStockPick:
    action, score, note = h.action, h.score, regime_note
    if regime:
        action, score, rnote = apply_regime_to_action(action, score, h.horizon, regime)
        if rnote:
            regime_note = rnote
    trade_type = "MIS" if h.horizon == "intraday" else "Delivery"
    return ChartStockPick(
        symbol=sym,
        nse_symbol=nse,
        name=name,
        price=price,
        action=action,
        score=score,
        horizon=h.horizon,
        timeframe=h.timeframe,
        entry_hint=h.entry_hint,
        stop_hint=h.stop_hint,
        target_hint=h.target_hint,
        chart_signals=h.chart_signals,
        summary=h.summary,
        regime_note=regime_note,
        trade_type=trade_type,
        screen_score=screen_score,
        screen_notes=list(screen_notes or []),
    )


def scan_index_options(
    fno_symbol: str,
    name: str,
    yahoo_symbol: str,
    period: str,
    index_pulse: IndexPulse | None,
) -> IndexOptionsPulse:
    intraday_action = None
    try:
        df, _ = fetch_intraday(yahoo_symbol, "5m", "india")
        verdict = analyze_live_chart(df, fno_symbol, "5m")
        if verdict.options:
            intraday_action = verdict.options.action
        elif verdict.action in BUY_ACTIONS_INTRADAY:
            intraday_action = "BUY CE"
        elif verdict.action in ("SELL", "STRONG SELL"):
            intraday_action = "BUY PE"
    except Exception:
        pass

    action = _index_options_action(index_pulse, intraday_action)
    try:
        from analyzer.options_analytics import analyze_and_record_chain

        chain, picks, err = enrich_with_nse_chain(action, fno_symbol)
        analytics = analyze_and_record_chain(chain) if chain else None
        if err:
            return IndexOptionsPulse(fno_symbol, name, index_pulse, action, None, [], analytics, err)
        return IndexOptionsPulse(fno_symbol, name, index_pulse, action, chain, picks, analytics)
    except Exception as exc:
        return IndexOptionsPulse(fno_symbol, name, index_pulse, action, None, [], None, str(exc))


def scan_stock(
    symbol: str,
    period: str = "1y",
    market: str = "india",
    kite_ltp: dict[str, float] | None = None,
    *,
    charts: bool = True,
    skip_intraday: bool | None = None,
    prior_session_intraday: bool = False,
    nifty_daily_df: pd.DataFrame | None = None,
    market_open: bool = False,
) -> StockPulseEntry:
    nse = symbol.replace(".NS", "").replace(".BO", "")
    name = nse
    price = 0.0
    ltp_source = "Yahoo"

    try:
        fetch_period = "2y" if period in ("3mo", "6mo") else period
        df, info = fetch_stock_data(nse, period=fetch_period, market=market, enrich_nse=False)
        df = add_indicators(df)
        name = info.get("name", nse)
        price = float(info.get("nse_last_price") or info.get("current_price") or df["Close"].iloc[-1])

        kite_key = f"NSE:{nse}-EQ"
        if kite_ltp and kite_key in kite_ltp:
            price = kite_ltp[kite_key]
            ltp_source = "Kite"

        combined = analyze_combined(df, info["symbol"], yf_info=info)
        short = analyze_short_term_chart(df)
        long = analyze_long_term_chart(df, yf_info=info)

        intraday_h = None
        intraday_verdict = None
        intraday_df = None
        if skip_intraday is None:
            skip_intraday = not market_open and not prior_session_intraday

        if not skip_intraday:
            try:
                idf, _ = fetch_intraday(nse, "5m", market)
                intraday_verdict = analyze_live_chart(idf, nse, "5m")
                intraday_h = analyze_intraday_horizon(intraday_verdict)
                if charts:
                    intraday_df = add_intraday_indicators(idf)
            except Exception:
                intraday_h = HorizonAnalysis(
                    horizon="intraday",
                    action="WAIT",
                    score=0.0,
                    timeframe="Today / MIS (5m chart)",
                    entry_hint="Intraday data unavailable",
                    stop_hint="—",
                    target_hint="—",
                    summary="Could not load 5m chart",
                )
        else:
            intraday_h = HorizonAnalysis(
                horizon="intraday",
                action="WAIT",
                score=0.0,
                timeframe="Today / MIS (5m chart)",
                entry_hint="Market closed",
                stop_hint="—",
                target_hint="—",
                summary="Intraday inactive while NSE is closed",
            )

        short_chart_df = df.tail(90) if charts else None
        long_chart_df = df.tail(250) if charts else None
        what = _what_to_do(intraday_h, short, long)

        volume_ratio = None
        price_change_pct = None
        avg_daily_volume = None
        daily_range_pct = None
        nifty_correlation = None
        if len(df) >= 2:
            row = df.iloc[-1]
            prev = df.iloc[-2]
            vol_sma = row.get("VOL_SMA_20")
            if vol_sma is not None and not pd.isna(vol_sma) and float(vol_sma) > 0:
                volume_ratio = round(float(row["Volume"]) / float(vol_sma), 2)
            p0, p1 = float(prev["Close"]), float(row["Close"])
            if p0 > 0:
                price_change_pct = round((p1 / p0 - 1) * 100, 2)
        if len(df) >= 20:
            tail = df.tail(20)
            avg_daily_volume = float(tail["Volume"].mean())
            ranges = (tail["High"] - tail["Low"]) / tail["Close"].replace(0, pd.NA) * 100
            daily_range_pct = round(float(ranges.mean()), 2)
            if nifty_daily_df is not None:
                from analyzer.intraday_stock_picker import rolling_nifty_correlation
                nifty_correlation = rolling_nifty_correlation(df, nifty_daily_df)

        from analyzer.intraday_watchlist import compute_prep_metrics

        prep = compute_prep_metrics(df)
        piv = prep.get("pivot")

        return StockPulseEntry(
            symbol=info["symbol"],
            nse_symbol=nse,
            name=name,
            price=price,
            combined_rec=combined.combined_recommendation,
            combined_score=combined.combined_score,
            intraday=intraday_h,
            short_term=short,
            long_term=long,
            intraday_verdict=intraday_verdict if charts else None,
            intraday_df=intraday_df,
            short_chart_df=short_chart_df,
            long_chart_df=long_chart_df,
            what_to_do=what,
            ltp_source=ltp_source,
            volume_ratio=volume_ratio,
            price_change_pct=price_change_pct,
            avg_daily_volume=avg_daily_volume,
            daily_range_pct=daily_range_pct,
            nifty_correlation=nifty_correlation,
            sector=str(info.get("sector") or ""),
            atr_pct=prep.get("atr_pct"),
            rsi_14=prep.get("rsi"),
            macd_bullish=bool(prep.get("macd_bullish")),
            pivot_p=piv.pivot if piv else None,
            pivot_r1=piv.r1 if piv else None,
            pivot_r2=piv.r2 if piv else None,
            pivot_s1=piv.s1 if piv else None,
            pivot_s2=piv.s2 if piv else None,
            support_20d=prep.get("support"),
            resistance_20d=prep.get("resistance"),
        )
    except Exception as exc:
        return StockPulseEntry(
            symbol=f"{nse}.NS",
            nse_symbol=nse,
            name=name,
            price=price,
            combined_rec="ERROR",
            combined_score=0,
            what_to_do=f"Scan failed: {exc}",
            error=str(exc),
        )


def _collect_picks(
    stocks: list[StockPulseEntry],
    regime: MarketRegime | None,
    earnings_by_nse: dict | None = None,
    delivery_by_nse_map: dict | None = None,
    *,
    skip_earnings_week: bool = False,
    filter_weak_delivery: bool = False,
    nifty_daily_df: pd.DataFrame | None = None,
) -> tuple[list[ChartStockPick], list[ChartStockPick], list[ChartStockPick]]:
    intraday_picks: list[ChartStockPick] = []
    short_picks: list[ChartStockPick] = []
    long_picks: list[ChartStockPick] = []
    gates = get_pulse_thresholds()
    intraday_min = gates["intraday"]
    short_min = gates["short"]
    long_min = gates["long"]
    earn_map = earnings_by_nse or {}
    del_map = delivery_by_nse_map or {}
    nifty_bias = "NEUTRAL"
    if regime:
        reg = regime.regime.upper()
        if "BULLISH" in reg:
            nifty_bias = "BULLISH"
        elif "BEARISH" in reg:
            nifty_bias = "BEARISH"

    for s in stocks:
        if s.error or not s.short_term or not s.long_term:
            continue
        ev = earn_map.get(s.nse_symbol.upper())
        dv = del_map.get(s.nse_symbol.upper())
        intra_note = earnings_note_for_pick(ev, "intraday")
        del_intra = delivery_note_for_horizon(dv, "intraday")
        if (
            s.intraday
            and s.intraday.score >= intraday_min
            and s.intraday.action in BUY_ACTIONS_INTRADAY
            and not should_skip_pick(ev, "intraday", skip_earnings_week=skip_earnings_week)
            and not should_downgrade_for_delivery(dv, "intraday", filter_weak_delivery=filter_weak_delivery)
        ):
            daily_df = s.short_chart_df if s.short_chart_df is not None else None
            screen = screen_intraday_stock(
                nse_symbol=s.nse_symbol,
                daily_df=daily_df,
                intraday_df=s.intraday_df,
                relative_volume=s.volume_ratio,
                nifty_df=nifty_daily_df,
                trade_action=s.intraday.action,
                nifty_bias=nifty_bias,
                avg_daily_volume=s.avg_daily_volume,
                daily_range_pct=s.daily_range_pct,
                nifty_correlation=s.nifty_correlation,
            )
            if not screen.passed_liquidity or not screen.passed_volatility:
                continue
            note_parts = [x for x in (intra_note, del_intra) if x]
            note = " · ".join(note_parts)
            pick = _horizon_to_pick(
                s.nse_symbol, s.name, s.symbol, s.price, s.intraday, regime,
                regime_note=note,
                screen_score=screen.composite_score,
                screen_notes=screen.notes,
            )
            pick.score = combined_intraday_rank(pick.score, screen.composite_score)
            intraday_picks.append(pick)
        if (
            s.short_term.score >= short_min
            and s.short_term.action in BUY_ACTIONS_SHORT
            and not should_skip_pick(ev, "short", skip_earnings_week=skip_earnings_week)
            and not should_downgrade_for_delivery(dv, "short", filter_weak_delivery=filter_weak_delivery)
        ):
            note = " · ".join(x for x in (earnings_note_for_pick(ev, "short"), delivery_note_for_horizon(dv, "short")) if x)
            short_picks.append(_horizon_to_pick(
                s.nse_symbol, s.name, s.symbol, s.price, s.short_term, regime,
                regime_note=note,
            ))
        if s.long_term.score >= long_min and s.long_term.action in BUY_ACTIONS_LONG:
            note = " · ".join(x for x in (earnings_note_for_pick(ev, "long"), delivery_note_for_horizon(dv, "long")) if x)
            long_picks.append(_horizon_to_pick(
                s.nse_symbol, s.name, s.symbol, s.price, s.long_term, regime,
                regime_note=note,
            ))

    intraday_picks.sort(key=lambda p: -p.score)
    short_picks.sort(key=lambda p: -p.score)
    long_picks.sort(key=lambda p: -p.score)
    return intraday_picks[:8], short_picks[:10], long_picks[:10]


def _scan_all_stocks(
    universe: list[str],
    period: str,
    market: str,
    nifty_daily_df: pd.DataFrame | None = None,
    *,
    prior_session_intraday: bool = False,
    market_open: bool = False,
) -> list[StockPulseEntry]:
    kite_syms = [f"NSE:{s}-EQ" for s in universe]
    kite_ltp = get_kite_ltp_cached(kite_syms)
    top10_set = set(MARKET_PULSE_TOP_10)

    results: list[StockPulseEntry] = []
    with ThreadPoolExecutor(max_workers=SCAN_WORKERS) as pool:
        futures = []
        for sym in universe:
            full_charts = sym in top10_set
            futures.append(
                pool.submit(
                    scan_stock,
                    sym,
                    period,
                    market,
                    kite_ltp,
                    charts=full_charts,
                    skip_intraday=not market_open and not prior_session_intraday,
                    prior_session_intraday=prior_session_intraday,
                    nifty_daily_df=nifty_daily_df,
                    market_open=market_open,
                )
            )
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def load_index_options_for_report(
    report: MarketPulseReport,
    period: str,
) -> list[IndexOptionsPulse]:
    """Lazy-load NSE option chains (slow — call from UI expander)."""
    if report.index_options and not getattr(report, "_index_options_deferred", False):
        return report.index_options
    pulse_by_yahoo = {p.symbol: p for p in report.indices}
    index_options: list[IndexOptionsPulse] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [
            pool.submit(scan_index_options, fno, name, yahoo, period, pulse_by_yahoo.get(yahoo))
            for fno, name, yahoo in INDEX_FNO_SYMBOLS
        ]
        for fut in as_completed(futs):
            index_options.append(fut.result())
    report.index_options = index_options
    report._index_options_deferred = False  # type: ignore[attr-defined]
    return index_options


def run_market_pulse_scan(
    period: str = "1y",
    market: str = "india",
    use_cache: bool = True,
    *,
    allow_stale_cache: bool = False,
    include_index_options: bool = False,
    skip_earnings_week: bool = True,
    filter_weak_delivery: bool = True,
    prior_session_intraday: bool = False,
) -> MarketPulseReport:
    from analyzer.pulse_cache import load_pulse_cache_with_stale, save_pulse_cache

    cache_key = f"pulse_{period}_{market}"
    if use_cache:
        cached, fresh = load_pulse_cache_with_stale(cache_key, CACHE_TTL)
        if cached is not None and getattr(cached, "indices", None):
            cached.from_cache = True
            if fresh or allow_stale_cache:
                return cached

    from analyzer.data import fetch_stock_data

    fetch_period = "2y" if period in ("3mo", "6mo") else period
    try:
        nifty_daily_df, _ = fetch_stock_data("NIFTY50", period=fetch_period, market=market)
    except Exception:
        nifty_daily_df = None

    from analyzer.context_engine import build_context_snapshot
    from analyzer.context_engine.migration import macro_from_snapshot, regime_from_snapshot

    ctx = build_context_snapshot(market=market, period=period, use_cache=True)
    regime = regime_from_snapshot(ctx)
    macro = macro_from_snapshot(ctx)
    market_open = bool(ctx.market_session.get("is_open", False))

    with ThreadPoolExecutor(max_workers=4) as pool:
        f_indices = pool.submit(india_market_pulse, period)
        f_stocks = pool.submit(
            _scan_all_stocks,
            MARKET_PULSE_SCAN_UNIVERSE,
            period,
            market,
            nifty_daily_df,
            prior_session_intraday=prior_session_intraday,
            market_open=market_open,
        )
        f_earnings = pool.submit(fetch_nifty50_earnings, MARKET_PULSE_SCAN_UNIVERSE, market)
        f_delivery = pool.submit(fetch_delivery_batch, MARKET_PULSE_SCAN_UNIVERSE)

        indices = f_indices.result()
        all_stocks = f_stocks.result()
        earnings_events = f_earnings.result()
        delivery_raw = f_delivery.result()
        delivery_snapshots = enrich_delivery_with_stocks(delivery_raw, all_stocks)

    if regime is None:
        from analyzer.market_regime import MarketRegime

        regime = MarketRegime(
            symbol="^NSEI",
            adx=None,
            plus_di=None,
            minus_di=None,
            regime="Unknown",
            allow_aggressive_intraday=True,
            allow_aggressive_swing=True,
            message="Regime unavailable",
            banner="",
        )

    verdict = overall_market_verdict(indices)

    index_options: list[IndexOptionsPulse] = []
    deferred_options = True
    if include_index_options:
        pulse_by_yahoo = {p.symbol: p for p in indices}
        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = [
                pool.submit(scan_index_options, fno, name, yahoo, period, pulse_by_yahoo.get(yahoo))
                for fno, name, yahoo in INDEX_FNO_SYMBOLS
            ]
            for fut in as_completed(futs):
                index_options.append(fut.result())
        deferred_options = False

    intraday_picks, short_picks, long_picks = _collect_picks(
        all_stocks,
        regime,
        events_by_nse(earnings_events),
        delivery_by_nse(delivery_snapshots),
        skip_earnings_week=skip_earnings_week,
        filter_weak_delivery=filter_weak_delivery,
        nifty_daily_df=nifty_daily_df,
    )
    stock_map = {s.nse_symbol: s for s in all_stocks}

    top10_set = set(MARKET_PULSE_TOP_10)
    display_stocks = [s for s in all_stocks if s.nse_symbol in top10_set]
    display_stocks.sort(key=lambda s: s.combined_score, reverse=True)

    report = MarketPulseReport(
        indices=indices,
        market_verdict=verdict,
        index_options=index_options,
        top_stocks=display_stocks,
        stock_map=stock_map,
        intraday_picks=intraday_picks,
        short_term_picks=short_picks,
        long_term_picks=long_picks,
        regime=regime,
        macro=macro,
        from_cache=False,
        strongest_ce=[f"{p.nse_symbol} ({p.action})" for p in intraday_picks[:5]],
        strongest_pe=[],
        strongest_equity=[f"{p.nse_symbol} ({p.action})" for p in long_picks[:5]],
        earnings_events=earnings_events,
        earnings_by_nse=events_by_nse(earnings_events),
        delivery_snapshots=delivery_snapshots,
        delivery_by_nse=delivery_by_nse(delivery_snapshots),
    )
    report._index_options_deferred = deferred_options  # type: ignore[attr-defined]
    save_pulse_cache(cache_key, report)
    try:
        from analyzer.suggestion_journal import record_from_market_pulse
        record_from_market_pulse(report)
    except Exception:
        pass
    return report
