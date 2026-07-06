"""Offline 6-month pattern research — tunes live suggestion weights."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from zoneinfo import ZoneInfo

import pandas as pd

from analyzer.data import fetch_stock_data
from analyzer.indicators import add_indicators
from analyzer.india import NIFTY_50
from analyzer.suggestion_features import (
    DEFAULT_BASELINE_HIT_RATE,
    DEFAULT_FEATURE_WEIGHTS,
    _feature_unit_scores,
    nifty_bias_from_df,
    simulate_daily_mis_outcome,
)
from analyzer.watchlist_learning import (
    WIN_OUTCOMES,
    load_strategy_state,
    save_strategy_state,
)

IST = ZoneInfo("Asia/Kolkata")
WIN_SET = WIN_OUTCOMES


@dataclass
class ResearchSample:
    symbol: str
    outcome: str
    unit_scores: dict[str, float]


@dataclass
class StrategyResearchReport:
    symbols_scanned: int
    samples: int
    wins: int
    losses: int
    win_rate_pct: float | None
    train_win_rate_pct: float | None
    test_win_rate_pct: float | None
    feature_weights: dict[str, float]
    baseline_hit_rate: float
    insights: list[str] = field(default_factory=list)
    applied: bool = False


def _is_win(outcome: str) -> bool:
    return outcome in WIN_SET


def _collect_symbol_samples(
    symbol: str,
    *,
    period: str = "6mo",
    market: str = "india",
    nifty_df: pd.DataFrame | None = None,
) -> list[ResearchSample]:
    try:
        df, _ = fetch_stock_data(symbol, period=period, market=market, enrich_nse=False)
        if "ATR_14" not in df.columns:
            df = add_indicators(df)
    except Exception:
        return []
    if len(df) < 30:
        return []

    samples: list[ResearchSample] = []
    for i in range(21, len(df) - 1):
        bias = nifty_bias_from_df(nifty_df, i) if nifty_df is not None else "NEUTRAL"
        result = simulate_daily_mis_outcome(df, i, market_bias=bias)
        if result is None:
            continue
        outcome, feats = result
        if outcome in ("no_data", "pending"):
            continue
        units = _feature_unit_scores(feats)
        samples.append(ResearchSample(symbol=symbol, outcome=outcome, unit_scores=units))
    return samples


def _tune_weights(
    train: list[ResearchSample],
    base_weights: dict[str, float],
) -> tuple[dict[str, float], list[str]]:
    wins = [s for s in train if _is_win(s.outcome)]
    losses = [s for s in train if not _is_win(s.outcome)]
    insights: list[str] = []
    if not wins or not losses:
        return dict(base_weights), insights

    tuned = dict(base_weights)
    for key in tuned:
        win_avg = mean(s.unit_scores.get(key, 0.5) for s in wins)
        loss_avg = mean(s.unit_scores.get(key, 0.5) for s in losses)
        delta = win_avg - loss_avg
        if abs(delta) < 0.05:
            continue
        factor = 1.0 + min(0.25, max(-0.15, delta * 0.4))
        tuned[key] = round(tuned[key] * factor, 4)
        if delta > 0.08:
            insights.append(f"**{key}** higher on winners ({win_avg:.2f} vs {loss_avg:.2f}) — weight up.")
        elif delta < -0.08:
            insights.append(f"**{key}** weaker signal — weight trimmed.")

    total = sum(tuned.values()) or 1.0
    tuned = {k: round(v / total, 4) for k, v in tuned.items()}
    return tuned, insights


def _win_rate(samples: list[ResearchSample]) -> float | None:
    decided = [s for s in samples if s.outcome not in ("no_data", "pending")]
    if not decided:
        return None
    wins = sum(1 for s in decided if _is_win(s.outcome))
    return 100.0 * wins / len(decided)


def run_strategy_research(
    *,
    period: str = "6mo",
    market: str = "india",
    symbols: list[str] | None = None,
    max_symbols: int | None = None,
    apply: bool = True,
    holdout_ratio: float = 0.25,
) -> StrategyResearchReport:
    """
    Mine Nifty 50 daily + session patterns; update feature_weights in strategy file.
    Uses last holdout_ratio of samples for out-of-sample check.
    """
    universe = symbols or list(NIFTY_50)
    if max_symbols:
        universe = universe[:max_symbols]

    try:
        nifty_df, _ = fetch_stock_data("NIFTY50", period=period, market=market, enrich_nse=False)
        if "ATR_14" not in nifty_df.columns:
            nifty_df = add_indicators(nifty_df)
    except Exception:
        nifty_df = None

    all_samples: list[ResearchSample] = []
    scanned = 0
    for sym in universe:
        batch = _collect_symbol_samples(sym, period=period, market=market, nifty_df=nifty_df)
        if batch:
            scanned += 1
            all_samples.extend(batch)

    if not all_samples:
        return StrategyResearchReport(
            symbols_scanned=0,
            samples=0,
            wins=0,
            losses=0,
            win_rate_pct=None,
            train_win_rate_pct=None,
            test_win_rate_pct=None,
            feature_weights=dict(DEFAULT_FEATURE_WEIGHTS),
            baseline_hit_rate=DEFAULT_BASELINE_HIT_RATE,
            insights=["No research samples — check data connectivity."],
            applied=False,
        )

    split = max(1, int(len(all_samples) * (1.0 - holdout_ratio)))
    train = all_samples[:split]
    test = all_samples[split:]

    state = load_strategy_state()
    fw = state.get("strategy", {}).get("feature_weights") or {}
    base_w = {**DEFAULT_FEATURE_WEIGHTS, **fw}
    tuned_w, insights = _tune_weights(train, base_w)

    wins = sum(1 for s in all_samples if _is_win(s.outcome))
    losses = len(all_samples) - wins
    wr = _win_rate(all_samples)
    train_wr = _win_rate(train)
    test_wr = _win_rate(test)
    baseline = (wr / 100.0) if wr is not None else DEFAULT_BASELINE_HIT_RATE

    if train_wr is not None and test_wr is not None:
        insights.insert(
            0,
            f"6mo simulation: **{wr:.0f}%** hit rate "
            f"({len(all_samples)} setups · train {train_wr:.0f}% · holdout {test_wr:.0f}%).",
        )

    applied = False
    if apply and len(all_samples) >= 40:
        strat = dict(state.get("strategy", {}))
        strat["feature_weights"] = tuned_w
        strat["baseline_hit_rate"] = round(baseline, 3)
        strat["research_version"] = int(strat.get("research_version", 0)) + 1
        strat["research_samples"] = len(all_samples)
        strat["research_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
        state["strategy"] = strat
        state.setdefault("history", []).append(
            {
                "at": strat["research_at"],
                "win_rate_pct": wr,
                "samples": len(all_samples),
                "weights": tuned_w,
            }
        )
        state["insights"] = insights[:8]
        save_strategy_state(state)
        applied = True
    elif len(all_samples) < 40:
        insights.append(f"Need **40+** samples to auto-apply (have {len(all_samples)}).")

    return StrategyResearchReport(
        symbols_scanned=scanned,
        samples=len(all_samples),
        wins=wins,
        losses=losses,
        win_rate_pct=wr,
        train_win_rate_pct=train_wr,
        test_win_rate_pct=test_wr,
        feature_weights=tuned_w,
        baseline_hit_rate=baseline,
        insights=insights,
        applied=applied,
    )
