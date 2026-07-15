"""Context normalizer — map producer outputs to canonical enums (no market math)."""

from __future__ import annotations

from analyzer.context_engine.models import (
    VALID_BREADTH,
    VALID_LIQUIDITY,
    VALID_PHASES,
    VALID_REGIMES,
    VALID_RISK_MODES,
    VALID_VOLATILITY,
)


def normalize_regime(raw: str | None) -> str:
    if not raw:
        return "Unknown"
    label = str(raw).strip()
    if label in VALID_REGIMES:
        return label
    return "Unknown"


def normalize_market_phase(session_phase: str, timing_phase: str, *, is_open: bool) -> str:
    if not is_open:
        if session_phase in ("weekend", "holiday"):
            return session_phase
        if session_phase == "pre_market":
            return "pre_market"
        return "closed"
    mapping = {
        "pre_open": "pre_market",
        "opening": "opening",
        "core": "mid_session",
        "wind_down": "wind_down",
        "open": "mid_session",
    }
    phase = mapping.get(timing_phase, timing_phase)
    if phase in VALID_PHASES:
        return phase
    return "mid_session" if is_open else "closed"


def normalize_volatility(vix_regime: str | None, vix_price: float | None = None) -> str:
    text = (vix_regime or "").lower()
    if vix_price is not None:
        if vix_price >= 20:
            return "high_fear"
        if vix_price >= 15:
            return "elevated"
        if vix_price <= 12:
            return "low"
        return "normal"
    if "high fear" in text:
        return "high_fear"
    if "elevated" in text or "cautious" in text:
        return "elevated"
    if "low fear" in text or "complacency" in text:
        return "low"
    if "normal" in text:
        return "normal"
    return "unknown"


def normalize_liquidity(*, data_health_ok: bool, session_open: bool) -> str:
    if not session_open:
        return "unknown"
    return "normal" if data_health_ok else "thin"


def normalize_breadth() -> str:
    """Market breadth not yet computed — honest GAP."""
    return "unknown"


def normalize_risk_mode(
    *,
    session_open: bool,
    session_phase: str,
    regime: str,
    spillover_score: float | None,
    volatility_state: str,
    allow_new_entries: bool,
) -> str:
    if not session_open or session_phase in ("weekend", "holiday", "closed", "after_hours"):
        return "CLOSED"
    if not allow_new_entries:
        return "RISK-OFF"
    bearish_regime = regime in ("Trending Bearish", "Range-bound")
    high_fear = volatility_state in ("high_fear", "elevated")
    spill = spillover_score if spillover_score is not None else 0.0

    if bearish_regime and high_fear and spill < -15:
        return "RISK-OFF"
    if regime == "Trending Bullish" and spill > 10 and volatility_state in ("low", "normal"):
        return "RISK-ON"
    if spill < -25 or (bearish_regime and spill < -5):
        return "RISK-OFF"
    return "NEUTRAL"


def build_trading_restrictions(
    *,
    timing_headline: str,
    allow_new_entries: bool,
    prefer_exit: bool,
    prep_incomplete: list[str],
    earnings_critical: list[str],
    data_warning: str,
    regime: str,
) -> list[str]:
    restrictions: list[str] = []
    if not allow_new_entries and timing_headline:
        restrictions.append(timing_headline)
    if prefer_exit:
        restrictions.append("Prefer exiting positions — wind-down session")
    if regime == "Range-bound":
        restrictions.append("Range-bound regime — reduce aggressive intraday size")
    for reason in prep_incomplete[:2]:
        restrictions.append(reason)
    for sym in earnings_critical[:3]:
        restrictions.append(f"Earnings risk: {sym}")
    if data_warning:
        restrictions.append(data_warning)
    return restrictions


def compute_confidence(
    *,
    errors: list[str],
    regime_known: bool,
    macro_ok: bool,
    global_ok: bool,
) -> float:
    base = 70.0
    if regime_known:
        base += 8.0
    if macro_ok:
        base += 8.0
    if global_ok:
        base += 6.0
    base -= min(len(errors) * 8.0, 40.0)
    return max(0.0, min(100.0, round(base, 1)))


def validate_snapshot_fields(
    *,
    market_regime: str,
    market_phase: str,
    market_breadth: str,
    volatility_state: str,
    liquidity_state: str,
    risk_mode: str,
) -> None:
    if market_regime not in VALID_REGIMES:
        raise ValueError(f"Invalid market_regime: {market_regime}")
    if market_phase not in VALID_PHASES:
        raise ValueError(f"Invalid market_phase: {market_phase}")
    if market_breadth not in VALID_BREADTH:
        raise ValueError(f"Invalid market_breadth: {market_breadth}")
    if volatility_state not in VALID_VOLATILITY:
        raise ValueError(f"Invalid volatility_state: {volatility_state}")
    if liquidity_state not in VALID_LIQUIDITY:
        raise ValueError(f"Invalid liquidity_state: {liquidity_state}")
    if risk_mode not in VALID_RISK_MODES:
        raise ValueError(f"Invalid risk_mode: {risk_mode}")
