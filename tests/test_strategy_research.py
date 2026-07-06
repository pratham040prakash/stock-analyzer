"""Tests for suggestion intelligence and strategy research."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from analyzer.indicators import add_indicators
from analyzer.intraday_watchlist import ProChecklist
from analyzer.suggestion_features import (
    build_suggestion_features,
    score_suggestion,
    simulate_daily_mis_outcome,
)


def _synthetic_daily(n: int = 80, *, trend: float = 0.003) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    price = 100.0
    rows = []
    for _ in dates:
        chg = trend + float(rng.normal(0, 0.018))
        o = price
        c = price * (1 + chg)
        h = max(o, c) * (1 + abs(float(rng.normal(0, 0.004))))
        l = min(o, c) * (1 - abs(float(rng.normal(0, 0.004))))
        v = float(rng.integers(800_000, 2_000_000))
        rows.append({"Open": o, "High": h, "Low": l, "Close": c, "Volume": v})
        price = c
    df = pd.DataFrame(rows, index=dates)
    return add_indicators(df)


class TestSuggestionFeatures(unittest.TestCase):
    def test_score_suggestion_range(self):
        checklist = ProChecklist(True, True, True, True, True, 5)
        feats = build_suggestion_features(
            metrics={"atr_pct": 2.0, "rsi": 58, "macd_bullish": True},
            checklist=checklist,
            sector_tailwind=True,
            market_bias="BULLISH",
            combined_score=20,
            volume_ratio=1.5,
            prep_score_base=60,
        )
        intel, conf = score_suggestion(
            feats,
            weights={
                "checklist": 0.2,
                "atr": 0.15,
                "volume": 0.15,
                "rsi_macd": 0.15,
                "sector_tailwind": 0.15,
                "combined": 0.1,
                "intraday_align": 0.05,
                "vwap_align": 0.05,
                "or_breakout": 0.0,
            },
            baseline_hit_rate=0.52,
        )
        self.assertGreaterEqual(conf, 35)
        self.assertLessEqual(conf, 85)
        self.assertGreater(intel, 40)

    def test_simulate_daily_outcome(self):
        df = _synthetic_daily(60)
        result = simulate_daily_mis_outcome(df, 30, market_bias="BULLISH")
        self.assertIsNotNone(result)
        outcome, feats = result
        self.assertIn(outcome, ("target_hit", "stop_hit", "mixed", "flat_positive", "flat_negative"))
        self.assertGreaterEqual(feats.checklist_passed, 0)


class TestStrategyResearch(unittest.TestCase):
    def test_tune_weights_from_samples(self):
        from analyzer.strategy_research import ResearchSample, _tune_weights
        from analyzer.suggestion_features import DEFAULT_FEATURE_WEIGHTS

        train = []
        for _ in range(20):
            train.append(
                ResearchSample(
                    "TCS",
                    "target_hit",
                    {"atr": 0.9, "volume": 0.8, "checklist": 0.8},
                )
            )
        for _ in range(20):
            train.append(
                ResearchSample(
                    "TCS",
                    "stop_hit",
                    {"atr": 0.3, "volume": 0.4, "checklist": 0.4},
                )
            )
        tuned, insights = _tune_weights(train, dict(DEFAULT_FEATURE_WEIGHTS))
        self.assertGreater(tuned.get("atr", 0), DEFAULT_FEATURE_WEIGHTS["atr"] * 0.9)
        self.assertTrue(any("atr" in i.lower() for i in insights))

    @patch("analyzer.strategy_research.fetch_stock_data")
    def test_run_strategy_research_applies(self, mock_fetch):
        from analyzer.strategy_research import run_strategy_research
        from analyzer.watchlist_learning import reset_watchlist_strategy, get_watchlist_strategy

        df = _synthetic_daily(90)
        mock_fetch.return_value = (df, {"symbol": "TCS.NS", "name": "TCS"})
        reset_watchlist_strategy()
        report = run_strategy_research(
            period="6mo",
            symbols=["TCS"],
            max_symbols=1,
            apply=True,
            holdout_ratio=0.2,
        )
        self.assertGreater(report.samples, 10)
        strat = get_watchlist_strategy()
        self.assertIn("feature_weights", strat)
        if report.applied:
            self.assertGreater(strat.get("research_version", 0), 0)


if __name__ == "__main__":
    unittest.main()
