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
from analyzer.india_macro import IndiaMacroSnapshot, build_india_macro_snapshot
from analyzer.indicators import add_indicators
from analyzer.intraday_data import fetch_intraday, market_session_status
from analyzer.intraday_signals import add_intraday_indicators
from analyzer.market_pulse import IndexPulse, india_market_pulse, overall_market_verdict
from analyzer.market_regime import MarketRegime, apply_regime_to_action, detect_nifty_regime
from analyzer.nse_options import (
    NSEOptionChain,
    NSEOptionPick,
    enrich_with_nse_chain,
)
from analyzer.kite_stream import get_kite_ltp_cached
from analyzer.threshold_tuning import get_pulse_thresholds

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
        chain, picks, err = enrich_with_nse_chain(action, fno_symbol)
        if err:
            return IndexOptionsPulse(fno_symbol, name, index_pulse, action, None, [], err)
        return IndexOptionsPulse(fno_symbol, name, index_pulse, action, chain, picks)
    except Exception as exc:
        return IndexOptionsPulse(fno_symbol, name, index_pulse, action, None, [], str(exc))


def scan_stock(
    symbol: str,
    period: str = "1y",
    market: str = "india",
    kite_ltp: dict[str, float] | None = None,
    *,
    charts: bool = True,
    skip_intraday: bool | None = None,
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
            skip_intraday = not market_session_status().get("is_open")

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
) -> tuple[list[ChartStockPick], list[ChartStockPick], list[ChartStockPick]]:
    intraday_picks: list[ChartStockPick] = []
    short_picks: list[ChartStockPick] = []
    long_picks: list[ChartStockPick] = []
    gates = get_pulse_thresholds()
    intraday_min = gates["intraday"]
    short_min = gates["short"]
    long_min = gates["long"]

    for s in stocks:
        if s.error or not s.short_term or not s.long_term:
            continue
        if (
            s.intraday
            and s.intraday.score >= intraday_min
            and s.intraday.action in BUY_ACTIONS_INTRADAY
        ):
            intraday_picks.append(_horizon_to_pick(
                s.nse_symbol, s.name, s.symbol, s.price, s.intraday, regime,
            ))
        if s.short_term.score >= short_min and s.short_term.action in BUY_ACTIONS_SHORT:
            short_picks.append(_horizon_to_pick(
                s.nse_symbol, s.name, s.symbol, s.price, s.short_term, regime,
            ))
        if s.long_term.score >= long_min and s.long_term.action in BUY_ACTIONS_LONG:
            long_picks.append(_horizon_to_pick(
                s.nse_symbol, s.name, s.symbol, s.price, s.long_term, regime,
            ))

    intraday_picks.sort(key=lambda p: -p.score)
    short_picks.sort(key=lambda p: -p.score)
    long_picks.sort(key=lambda p: -p.score)
    return intraday_picks[:8], short_picks[:10], long_picks[:10]


def _scan_all_stocks(
    universe: list[str],
    period: str,
    market: str,
) -> list[StockPulseEntry]:
    kite_syms = [f"NSE:{s}-EQ" for s in universe]
    kite_ltp = get_kite_ltp_cached(kite_syms)
    market_open = market_session_status().get("is_open", False)
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
                    skip_intraday=not market_open,
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
) -> MarketPulseReport:
    from analyzer.pulse_cache import load_pulse_cache_with_stale, save_pulse_cache

    cache_key = f"pulse_{period}_{market}"
    if use_cache:
        cached, fresh = load_pulse_cache_with_stale(cache_key, CACHE_TTL)
        if cached is not None and getattr(cached, "indices", None):
            cached.from_cache = True
            if fresh or allow_stale_cache:
                return cached

    with ThreadPoolExecutor(max_workers=4) as pool:
        f_regime = pool.submit(detect_nifty_regime, period)
        f_macro = pool.submit(build_india_macro_snapshot)
        f_indices = pool.submit(india_market_pulse, period)
        f_stocks = pool.submit(_scan_all_stocks, MARKET_PULSE_SCAN_UNIVERSE, period, market)

        regime = f_regime.result()
        macro = f_macro.result()
        indices = f_indices.result()
        all_stocks = f_stocks.result()

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

    intraday_picks, short_picks, long_picks = _collect_picks(all_stocks, regime)
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
    )
    report._index_options_deferred = deferred_options  # type: ignore[attr-defined]
    save_pulse_cache(cache_key, report)
    try:
        from analyzer.suggestion_journal import record_from_market_pulse
        record_from_market_pulse(report)
    except Exception:
        pass
    return report
