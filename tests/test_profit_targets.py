"""Tests for profit target profiles."""

from __future__ import annotations

from analyzer.market_regime import MarketRegime
from analyzer.profit_targets import build_profit_targets, capital_profit_inr, regime_allows_aggressive_target


def _trend_regime() -> MarketRegime:
    return MarketRegime(
        symbol="^NSEI",
        adx=24.0,
        plus_di=30.0,
        minus_di=15.0,
        regime="Trending Bullish",
        allow_aggressive_intraday=True,
        allow_aggressive_swing=True,
        message="trend",
        banner="trend",
    )


def _chop_regime() -> MarketRegime:
    return MarketRegime(
        symbol="^NSEI",
        adx=14.0,
        plus_di=18.0,
        minus_di=17.0,
        regime="Range-bound",
        allow_aggressive_intraday=False,
        allow_aggressive_swing=False,
        message="chop",
        banner="chop",
    )


def test_aggressive_ladder_on_trend_day():
    t = build_profit_targets(80.0, mode="aggressive", regime=_trend_regime())
    assert t.t1 == 96.0   # +20% min
    assert t.t2 == 100.0  # +25% lock
    assert t.stretch == 108.0  # +35%
    assert t.chase_stretch is True


def test_aggressive_min_20_on_chop():
    t = build_profit_targets(80.0, mode="aggressive", regime=_chop_regime())
    assert t.t1 == 96.0
    assert t.t2 == 96.0
    assert t.stretch_pct == 20.0
    assert t.chase_stretch is False
    assert regime_allows_aggressive_target(_chop_regime()) is False


def test_capital_goals_inr():
    assert capital_profit_inr(5000, 20) == 1000.0
    assert capital_profit_inr(5000, 25) == 1250.0
    assert capital_profit_inr(5000, 35) == 1750.0
