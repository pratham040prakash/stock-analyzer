"""Sideways / range-bound index options strategy advisor — live CE/PE input."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from analyzer.market_regime import detect_nifty_regime
from analyzer.opening_range_confirm import fetch_symbol_opening_range
from analyzer.options_analytics import OptionsAnalytics, analyze_and_record_chain
from analyzer.options_reversal_alerts import INDEX_LABEL, INDEX_YAHOO
from analyzer.providers import get_live_ltp

STRIKE_STEP: dict[str, int] = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
    "MIDCPNIFTY": 25,
}

# IV tiers — GTF + Strike.money: sell premium when IV high; iron fly at mid IV
IV_EXTREME_RANK = 85.0
IV_HIGH_RANK = 70.0
IV_LOW_RANK = 30.0

REFERENCES = (
    "GTF sideways credit strategies · "
    "[Strike.money income strategies](https://www.strike.money/options/best-options-income-strategies) · "
    "[Investopedia options strategies](https://www.investopedia.com/trading/options-strategies/)"
)


@dataclass
class StrategyLeg:
    action: str  # buy | sell
    option_type: str  # CE | PE
    strike: float
    role: str  # anchor | wing | hedge


@dataclass
class SidewaysStrategyAdvice:
    strategy_id: str
    strategy_name: str
    market_view: str
    risk_profile: str  # defined | undefined
    iv_tier: str  # extreme | high | mid | low | unknown
    spot: float | None
    range_high: float | None
    range_low: float | None
    range_pct: float | None
    legs: list[StrategyLeg] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    action: str = ""
    safer_alternative: str | None = None
    emoji: str = "📐"
    references: str = REFERENCES
    blocks_directional: bool = False  # user had directional CE/PE in chop


def _normalize_fno(symbol: str) -> str:
    s = symbol.upper().strip().replace(" ", "")
    if "BANK" in s:
        return "BANKNIFTY"
    if s in ("NIFTY", "NIFTY50", "^NSEI"):
        return "NIFTY"
    return s


def strike_step(fno_symbol: str) -> int:
    return STRIKE_STEP.get(_normalize_fno(fno_symbol), 50)


def _round_strike(value: float, step: int, direction: str = "nearest") -> float:
    if direction == "up":
        return math.ceil(value / step) * step
    if direction == "down":
        return math.floor(value / step) * step
    return round(value / step) * step


def _iv_tier(iv_rank: float | None, iv_band: str) -> str:
    if iv_band == "expensive" or (iv_rank is not None and iv_rank >= IV_EXTREME_RANK):
        return "extreme"
    if iv_band == "expensive" or (iv_rank is not None and iv_rank >= IV_HIGH_RANK):
        return "high"
    if iv_band == "cheap" or (iv_rank is not None and iv_rank <= IV_LOW_RANK):
        return "low"
    if iv_rank is not None or iv_band == "mid":
        return "mid"
    return "unknown"


def _spot_inside_range(spot: float, high: float, low: float) -> bool:
    return low <= spot <= high


def _range_pct(spot: float, high: float, low: float) -> float:
    if spot <= 0:
        return 0.0
    return (high - low) / spot * 100.0


def _wing_width_steps(range_pct: float) -> int:
    if range_pct >= 1.2:
        return 3
    if range_pct >= 0.6:
        return 2
    return 2


def build_iron_condor(
    *,
    fno_symbol: str,
    range_high: float,
    range_low: float,
    wing_steps: int | None = None,
) -> list[StrategyLeg]:
    step = strike_step(fno_symbol)
    spot_mid = (range_high + range_low) / 2
    rp = _range_pct(spot_mid, range_high, range_low)
    wings = wing_steps or _wing_width_steps(rp)
    short_ce = _round_strike(range_high, step, "up")
    short_pe = _round_strike(range_low, step, "down")
    long_ce = short_ce + wings * step
    long_pe = short_pe - wings * step
    return [
        StrategyLeg("sell", "CE", short_ce, "anchor"),
        StrategyLeg("buy", "CE", long_ce, "wing"),
        StrategyLeg("sell", "PE", short_pe, "anchor"),
        StrategyLeg("buy", "PE", long_pe, "wing"),
    ]


def build_iron_butterfly(*, fno_symbol: str, spot: float, wing_steps: int = 2) -> list[StrategyLeg]:
    step = strike_step(fno_symbol)
    atm = _round_strike(spot, step)
    long_ce = atm + wing_steps * step
    long_pe = atm - wing_steps * step
    return [
        StrategyLeg("sell", "CE", atm, "anchor"),
        StrategyLeg("sell", "PE", atm, "anchor"),
        StrategyLeg("buy", "CE", long_ce, "wing"),
        StrategyLeg("buy", "PE", long_pe, "wing"),
    ]


def build_short_strangle(*, fno_symbol: str, range_high: float, range_low: float) -> list[StrategyLeg]:
    step = strike_step(fno_symbol)
    return [
        StrategyLeg("sell", "CE", _round_strike(range_high, step, "up"), "anchor"),
        StrategyLeg("sell", "PE", _round_strike(range_low, step, "down"), "anchor"),
    ]


def build_short_straddle(*, fno_symbol: str, spot: float) -> list[StrategyLeg]:
    atm = _round_strike(spot, strike_step(fno_symbol))
    return [
        StrategyLeg("sell", "CE", atm, "anchor"),
        StrategyLeg("sell", "PE", atm, "anchor"),
    ]


def build_bear_call_spread(*, fno_symbol: str, short_strike: float, wing_steps: int = 2) -> list[StrategyLeg]:
    step = strike_step(fno_symbol)
    short_ce = _round_strike(short_strike, step, "up")
    long_ce = short_ce + wing_steps * step
    return [
        StrategyLeg("sell", "CE", short_ce, "anchor"),
        StrategyLeg("buy", "CE", long_ce, "wing"),
    ]


def build_bull_put_spread(*, fno_symbol: str, short_strike: float, wing_steps: int = 2) -> list[StrategyLeg]:
    step = strike_step(fno_symbol)
    short_pe = _round_strike(short_strike, step, "down")
    long_pe = short_pe - wing_steps * step
    return [
        StrategyLeg("sell", "PE", short_pe, "anchor"),
        StrategyLeg("buy", "PE", long_pe, "wing"),
    ]


def _pick_credit_strategy(
    *,
    fno_symbol: str,
    spot: float,
    range_high: float,
    range_low: float,
    iv_tier: str,
    pin_to_spot: bool,
) -> tuple[str, str, list[StrategyLeg], str, list[str], list[str], str | None]:
    """Return strategy_id, name, legs, risk_profile, rationale, risks, safer_alt."""
    label = INDEX_LABEL.get(fno_symbol, fno_symbol)
    range_pct = _range_pct(spot, range_high, range_low)
    rationale: list[str] = []
    risks: list[str] = []

    if iv_tier == "low":
        return (
            "wait_breakout",
            "Wait — IV too low to sell premium",
            [],
            "defined",
            [
                f"{label} is range-bound but **IV is low** — premium selling pays little.",
                "Prefer waiting for OR breakout or use small **long straddle/strangle** only if you expect a big move.",
                "For MIS income, skip until IV rises (events, VIX spike).",
            ],
            ["Low IV = poor credit; directional lottery tickets decay slowly."],
            "Iron Condor when IV rank rises above 50",
        )

    if pin_to_spot and iv_tier in ("mid", "unknown"):
        legs = build_iron_butterfly(fno_symbol=fno_symbol, spot=spot)
        rationale.extend([
            f"Spot ₹{spot:,.0f} is **near range centre** — pin-risk setup.",
            "**Iron Butterfly** (Investopedia #10): sell ATM straddle + OTM wings — defined risk vs naked straddle.",
            "Best when IV is **mid** (GTF: ~1σ zone) and you expect price to stay around CMP.",
        ])
        risks.extend([
            "Exit if spot breaks wing strikes; book 50–70% of max profit before 3:20 MIS square-off.",
            "Gap moves can still hurt — keep size small.",
        ])
        return (
            "iron_butterfly",
            "Iron Butterfly",
            legs,
            "defined",
            rationale,
            risks,
            "Short Straddle (unlimited risk — not recommended for MIS)",
        )

    if iv_tier == "extreme":
        legs = build_iron_condor(
            fno_symbol=fno_symbol, range_high=range_high, range_low=range_low,
        )
        rationale.extend([
            f"**IV very high** — credit strategies collect rich premium (Strike.money: sell when IV elevated).",
            f"Range ₹{range_low:,.0f}–₹{range_high:,.0f} ({range_pct:.2f}% wide) — **Iron Condor** is the safer credit play.",
            "Short strangle/straddle also work in theory but carry **unlimited risk** — use iron condor wings instead.",
        ])
        risks.extend([
            "IV crush helps after entry; sudden expansion hurts all short-vol positions.",
            "Convert to iron condor if you already sold a strangle and price approaches short strike.",
        ])
        safer = "Iron Condor (already selected)"
        return "iron_condor", "Iron Condor", legs, "defined", rationale, risks, safer

    if iv_tier == "high":
        legs = build_iron_condor(
            fno_symbol=fno_symbol, range_high=range_high, range_low=range_low,
        )
        rationale.extend([
            f"Sideways {label} with **high IV** — iron condor sells OTM CE/PE at range edges (GTF / Strike.money).",
            f"Short CE near **₹{range_high:,.0f}** resistance, short PE near **₹{range_low:,.0f}** support.",
            "Defined max loss — safer than short strangle for intraday MIS.",
        ])
        risks.extend([
            "Exit if spot closes outside short strikes; avoid event days (RBI, budget).",
            "Target 50% of credit; square off by **3:20 PM** for MIS.",
        ])
        alt_legs = build_short_strangle(
            fno_symbol=fno_symbol, range_high=range_high, range_low=range_low,
        )
        alt = ", ".join(f"{l.action.upper()} {l.option_type} {l.strike:g}" for l in alt_legs)
        return (
            "iron_condor",
            "Iron Condor",
            legs,
            "defined",
            rationale,
            risks,
            f"Short Strangle ({alt}) — higher credit, unlimited risk",
        )

    # mid / unknown
    legs = build_iron_butterfly(fno_symbol=fno_symbol, spot=spot)
    rationale.extend([
        f"**Mid IV** + sideways — Iron Butterfly often fits better than wide condor (GTF).",
        f"Expect {label} to stay near **₹{spot:,.0f}**; wings protect vs gap moves.",
    ])
    risks.append("Narrower profit zone than iron condor — watch pin risk at ATM.")
    return (
        "iron_butterfly",
        "Iron Butterfly",
        legs,
        "defined",
        rationale,
        risks,
        "Iron Condor if you have a wider S/R range",
    )


def advise_sideways_strategy(
    *,
    fno_symbol: str,
    ce_strike: float | None = None,
    pe_strike: float | None = None,
    option_type: str | None = None,
    strike: float | None = None,
    spot: float | None = None,
    or_high: float | None = None,
    or_low: float | None = None,
    iv_rank: float | None = None,
    iv_band: str = "unknown",
    analytics: OptionsAnalytics | None = None,
    market: str = "india",
) -> SidewaysStrategyAdvice:
    """Recommend credit / neutral strategy from user CE/PE legs and live context."""
    fno = _normalize_fno(fno_symbol)
    yahoo = INDEX_YAHOO.get(fno)

    if spot is None and yahoo:
        spot, _ = get_live_ltp(yahoo, market=market)
    if (or_high is None or or_low is None) and yahoo:
        or_rng = fetch_symbol_opening_range(yahoo, market=market)
        if or_rng:
            or_high, or_low = or_rng

    if analytics:
        iv_rank = iv_rank if iv_rank is not None else analytics.iv_rank
        iv_band = analytics.iv_band or iv_band

    iv_t = _iv_tier(iv_rank, iv_band)
    label = INDEX_LABEL.get(fno, fno)

    # User supplied range via CE/PE strikes (CE = upper, PE = lower anchor)
    range_high = or_high
    range_low = or_low
    if ce_strike and pe_strike:
        range_high = max(ce_strike, pe_strike)
        range_low = min(ce_strike, pe_strike)
        if or_high is not None:
            range_high = max(range_high, or_high)
        if or_low is not None:
            range_low = min(range_low, or_low)
    elif ce_strike is not None:
        range_high = max(ce_strike, or_high or ce_strike)
    elif pe_strike is not None:
        range_low = min(pe_strike, or_low or pe_strike)

    opt = (option_type or "").upper().strip()
    single_strike = strike or (ce_strike if opt == "CE" else pe_strike if opt == "PE" else None)

    # Single directional leg in sideways market
    if single_strike and opt in ("CE", "PE") and spot and range_high and range_low:
        if _spot_inside_range(spot, range_high, range_low):
            if opt == "CE":
                legs = build_bear_call_spread(fno_symbol=fno, short_strike=single_strike)
                return SidewaysStrategyAdvice(
                    strategy_id="bear_call_spread",
                    strategy_name="Bear Call Spread (credit)",
                    market_view="Sideways to mildly bearish",
                    risk_profile="defined",
                    iv_tier=iv_t,
                    spot=spot,
                    range_high=range_high,
                    range_low=range_low,
                    range_pct=_range_pct(spot, range_high, range_low),
                    legs=legs,
                    rationale=[
                        f"You asked about **CE {single_strike:g}** but {label} is **inside OR** (sideways).",
                        "Buying CE fights theta in chop — prefer **credit** (Strike.money: bear call spread).",
                        f"Sell CE near **₹{legs[0].strike:g}**, buy higher CE as hedge.",
                    ],
                    risk_notes=[
                        "Defined risk; exit if spot reclaims above short CE.",
                        "For pure income with range, see Iron Condor below.",
                    ],
                    action="Consider bear call spread instead of buying CE",
                    emoji="🟡",
                    blocks_directional=True,
                )
            legs = build_bull_put_spread(fno_symbol=fno, short_strike=single_strike)
            return SidewaysStrategyAdvice(
                strategy_id="bull_put_spread",
                strategy_name="Bull Put Spread (credit)",
                market_view="Sideways to mildly bullish",
                risk_profile="defined",
                iv_tier=iv_t,
                spot=spot,
                range_high=range_high,
                range_low=range_low,
                range_pct=_range_pct(spot, range_high, range_low),
                legs=legs,
                rationale=[
                    f"You asked about **PE {single_strike:g}** but {label} is **inside OR** (sideways).",
                    "Buying PE in chop bleeds premium — **bull put spread** earns theta (Investopedia credit spread).",
                    f"Sell PE near **₹{legs[0].strike:g}**, buy lower PE as hedge.",
                ],
                risk_notes=[
                    "Defined risk; exit if spot breaks below short PE.",
                    "Matches your PE thesis with less decay pain.",
                ],
                action="Consider bull put spread instead of buying PE",
                emoji="🟡",
                blocks_directional=True,
            )

    if not spot or not range_high or not range_low:
        return SidewaysStrategyAdvice(
            strategy_id="no_data",
            strategy_name="Need spot + range",
            market_view="Unknown",
            risk_profile="defined",
            iv_tier=iv_t,
            spot=spot,
            range_high=range_high,
            range_low=range_low,
            range_pct=None,
            rationale=["Connect Kite / wait for live index + opening range."],
            action="Wait for data",
            emoji="⚪",
        )

    range_pct = _range_pct(spot, range_high, range_low)
    pin = range_pct < 0.55 and _spot_inside_range(spot, range_high, range_low)
    dist_high = abs(spot - range_high) / spot * 100 if spot else 0
    dist_low = abs(spot - range_low) / spot * 100 if spot else 0
    pin = pin or (dist_high < 0.25 and dist_low < 0.25)

    sid, name, legs, risk_prof, rationale, risks, safer = _pick_credit_strategy(
        fno_symbol=fno,
        spot=spot,
        range_high=range_high,
        range_low=range_low,
        iv_tier=iv_t,
        pin_to_spot=pin,
    )

    emoji = "🟢" if sid in ("iron_condor", "iron_butterfly") else "🟡"
    if sid == "wait_breakout":
        emoji = "⚪"

    sideways_note = ""
    if _spot_inside_range(spot, range_high, range_low):
        sideways_note = f"Spot **inside range** ({range_pct:.2f}% OR width) — non-directional credit fits."
    else:
        sideways_note = f"Spot **outside** OR centre — condor wings may need wider strikes."
    rationale.insert(0, sideways_note)

    try:
        regime = detect_nifty_regime(symbol=yahoo or "^NSEI")
        if regime.regime == "Range-bound":
            rationale.append(f"Nifty regime: **{regime.regime}** (ADX) — aligns with income strategies.")
    except Exception:
        pass

    return SidewaysStrategyAdvice(
        strategy_id=sid,
        strategy_name=name,
        market_view="Sideways / range-bound",
        risk_profile=risk_prof,
        iv_tier=iv_t,
        spot=spot,
        range_high=range_high,
        range_low=range_low,
        range_pct=range_pct,
        legs=legs,
        rationale=rationale,
        risk_notes=risks,
        action=f"Primary: **{name}** — execute all legs together; MIS square-off ~3:20 PM",
        safer_alternative=safer,
        emoji=emoji,
    )


def advise_from_chain(
    *,
    fno_symbol: str,
    chain: Any,
    ce_strike: float | None = None,
    pe_strike: float | None = None,
    option_type: str | None = None,
    strike: float | None = None,
    market: str = "india",
) -> SidewaysStrategyAdvice:
    analytics = None
    iv_rank = None
    iv_band = "unknown"
    if chain is not None:
        try:
            analytics = analyze_and_record_chain(chain)
            iv_rank = analytics.iv_rank
            iv_band = analytics.iv_band
        except Exception:
            pass
    spot = getattr(chain, "spot", None) if chain else None
    return advise_sideways_strategy(
        fno_symbol=fno_symbol,
        ce_strike=ce_strike,
        pe_strike=pe_strike,
        option_type=option_type,
        strike=strike,
        spot=spot,
        iv_rank=iv_rank,
        iv_band=iv_band,
        analytics=analytics,
        market=market,
    )


def format_legs_table(legs: list[StrategyLeg]) -> list[dict[str, str]]:
    rows = []
    for leg in legs:
        rows.append({
            "Action": leg.action.upper(),
            "Type": leg.option_type,
            "Strike": f"{leg.strike:g}",
            "Role": leg.role,
        })
    return rows


def strategy_comparison_rows() -> list[dict[str, str]]:
    """Quick reference — sideways credit strategies."""
    return [
        {
            "Strategy": "Iron Condor",
            "When": "Known upper/lower range · high IV",
            "Risk": "Defined",
            "IV": "High",
        },
        {
            "Strategy": "Iron Butterfly",
            "When": "Price pinned near CMP · mid IV",
            "Risk": "Defined",
            "IV": "Mid",
        },
        {
            "Strategy": "Short Strangle",
            "When": "Wide range · very high IV",
            "Risk": "Unlimited",
            "IV": "Very high",
        },
        {
            "Strategy": "Short Straddle",
            "When": "Strong pin at ATM · very high IV",
            "Risk": "Unlimited",
            "IV": "Very high",
        },
        {
            "Strategy": "Bear Call / Bull Put Spread",
            "When": "Mild bias inside range",
            "Risk": "Defined",
            "IV": "High",
        },
    ]
