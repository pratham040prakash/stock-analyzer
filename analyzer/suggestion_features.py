"""Multi-factor features and confidence scoring for MIS suggestions."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.intraday_signals import add_intraday_indicators, analyze_intraday
from analyzer.intraday_watchlist import (
    ProChecklist,
    compute_prep_metrics,
    macd_bullish_aligned,
)
from analyzer.watchlist_eod import score_session_plan


DEFAULT_FEATURE_WEIGHTS: dict[str, float] = {
    "checklist": 0.14,
    "atr": 0.12,
    "volume": 0.12,
    "rsi_macd": 0.10,
    "sector_tailwind": 0.14,
    "combined": 0.10,
    "intraday_align": 0.12,
    "vwap_align": 0.08,
    "or_breakout": 0.08,
}

DEFAULT_BASELINE_HIT_RATE = 0.52


@dataclass
class SessionCandleProfile:
    """Prior session 5m structure."""
    available: bool = False
    above_vwap: bool = False
    or_breakout_up: bool = False
    or_breakdown: bool = False
    session_bias: str = "NEUTRAL"
    session_return_pct: float | None = None


@dataclass
class SuggestionFeatures:
    atr_pct: float | None = None
    volume_ratio: float | None = None
    rsi: float | None = None
    macd_bullish: bool = False
    sector_tailwind: bool = False
    checklist_passed: int = 0
    checklist_total: int = 5
    combined_score: float = 0.0
    intraday_aligned: bool = False
    market_bias: str = "NEUTRAL"
    session: SessionCandleProfile = field(default_factory=SessionCandleProfile)
    prep_score_base: float = 0.0


def get_feature_weights() -> dict[str, float]:
    from analyzer.watchlist_learning import get_watchlist_strategy

    strat = get_watchlist_strategy()
    raw = strat.get("feature_weights") or DEFAULT_FEATURE_WEIGHTS
    weights = {**DEFAULT_FEATURE_WEIGHTS, **raw}
    total = sum(float(v) for v in weights.values()) or 1.0
    return {k: float(v) / total for k, v in weights.items()}


def get_baseline_hit_rate() -> float:
    from analyzer.watchlist_learning import get_watchlist_strategy

    strat = get_watchlist_strategy()
    val = strat.get("baseline_hit_rate")
    if val is None:
        return DEFAULT_BASELINE_HIT_RATE
    return max(0.35, min(0.75, float(val)))


def build_session_profile(intraday_df: pd.DataFrame | None) -> SessionCandleProfile:
    if intraday_df is None or len(intraday_df) < 5:
        return SessionCandleProfile()
    try:
        analysis = analyze_intraday(intraday_df, "", "5m")
        df = add_intraday_indicators(intraday_df)
        row = df.iloc[-1]
        price = float(row["Close"])
        vwap = float(row["VWAP"]) if not pd.isna(row.get("VWAP")) else price
        or_high = analysis.opening_range_high
        or_low = analysis.opening_range_low
        open_px = float(df.iloc[0]["Open"])
        ret = ((price / open_px) - 1) * 100 if open_px > 0 else None
        return SessionCandleProfile(
            available=True,
            above_vwap=price > vwap * 1.001,
            or_breakout_up=price > or_high,
            or_breakdown=price < or_low,
            session_bias=analysis.session_bias,
            session_return_pct=round(ret, 2) if ret is not None else None,
        )
    except Exception:
        return SessionCandleProfile()


def build_suggestion_features(
    *,
    metrics: dict,
    checklist: ProChecklist,
    sector_tailwind: bool,
    market_bias: str,
    combined_score: float = 0.0,
    volume_ratio: float | None = None,
    intraday_action: str | None = None,
    session: SessionCandleProfile | None = None,
    prep_score_base: float = 0.0,
) -> SuggestionFeatures:
    sess = session or SessionCandleProfile()
    aligned = False
    if intraday_action:
        if market_bias == "BEARISH" and intraday_action in ("SELL", "STRONG SELL"):
            aligned = True
        elif market_bias != "BEARISH" and intraday_action in ("BUY", "STRONG BUY"):
            aligned = True
    if sess.available and not aligned:
        if market_bias == "BEARISH" and sess.session_bias == "BEARISH":
            aligned = True
        elif market_bias != "BEARISH" and sess.session_bias == "BULLISH":
            aligned = True
    return SuggestionFeatures(
        atr_pct=metrics.get("atr_pct"),
        volume_ratio=volume_ratio,
        rsi=metrics.get("rsi"),
        macd_bullish=bool(metrics.get("macd_bullish")),
        sector_tailwind=sector_tailwind,
        checklist_passed=checklist.passed,
        checklist_total=checklist.total,
        combined_score=combined_score,
        intraday_aligned=aligned,
        market_bias=market_bias,
        session=sess,
        prep_score_base=prep_score_base,
    )


def _feature_unit_scores(f: SuggestionFeatures) -> dict[str, float]:
    """Map raw features to 0–1 scores."""
    checklist = f.checklist_passed / max(f.checklist_total, 1)
    atr = min(1.0, (f.atr_pct or 0) / 3.0)
    vol = min(1.0, max(0.0, ((f.volume_ratio or 1.0) - 0.8) / 1.7))
    rsi_ok = 0.0
    if f.rsi is not None:
        if f.market_bias == "BEARISH":
            rsi_ok = 1.0 if 35 <= f.rsi <= 48 else 0.4
        else:
            rsi_ok = 1.0 if 52 <= f.rsi <= 68 else 0.4
    rsi_macd = (0.55 * rsi_ok + 0.45 * (1.0 if f.macd_bullish else 0.25))
    combined = min(1.0, max(0.0, (f.combined_score + 30) / 80))
    vwap_align = 0.5
    if f.session.available:
        if f.market_bias == "BEARISH":
            vwap_align = 1.0 if not f.session.above_vwap else 0.2
        else:
            vwap_align = 1.0 if f.session.above_vwap else 0.2
    or_brk = 0.5
    if f.session.available:
        if f.market_bias == "BEARISH":
            or_brk = 1.0 if f.session.or_breakdown else 0.3
        else:
            or_brk = 1.0 if f.session.or_breakout_up else 0.3
    return {
        "checklist": checklist,
        "atr": atr,
        "volume": vol,
        "rsi_macd": rsi_macd,
        "sector_tailwind": 1.0 if f.sector_tailwind else 0.2,
        "combined": combined,
        "intraday_align": 1.0 if f.intraday_aligned else 0.25,
        "vwap_align": vwap_align,
        "or_breakout": or_brk,
    }


def score_suggestion(
    features: SuggestionFeatures,
    *,
    weights: dict[str, float] | None = None,
    baseline_hit_rate: float | None = None,
) -> tuple[float, float]:
    """
    Return (intelligence_score 0–100, confidence_pct).
    Confidence = estimated target-hit likelihood from learned weights.
    """
    w = weights or get_feature_weights()
    baseline = baseline_hit_rate if baseline_hit_rate is not None else get_baseline_hit_rate()
    units = _feature_unit_scores(features)
    intel = sum(w.get(k, 0.0) * units.get(k, 0.5) for k in w) * 100.0
    # Map intelligence spread around baseline (e.g. 52% base ± 15 pts)
    confidence = baseline * 100.0 + (intel - 55.0) * 0.35
    confidence = max(35.0, min(85.0, confidence))
    return round(intel, 1), round(confidence, 0)


def simulate_daily_mis_outcome(
    daily_df: pd.DataFrame,
    day_index: int,
    *,
    market_bias: str = "NEUTRAL",
) -> tuple[str, SuggestionFeatures] | None:
    """
    Simulate one MIS plan from daily history (research).
    day_index = last bar used for prep; outcome scored on day_index + 1.
    """
    if day_index < 21 or day_index >= len(daily_df) - 1:
        return None
    window = daily_df.iloc[: day_index + 1].copy()
    metrics = compute_prep_metrics(window)
    if not metrics or metrics.get("atr_pct") is None:
        return None
    pivots = metrics.get("pivot")
    support = metrics.get("support")
    resistance = metrics.get("resistance")
    if not pivots or support is None or resistance is None:
        return None
    row = window.iloc[-1]
    price = float(row["Close"])
    atr_pct = float(metrics["atr_pct"])
    if atr_pct < 1.2:
        return None

    if market_bias == "BEARISH":
        entry = min(price, pivots.pivot)
        stop = pivots.r1
        target = pivots.s1
        side = "SHORT"
    elif metrics.get("breakout"):
        entry = max(price, resistance)
        stop = max(pivots.s1, support)
        target = pivots.r2
        side = "LONG"
    else:
        entry = max(price, pivots.pivot)
        stop = pivots.s1
        target = pivots.r1
        side = "LONG"

    next_row = daily_df.iloc[day_index + 1]
    outcome, _ = score_session_plan(
        entry=entry,
        stop_loss=stop,
        target=target,
        session_high=float(next_row["High"]),
        session_low=float(next_row["Low"]),
        session_close=float(next_row["Close"]),
        side=side,
    )
    vol_sma = row.get("VOL_SMA_20")
    vol_ratio = None
    if vol_sma is not None and not pd.isna(vol_sma) and float(vol_sma) > 0:
        vol_ratio = round(float(row["Volume"]) / float(vol_sma), 2)

    checklist = ProChecklist(
        volume_ok=(vol_ratio or 0) >= 1.0,
        atr_ok=atr_pct >= 1.5,
        rsi_macd_ok=macd_bullish_aligned(window),
        levels_ok=True,
        news_ok=True,
        passed=0,
    )
    checklist.passed = sum(
        [checklist.volume_ok, checklist.atr_ok, checklist.rsi_macd_ok, checklist.levels_ok, checklist.news_ok]
    )

    feats = build_suggestion_features(
        metrics=metrics,
        checklist=checklist,
        sector_tailwind=False,
        market_bias=market_bias,
        volume_ratio=vol_ratio,
        prep_score_base=checklist.passed * 12,
    )
    return outcome, feats


def nifty_bias_from_df(nifty_df: pd.DataFrame, day_index: int) -> str:
    if nifty_df is None or day_index < 20:
        return "NEUTRAL"
    window = nifty_df.iloc[: day_index + 1]
    if len(window) < 20:
        return "NEUTRAL"
    close = float(window["Close"].iloc[-1])
    sma20 = float(window["Close"].tail(20).mean())
    if close > sma20 * 1.01:
        return "BULLISH"
    if close < sma20 * 0.99:
        return "BEARISH"
    return "NEUTRAL"
