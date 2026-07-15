"""Profit target profiles — +20% minimum floor, up to +35% stretch on trend days."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.market_regime import MarketRegime

PROFIT_MODES = ("conservative", "standard", "aggressive")

# User ladder: minimum +20% on every winning trade; stretch to +35% on trend days.
DEFAULT_MIN_TRADE_PCT = 20.0
DEFAULT_TARGET_TRADE_PCT = 25.0
DEFAULT_STRETCH_TRADE_PCT = 35.0


@dataclass
class ProfitTargets:
    """Premium-based exit levels for 1-lot MIS options (multiples of entry)."""
    mode: str
    entry: float
    t1_pct: float  # minimum floor (+20%)
    t2_pct: float  # lock / chop exit (+20% chop, +25% trend)
    stretch_pct: float  # trend-day stretch (+35%)
    trail_pct: float
    hard_stop_pct: float
    min_daily_capital_pct: float
    regime_ok_for_stretch: bool
    headline: str

    @property
    def t1(self) -> float:
        return round(self.entry * (1 + self.t1_pct / 100), 2)

    @property
    def t2(self) -> float:
        return round(self.entry * (1 + self.t2_pct / 100), 2)

    @property
    def stretch(self) -> float:
        return round(self.entry * (1 + self.stretch_pct / 100), 2)

    @property
    def trail(self) -> float:
        return round(self.entry * (1 + self.trail_pct / 100), 2)

    @property
    def hard_stop(self) -> float:
        return round(self.entry * (1 + self.hard_stop_pct / 100), 2)

    @property
    def min_floor_pct(self) -> float:
        return self.t1_pct

    @property
    def chase_stretch(self) -> bool:
        return self.regime_ok_for_stretch and self.stretch_pct > self.t2_pct + 5


def regime_allows_aggressive_target(regime: MarketRegime | None) -> bool:
    if regime is None:
        return False
    if regime.regime.startswith("Trending") and regime.adx is not None and regime.adx >= 20:
        return True
    return bool(regime.allow_aggressive_intraday and regime.adx is not None and regime.adx >= 18)


def build_profit_targets(
    entry: float,
    *,
    mode: str = "aggressive",
    min_trade_pct: float = DEFAULT_MIN_TRADE_PCT,
    target_trade_pct: float = DEFAULT_TARGET_TRADE_PCT,
    stretch_trade_pct: float = DEFAULT_STRETCH_TRADE_PCT,
    min_daily_capital_pct: float = 20.0,
    regime: MarketRegime | None = None,
) -> ProfitTargets:
    """
    Ladder for 1-lot options:
      - Floor: +20% minimum (never give back below after touch)
      - Chop: sell at +20%
      - Trend lock: +25% before chasing stretch
      - Stretch: +35% (trend days only)
    """
    mode = mode.lower().strip() if mode in PROFIT_MODES else "aggressive"
    stretch_ok = regime_allows_aggressive_target(regime)

    if mode == "conservative":
        t1, t2, stretch = 15.0, 18.0, 22.0
    elif mode == "standard":
        t1, t2, stretch = min_trade_pct, target_trade_pct, min(target_trade_pct + 5, 28.0)
    else:
        t1 = min_trade_pct
        if stretch_ok:
            t2, stretch = target_trade_pct, stretch_trade_pct
        else:
            t2, stretch = min_trade_pct, min_trade_pct

    effective = mode
    if mode == "aggressive" and not stretch_ok:
        effective = "aggressive (chop — min +20% only)"

    if stretch_ok and mode == "aggressive":
        headline = (
            f"Min +{t1:.0f}% (₹{entry * (1 + t1/100):.0f}) · lock +{t2:.0f}% · "
            f"stretch +{stretch:.0f}% (₹{entry * (1 + stretch/100):.0f})"
        )
    elif mode == "aggressive":
        headline = (
            f"Chop — minimum +{t1:.0f}% only (₹{entry * (1 + t1/100):.0f}); "
            f"+{stretch_trade_pct:.0f}% stretch off"
        )
    else:
        headline = f"Min +{t1:.0f}% · target +{t2:.0f}%"

    return ProfitTargets(
        mode=effective,
        entry=entry,
        t1_pct=t1,
        t2_pct=t2,
        stretch_pct=stretch,
        trail_pct=-4.0,
        hard_stop_pct=-35.0,
        min_daily_capital_pct=min_daily_capital_pct,
        regime_ok_for_stretch=stretch_ok,
        headline=headline,
    )


def capital_profit_inr(capital: float, pct: float) -> float:
    return round(capital * pct / 100, 2)
