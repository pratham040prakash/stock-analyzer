"""Live CE/PE coach — synthesize OR gate, reversal, regime, sideways strategies."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.nse_options import fetch_option_chain
from analyzer.opening_range_confirm import fetch_symbol_opening_range
from analyzer.options_analytics import analyze_and_record_chain, guidance_for_horizon
from analyzer.options_entry_gate import OptionsEntryGate, assess_option_entry_gate
from analyzer.options_reversal_alerts import (
    INDEX_LABEL,
    INDEX_YAHOO,
    IndexReversalStatus,
    assess_option_index_thesis,
)
from analyzer.providers import data_source_status, get_live_ltp
from analyzer.sideways_options_advisor import (
    SidewaysStrategyAdvice,
    advise_from_chain,
    strike_step,
)
from analyzer.watchlist_plan_tracker import assess_options_live_plan

IST = ZoneInfo("Asia/Kolkata")
_CHAIN_CACHE: dict[str, tuple[float, Any]] = {}
_CHAIN_TTL_SEC = 30.0


@dataclass
class CoachSignal:
    category: str
    emoji: str
    headline: str
    detail: str
    action: str
    priority: int


@dataclass
class LiveOptionsCoachSnapshot:
    fno_symbol: str
    option_type: str
    strike: float
    spot: float | None
    premium: float | None
    or_high: float | None
    or_low: float | None
    spot_vs_or: str
    updated_at: str
    primary_emoji: str
    primary_action: str
    whats_happening: str
    signals: list[CoachSignal] = field(default_factory=list)
    gate: OptionsEntryGate | None = None
    reversal: IndexReversalStatus | None = None
    sideways: SidewaysStrategyAdvice | None = None
    regime_banner: str = ""
    iv_guidance: str = ""
    premium_status: str = ""
    data_source: str = ""
    expiry: str = ""


def _atm_strike(fno_symbol: str, spot: float) -> float:
    step = strike_step(fno_symbol)
    return round(spot / step) * step


def _spot_vs_or_label(
    spot: float | None,
    or_high: float | None,
    or_low: float | None,
) -> str:
    if spot is None or or_high is None or or_low is None:
        return "OR loading"
    if spot > or_high:
        return f"above OR high (₹{or_high:,.0f})"
    if spot < or_low:
        return f"below OR low (₹{or_low:,.0f})"
    return f"inside OR ₹{or_low:,.0f}–₹{or_high:,.0f}"


def _cached_chain(fno_symbol: str, *, force: bool = False) -> Any | None:
    key = fno_symbol.upper()
    now = time.time()
    if not force and key in _CHAIN_CACHE:
        ts, chain = _CHAIN_CACHE[key]
        if now - ts < _CHAIN_TTL_SEC:
            return chain
    try:
        chain = fetch_option_chain(fno_symbol)
    except Exception:
        return _CHAIN_CACHE.get(key, (0, None))[1]
    _CHAIN_CACHE[key] = (now, chain)
    return chain


def _premium_from_chain(chain: Any, option_type: str, strike: float) -> float | None:
    if chain is None:
        return None
    opt = option_type.upper()
    for leg in chain.legs:
        if leg.option_type == opt and abs(leg.strike - strike) < 0.01:
            return leg.ltp
    return None


def _pick_primary(signals: list[CoachSignal]) -> tuple[str, str]:
    if not signals:
        return "⚪", "Wait for live data"
    best = min(signals, key=lambda s: s.priority)
    return best.emoji, best.action


def build_live_options_coach(
    *,
    fno_symbol: str,
    option_type: str,
    strike: float,
    market: str = "india",
    now: datetime | None = None,
    force_chain: bool = False,
) -> LiveOptionsCoachSnapshot:
    """One live read — gate, reversal, regime, sideways, premium ladder."""
    now = now or datetime.now(IST)
    fno = fno_symbol.upper().strip()
    opt = option_type.upper().strip()
    yahoo = INDEX_YAHOO.get(fno)
    index_label = INDEX_LABEL.get(fno, fno)

    spot: float | None = None
    or_high: float | None = None
    or_low: float | None = None
    if yahoo:
        spot, _ = get_live_ltp(yahoo, market=market)
        or_rng = fetch_symbol_opening_range(yahoo, market=market)
        if or_rng:
            or_high, or_low = or_rng

    chain = _cached_chain(fno, force=force_chain)
    premium = _premium_from_chain(chain, opt, strike)
    expiry = getattr(chain, "expiry", "") if chain else ""

    ds = data_source_status()
    data_source = "Kite live" if ds.get("kite_live_data") else "Yahoo (~15 min lag)"

    gate = assess_option_entry_gate(
        opt,
        fno_symbol=fno,
        strike=strike,
        spot=spot,
        or_high=or_high,
        or_low=or_low,
        now=now,
    )

    reversal: IndexReversalStatus | None = None
    if or_high is not None and or_low is not None:
        reversal = assess_option_index_thesis(
            opt,
            fno_symbol=fno,
            strike=strike,
            spot=spot,
            or_high=or_high,
            or_low=or_low,
            now=now,
        )

    sideways = advise_from_chain(
        fno_symbol=fno,
        chain=chain,
        option_type=opt,
        strike=strike,
        market=market,
    )

    regime_banner = ""
    if yahoo:
        try:
            from analyzer.context_engine import build_context_snapshot
            from analyzer.context_engine.migration import regime_from_snapshot

            regime = regime_from_snapshot(build_context_snapshot(market=market))
            if regime:
                regime_banner = regime.banner
        except Exception:
            pass

    iv_guidance = ""
    if chain is not None:
        try:
            analytics = analyze_and_record_chain(chain)
            iv_guidance = guidance_for_horizon(analytics, horizon="options")
        except Exception:
            pass

    premium_status = ""
    if premium and premium > 0:
        ladder_plan = assess_options_live_plan(
            premium,
            entry=premium,
            stop_loss=round(premium * 0.65, 2),
            target=round(premium * 1.5, 2),
            label=f"{fno} {opt}",
        )
        premium_status = f"{ladder_plan.emoji} {ladder_plan.label} — {ladder_plan.detail}"

    signals: list[CoachSignal] = []

    if reversal and reversal.phase == "invalidated":
        signals.append(
            CoachSignal(
                "reversal",
                reversal.emoji,
                reversal.label,
                reversal.detail,
                reversal.action,
                priority=1,
            )
        )

    if gate.phase == "do_not_enter":
        signals.append(
            CoachSignal(
                "gate",
                gate.emoji,
                gate.headline,
                gate.detail,
                gate.action,
                priority=2,
            )
        )
    elif gate.phase == "observe":
        signals.append(
            CoachSignal(
                "gate",
                gate.emoji,
                gate.headline,
                gate.detail,
                gate.action,
                priority=3,
            )
        )
    elif sideways and sideways.blocks_directional:
        signals.append(
            CoachSignal(
                "sideways",
                sideways.emoji,
                f"Chop — use {sideways.strategy_name}",
                " · ".join(sideways.rationale[:2]),
                sideways.action,
                priority=4,
            )
        )
    elif gate.phase == "enter_ok" and reversal and reversal.phase == "ok":
        signals.append(
            CoachSignal(
                "gate",
                gate.emoji,
                gate.headline,
                gate.detail,
                f"{gate.action} · {reversal.action}",
                priority=5,
            )
        )
    elif gate.phase == "wait":
        signals.append(
            CoachSignal(
                "gate",
                gate.emoji,
                gate.headline,
                gate.detail,
                gate.action,
                priority=6,
            )
        )

    if sideways and sideways.strategy_id not in ("no_data",) and not sideways.blocks_directional:
        signals.append(
            CoachSignal(
                "sideways",
                sideways.emoji,
                f"Alt: {sideways.strategy_name}",
                sideways.action,
                "Consider if directional thesis weakens",
                priority=8,
            )
        )

    if iv_guidance:
        signals.append(
            CoachSignal(
                "iv",
                "📊",
                "IV context",
                iv_guidance,
                "Size per IV — avoid lottery OTM when expensive",
                priority=9,
            )
        )

    if premium_status and "stop" in premium_status.lower():
        signals.append(
            CoachSignal(
                "premium",
                "🛑",
                "Premium stop zone",
                premium_status,
                "Exit or trail — premium near stop",
                priority=2,
            )
        )
    elif premium_status and ("target" in premium_status.lower() or "T1" in premium_status):
        signals.append(
            CoachSignal(
                "premium",
                "🎯",
                "Premium target zone",
                premium_status,
                "Book 40–50% · trail stop to breakeven",
                priority=5,
            )
        )

    primary_emoji, primary_action = _pick_primary(signals)
    spot_label = _spot_vs_or_label(spot, or_high, or_low)

    whats = []
    if spot is not None:
        whats.append(f"{index_label} **₹{spot:,.0f}** · {spot_label}")
    if premium is not None:
        whats.append(f"{opt} **{strike:g}** premium **₹{premium:,.2f}**")
    elif chain is None:
        whats.append("Option chain loading — NSE may be slow")
    if regime_banner:
        whats.append(regime_banner)

    return LiveOptionsCoachSnapshot(
        fno_symbol=fno,
        option_type=opt,
        strike=strike,
        spot=spot,
        premium=premium,
        or_high=or_high,
        or_low=or_low,
        spot_vs_or=spot_label,
        updated_at=now.strftime("%H:%M:%S IST"),
        primary_emoji=primary_emoji,
        primary_action=primary_action,
        whats_happening=" · ".join(whats) if whats else "Waiting for live quotes…",
        signals=signals,
        gate=gate,
        reversal=reversal,
        sideways=sideways,
        regime_banner=regime_banner,
        iv_guidance=iv_guidance,
        premium_status=premium_status,
        data_source=data_source,
        expiry=expiry,
    )


def suggest_strike(
    fno_symbol: str,
    _option_type: str,
    *,
    market: str = "india",
) -> float | None:
    """ATM strike from live spot."""
    yahoo = INDEX_YAHOO.get(fno_symbol.upper())
    if not yahoo:
        return None
    spot, _ = get_live_ltp(yahoo, market=market)
    if spot is None or spot <= 0:
        return None
    return _atm_strike(fno_symbol, spot)
