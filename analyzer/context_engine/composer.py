"""Context composer — parallel orchestration of existing producers (no market math)."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.context_engine.models import ContextSnapshot
from analyzer.context_engine.normalizer import (
    build_trading_restrictions,
    compute_confidence,
    normalize_breadth,
    normalize_liquidity,
    normalize_market_phase,
    normalize_regime,
    normalize_risk_mode,
    normalize_volatility,
    validate_snapshot_fields,
)

IST = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)


def _safe_call(name: str, fn, errors: list[str]) -> Any:
    try:
        return fn()
    except Exception as exc:
        msg = f"{name}: {exc}"
        logger.warning("context compose %s", msg)
        errors.append(msg[:200])
        return None


def _macro_state_dict(macro) -> dict[str, Any]:
    if macro is None:
        return {"status": "GAP", "errors": ["macro_unavailable"]}
    sectors = [
        {"name": s.name, "symbol": s.symbol, "change_1d_pct": s.change_1d_pct}
        for s in getattr(macro, "sectors", [])[:12]
    ]
    return {
        "fetched_at": getattr(macro, "fetched_at", ""),
        "vix_regime": getattr(macro, "vix_regime", "") or "unknown",
        "vix_price": getattr(getattr(macro, "india_vix", None), "price", None),
        "fii_dii_summary": getattr(getattr(macro, "fii_dii", None), "summary", ""),
        "premarket_note": getattr(macro, "premarket_note", ""),
        "sectors": sectors,
        "errors": list(getattr(macro, "errors", []) or []),
    }


def _sector_strength_dict(macro) -> dict[str, Any]:
    if macro is None:
        return {"leader": "unknown", "laggard": "unknown", "ranked": []}
    ranked = [
        {"name": s.name, "change_1d_pct": s.change_1d_pct}
        for s in sorted(
            getattr(macro, "sectors", []),
            key=lambda q: q.change_1d_pct if q.change_1d_pct is not None else -999.0,
            reverse=True,
        )[:8]
    ]
    return {
        "leader": getattr(macro, "sector_leader", "") or "unknown",
        "laggard": getattr(macro, "sector_laggard", "") or "unknown",
        "ranked": ranked,
    }


def _global_state_dict(report) -> dict[str, Any]:
    if report is None:
        return {"status": "GAP", "bias": "unknown", "spillover_score": None}
    return {
        "fetched_at": getattr(report, "fetched_at", ""),
        "bias": getattr(report, "predicted_nifty_bias", "unknown"),
        "spillover_score": getattr(report, "spillover_score", None),
        "predicted_move_pct": getattr(report, "predicted_move_pct", None),
        "confidence": getattr(report, "confidence", ""),
        "india_action": getattr(report, "india_action", ""),
        "drivers": list(getattr(report, "drivers", [])[:5]),
        "risks": list(getattr(report, "risks", [])[:5]),
    }


def _industry_strength_dict() -> dict[str, Any]:
    return {"status": "GAP", "note": "Industry-level strength not yet available"}


def _earnings_restrictions(events) -> list[str]:
    if not events:
        return []
    critical = [
        e.nse_symbol
        for e in events
        if getattr(e, "risk_band", "") == "critical" and getattr(e, "days_until", 99) is not None
    ]
    return critical


def compose_context_snapshot(
    *,
    market: str = "india",
    now: datetime | None = None,
    include_global: bool = True,
    period: str = "6mo",
) -> ContextSnapshot:
    """Parallel compose from canonical producers — composition only."""
    now = now or datetime.now(IST)
    errors: list[str] = []

    from analyzer.data_health import build_data_health
    from analyzer.earnings_calendar import fetch_nifty50_earnings, upcoming_within_days
    from analyzer.global_impact import build_india_impact_report
    from analyzer.india_macro import build_india_macro_snapshot
    from analyzer.intraday_beginner_tips import session_timing_advice
    from analyzer.market_regime import detect_nifty_regime
    from analyzer.market_session import market_session_status
    from analyzer.prep_status import prep_incomplete_reasons, prep_status_for

    futures: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures["session"] = pool.submit(_safe_call, "session", market_session_status, errors)
        futures["timing"] = pool.submit(_safe_call, "timing", lambda: session_timing_advice(now), errors)
        futures["regime"] = pool.submit(_safe_call, "regime", lambda: detect_nifty_regime(period), errors)
        futures["macro"] = pool.submit(_safe_call, "macro", build_india_macro_snapshot, errors)
        futures["data_health"] = pool.submit(_safe_call, "data_health", build_data_health, errors)
        futures["prep"] = pool.submit(_safe_call, "prep", prep_status_for, errors)
        if include_global:
            futures["global"] = pool.submit(_safe_call, "global", build_india_impact_report, errors)
        futures["earnings"] = pool.submit(
            _safe_call,
            "earnings",
            lambda: upcoming_within_days(fetch_nifty50_earnings(market=market), days=7),
            errors,
        )

        results: dict[str, Any] = {}
        for key, fut in futures.items():
            results[key] = fut.result()

    session = results.get("session") or {
        "status": "Unknown",
        "is_open": False,
        "phase": "closed",
        "next_session": "",
        "time_ist": now.strftime("%H:%M:%S IST"),
        "date": now.strftime("%Y-%m-%d"),
    }
    timing = results.get("timing")
    regime_obj = results.get("regime")
    macro = results.get("macro")
    global_r = results.get("global")
    data_health = results.get("data_health")
    prep = results.get("prep") or {}
    earnings = results.get("earnings") or []

    regime_label = normalize_regime(getattr(regime_obj, "regime", None) if regime_obj else None)
    regime_detail = {}
    if regime_obj is not None:
        regime_detail = {
            "adx": getattr(regime_obj, "adx", None),
            "plus_di": getattr(regime_obj, "plus_di", None),
            "minus_di": getattr(regime_obj, "minus_di", None),
            "allow_aggressive_intraday": getattr(regime_obj, "allow_aggressive_intraday", True),
            "allow_aggressive_swing": getattr(regime_obj, "allow_aggressive_swing", True),
            "banner": getattr(regime_obj, "banner", ""),
            "message": getattr(regime_obj, "message", ""),
        }
    timing_phase = getattr(timing, "phase", session.get("phase", "closed")) if timing else session.get("phase", "closed")
    is_open = bool(session.get("is_open"))
    market_phase = normalize_market_phase(session.get("phase", "closed"), timing_phase, is_open=is_open)

    vix_price = getattr(getattr(macro, "india_vix", None), "price", None) if macro else None
    volatility_state = normalize_volatility(
        getattr(macro, "vix_regime", None) if macro else None,
        vix_price=vix_price,
    )
    liquidity_state = normalize_liquidity(
        data_health_ok=bool(getattr(data_health, "ok_for_live_cockpit", False)) if data_health else False,
        session_open=is_open,
    )
    spillover = getattr(global_r, "spillover_score", None) if global_r else None
    allow_entries = bool(getattr(timing, "allow_new_entries", False)) if timing else False
    prefer_exit = bool(getattr(timing, "prefer_exit", False)) if timing else False

    risk_mode = normalize_risk_mode(
        session_open=is_open,
        session_phase=session.get("phase", "closed"),
        regime=regime_label,
        spillover_score=spillover,
        volatility_state=volatility_state,
        allow_new_entries=allow_entries,
    )

    prep_missing = prep_incomplete_reasons(prep) if prep else []
    earnings_critical = _earnings_restrictions(earnings)
    data_warning = getattr(data_health, "warning", "") if data_health else ""

    restrictions = tuple(
        build_trading_restrictions(
            timing_headline=getattr(timing, "headline", "") if timing else "",
            allow_new_entries=allow_entries,
            prefer_exit=prefer_exit,
            prep_incomplete=prep_missing,
            earnings_critical=earnings_critical,
            data_warning=data_warning,
            regime=regime_label,
        )
    )

    confidence = compute_confidence(
        errors=errors,
        regime_known=regime_label != "Unknown",
        macro_ok=macro is not None,
        global_ok=global_r is not None,
    )

    validate_snapshot_fields(
        market_regime=regime_label,
        market_phase=market_phase,
        market_breadth=normalize_breadth(),
        volatility_state=volatility_state,
        liquidity_state=liquidity_state,
        risk_mode=risk_mode,
    )

    timestamp = now.strftime("%Y-%m-%d %H:%M:%S IST")
    return ContextSnapshot.create(
        timestamp=timestamp,
        market_regime=regime_label,
        market_phase=market_phase,
        market_breadth=normalize_breadth(),
        volatility_state=volatility_state,
        liquidity_state=liquidity_state,
        market_session=dict(session),
        sector_strength=_sector_strength_dict(macro),
        industry_strength=_industry_strength_dict(),
        macro_state=_macro_state_dict(macro),
        global_market_state=_global_state_dict(global_r),
        risk_mode=risk_mode,
        trading_restrictions=list(restrictions),
        confidence=confidence,
        metadata={
            "market": market,
            "errors": errors,
            "producers": [
                "market_session",
                "intraday_beginner_tips",
                "market_regime",
                "india_macro",
                "global_impact",
                "data_health",
                "prep_status",
                "earnings_calendar",
            ],
            "prep_status": dict(prep) if prep else {},
            "data_health_ok": bool(getattr(data_health, "ok_for_live_cockpit", False)) if data_health else False,
            "timing_phase": timing_phase,
            "allow_new_entries": allow_entries,
            "prefer_exit": prefer_exit,
            "regime_detail": regime_detail,
            "context_snapshot_producers_only": True,
        },
    )
