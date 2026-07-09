"""9:45 OR gate + OTM strike checks before index CE/PE entry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.intraday_beginner_tips import OPENING_OBSERVE_UNTIL
from analyzer.opening_range_confirm import fetch_symbol_opening_range
from analyzer.options_reversal_alerts import INDEX_LABEL, INDEX_YAHOO
from analyzer.providers import get_live_ltp

IST = ZoneInfo("Asia/Kolkata")

WARN_OTM_PCT = 2.0
BLOCK_OTM_PCT = 3.5


@dataclass
class OptionsEntryGate:
    fno_symbol: str
    option_type: str
    strike: float
    spot: float | None
    or_high: float | None
    or_low: float | None
    otm_pct: float | None
    phase: str  # observe | wait | enter_ok | do_not_enter
    allowed: bool
    emoji: str
    headline: str
    detail: str
    action: str
    checks: list[str] = field(default_factory=list)


def _past_or_window(now: datetime) -> bool:
    cutoff = now.replace(
        hour=OPENING_OBSERVE_UNTIL[0],
        minute=OPENING_OBSERVE_UNTIL[1],
        second=0,
        microsecond=0,
    )
    return now >= cutoff


def _otm_pct(option_type: str, strike: float, spot: float) -> float | None:
    opt = option_type.upper()
    if spot <= 0:
        return None
    if opt == "PE" and spot > strike:
        return (spot - strike) / spot * 100.0
    if opt == "CE" and strike > spot:
        return (strike - spot) / spot * 100.0
    return 0.0


def assess_option_entry_gate(
    option_type: str,
    *,
    fno_symbol: str,
    strike: float,
    spot: float | None,
    or_high: float | None,
    or_low: float | None,
    now: datetime | None = None,
) -> OptionsEntryGate:
    """Gate MIS index option entries — learn-from-mistake rules."""
    now = now or datetime.now(IST)
    opt = option_type.upper().strip()
    index_label = INDEX_LABEL.get(fno_symbol.upper(), fno_symbol)
    checks: list[str] = []

    base = OptionsEntryGate(
        fno_symbol=fno_symbol.upper(),
        option_type=opt,
        strike=float(strike),
        spot=spot,
        or_high=or_high,
        or_low=or_low,
        otm_pct=None,
        phase="wait",
        allowed=False,
        emoji="⚪",
        headline="Checking…",
        detail="",
        action="Wait",
        checks=checks,
    )

    if now.weekday() >= 5:
        base.phase = "observe"
        base.emoji = "⚪"
        base.headline = "Market closed"
        base.detail = "No MIS entries on weekends."
        base.action = "No trade"
        return base

    if spot is None or spot <= 0:
        base.headline = "No index LTP"
        base.detail = "Connect Kite or wait for live index price."
        base.action = "Wait for data"
        checks.append("□ Index live price available")
        base.checks = checks
        return base

    otm = _otm_pct(opt, float(strike), spot)
    base.otm_pct = otm

    if not _past_or_window(now):
        base.phase = "observe"
        base.emoji = "🟡"
        base.headline = "Wait until 9:45 AM"
        base.detail = (
            f"Observe opening range only. {index_label} ₹{spot:,.0f} · "
            f"note OR when formed."
        )
        base.action = "No entry before 9:45 IST"
        checks.extend([
            "□ Wait until 9:45 AM IST",
            "□ Note OR high and OR low on chart",
            "□ Stop on Kite ready before entry",
        ])
        base.checks = checks
        return base

    checks.append("☑ After 9:45 AM")

    if otm is not None and otm >= BLOCK_OTM_PCT:
        base.phase = "do_not_enter"
        base.emoji = "🔴"
        base.headline = "Strike too far OTM"
        base.detail = (
            f"{opt} {strike:g} is **{otm:.1f}%** OTM vs spot ₹{spot:,.0f} — "
            "needs a very large move; skip or pick nearer ATM."
        )
        base.action = "Do not enter — pick nearer strike or skip"
        checks.append(f"□ OTM {otm:.1f}% — too far (max {BLOCK_OTM_PCT:g}%)")
        base.checks = checks
        return base

    if otm is not None and otm >= WARN_OTM_PCT:
        checks.append(f"⚠ OTM {otm:.1f}% — size small or skip")

    if or_high is None or or_low is None:
        base.headline = "OR not ready"
        base.detail = "Opening range not available yet — wait 1–2 candles."
        base.action = "Wait for OR"
        checks.append("□ OR high/low loaded")
        base.checks = checks
        return base

    checks.append(f"☑ OR ₹{or_low:,.0f}–₹{or_high:,.0f}")

    if opt == "PE":
        if spot > or_high:
            base.phase = "do_not_enter"
            base.emoji = "🔴"
            base.headline = "DO NOT ENTER PE"
            base.detail = (
                f"{index_label} **₹{spot:,.0f}** above OR high **₹{or_high:,.0f}** — "
                "bearish PE not confirmed."
            )
            base.action = "Exit if held · wait for breakdown below OR low"
            checks.append("□ Spot ≤ OR low for PE entry")
        elif spot <= or_low:
            base.phase = "enter_ok"
            base.allowed = True
            base.emoji = "🟢"
            base.headline = "PE entry OK (OR breakdown)"
            base.detail = (
                f"Spot ₹{spot:,.0f} ≤ OR low ₹{or_low:,.0f}. "
                "Enter only if premium near plan + stop on Kite."
            )
            base.action = "May enter PE with stop"
            checks.append("☑ OR breakdown for PE")
        else:
            base.phase = "wait"
            base.emoji = "🟡"
            base.headline = "Wait — PE not confirmed"
            base.detail = (
                f"Spot ₹{spot:,.0f} inside OR — need break below **₹{or_low:,.0f}**."
            )
            base.action = "Wait for OR low break"
            checks.append("□ Spot ≤ OR low for PE")
    else:  # CE
        if spot < or_low:
            base.phase = "do_not_enter"
            base.emoji = "🔴"
            base.headline = "DO NOT ENTER CE"
            base.detail = (
                f"{index_label} **₹{spot:,.0f}** below OR low **₹{or_low:,.0f}** — "
                "bullish CE not confirmed."
            )
            base.action = "Exit if held · wait for reclaim above OR high"
            checks.append("□ Spot ≥ OR high for CE entry")
        elif spot >= or_high:
            base.phase = "enter_ok"
            base.allowed = True
            base.emoji = "🟢"
            base.headline = "CE entry OK (OR breakout)"
            base.detail = (
                f"Spot ₹{spot:,.0f} ≥ OR high ₹{or_high:,.0f}. "
                "Enter only if premium near plan + stop on Kite."
            )
            base.action = "May enter CE with stop"
            checks.append("☑ OR breakout for CE")
        else:
            base.phase = "wait"
            base.emoji = "🟡"
            base.headline = "Wait — CE not confirmed"
            base.detail = (
                f"Spot ₹{spot:,.0f} inside OR — need break above **₹{or_high:,.0f}**."
            )
            base.action = "Wait for OR high break"
            checks.append("□ Spot ≥ OR high for CE")

    checks.append("□ Premium stop placed on Kite before entry")
    base.checks = checks
    return base


def assess_pick_entry_gate(
    pick: Any,
    *,
    market: str = "india",
    now: datetime | None = None,
) -> OptionsEntryGate | None:
    fno = getattr(pick, "fno_symbol", pick.get("fno_symbol") if isinstance(pick, dict) else "")
    opt = getattr(pick, "option_type", pick.get("option_type") if isinstance(pick, dict) else "")
    strike = float(getattr(pick, "strike", pick.get("strike", 0) if isinstance(pick, dict) else 0))
    yahoo = INDEX_YAHOO.get(str(fno).upper())
    if not yahoo:
        return None
    or_rng = fetch_symbol_opening_range(yahoo, market=market)
    or_high, or_low = (or_rng if or_rng else (None, None))
    spot, _ = get_live_ltp(yahoo, market=market)
    return assess_option_entry_gate(
        str(opt),
        fno_symbol=str(fno),
        strike=strike,
        spot=spot,
        or_high=or_high,
        or_low=or_low,
        now=now,
    )


def gate_label_short(gate: OptionsEntryGate) -> str:
    return f"{gate.emoji} {gate.headline}"
