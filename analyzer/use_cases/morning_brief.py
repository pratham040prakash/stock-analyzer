"""Morning Brief application use case — Context → Decision → Evidence → Trust (ETS-003b v0.2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.context_engine import build_context_snapshot
from analyzer.context_engine.cache import cache_age_sec, get_cached
from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.intraday_prefs import IntradayPrefs, load_intraday_prefs
from analyzer.investment_os import InvestmentOS, build_investment_os
from analyzer.mis_trade_advisory import MisTradeAdvisory, build_mis_trade_advisory
from analyzer.use_cases.morning_brief_assembly import (
    assemble_morning_brief_view_model,
    domain_bundle_for_cache,
    fetch_evidence_packet_safe,
)
from analyzer.use_cases.morning_brief_helpers import (
    MorningBriefScenario,
    built_at_label,
    detect_scenario,
    evaluate_stale,
)
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from analyzer.use_cases.snapshot_cache import snapshot_from_cache
from analyzer.watchlist_pins import PinnedPlan, load_pinned_plans
from ui.broker.state import BrokerSnapshot, load_broker_snapshot

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class MorningBriefDomain:
    """Loaded domain inputs — cached between requests."""

    market: str
    context: ContextSnapshot
    decision: DecisionArtifact | None
    decision_source: str
    broker: BrokerSnapshot
    mis: MisTradeAdvisory
    os_report: InvestmentOS
    pins: list[PinnedPlan]
    prefs: IntradayPrefs
    built_at: str
    scenario: MorningBriefScenario
    stale: bool
    stale_reason: str
    context_from_cache: bool
    context_cache_age: float | None
    data_error: str


def pick_decision(
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
) -> tuple[DecisionArtifact | None, str]:
    """Prefer starred equity decision; fall back to equity session decision only."""

    def _is_equity(artifact: object | None) -> bool:
        if artifact is None:
            return False
        return str(getattr(artifact, "subject_type", "equity") or "equity").lower() == "equity"

    os_art = getattr(os_report, "decision_artifact", None)
    mis_art = getattr(mis, "decision_artifact", None)
    if os_art and os_report.starred_symbol:
        return os_art, "equity"
    if mis_art and _is_equity(mis_art):
        return mis_art, "session"
    if os_art and _is_equity(os_art):
        return os_art, "equity"
    return None, "none"


def _empty_context() -> ContextSnapshot:
    return ContextSnapshot(
        timestamp=datetime.now(IST).isoformat(),
        market_regime="Unknown",
        market_phase="unknown",
        market_breadth="unknown",
        volatility_state="unknown",
        liquidity_state="unknown",
        market_session={"phase": "unknown", "is_open": False},
        sector_strength={},
        industry_strength={},
        macro_state={},
        global_market_state={},
        risk_mode="NEUTRAL",
        trading_restrictions=(),
        confidence=0.0,
        snapshot_id="",
        context_hash="",
    )


def load_morning_brief_domain(
    *,
    market: str,
    period: str = "1y",
    broker: BrokerSnapshot | None = None,
    deep: bool = False,
    use_cache: bool = True,
) -> MorningBriefDomain:
    """Load domain layer — context, decision attach path, broker."""
    broker_snap = broker if broker is not None else load_broker_snapshot()
    built_at = built_at_label()
    data_error = ""
    context_from_cache = False
    context_cache_age: float | None = None

    try:
        cached_ctx = get_cached(market, include_global=True) if use_cache else None
        context_from_cache = cached_ctx is not None
        if context_from_cache:
            context_cache_age = cache_age_sec(market, include_global=True)
        context = build_context_snapshot(market=market, use_cache=use_cache)
    except Exception as exc:
        context = _empty_context()
        data_error = str(exc)[:200]

    prefs = load_intraday_prefs()
    try:
        mis = build_mis_trade_advisory(market=market)
        os_report = build_investment_os(market, period=period, prefs=prefs, deep=deep)
        pins = load_pinned_plans()
    except Exception as exc:
        if not data_error:
            data_error = str(exc)[:200]
        mis = MisTradeAdvisory(
            verdict="NO_TRADE",
            emoji="⏸",
            headline="Unavailable",
            summary="Data temporarily unavailable.",
            score=0,
        )
        os_report = InvestmentOS()
        pins = []

    decision, decision_source = pick_decision(mis, os_report)
    scenario = detect_scenario(
        broker=broker_snap,
        snapshot=context,
        decision=decision,
        data_error=data_error,
    )
    stale, stale_reason = evaluate_stale(
        decision=decision,
        snapshot=context,
        broker=broker_snap,
        context_from_cache=context_from_cache,
        context_cache_age=context_cache_age,
    )

    return MorningBriefDomain(
        market=market,
        context=context,
        decision=decision,
        decision_source=decision_source,
        broker=broker_snap,
        mis=mis,
        os_report=os_report,
        pins=pins,
        prefs=prefs,
        built_at=built_at,
        scenario=scenario,
        stale=stale,
        stale_reason=stale_reason,
        context_from_cache=context_from_cache,
        context_cache_age=context_cache_age,
        data_error=data_error,
    )


def view_model_from_domain(domain: MorningBriefDomain, *, broker: BrokerSnapshot | None = None) -> MorningBriefViewModel:
    """Assemble authoritative view model — fetches Evidence in use case."""
    broker_snap = broker if broker is not None else domain.broker
    stale = domain.stale
    stale_reason = domain.stale_reason
    scenario = domain.scenario

    if broker_snap.to_dict() != domain.broker.to_dict():
        stale, stale_reason = evaluate_stale(
            decision=domain.decision,
            snapshot=domain.context,
            broker=broker_snap,
            context_from_cache=domain.context_from_cache,
            context_cache_age=domain.context_cache_age,
        )
        scenario = detect_scenario(
            broker=broker_snap,
            snapshot=domain.context,
            decision=domain.decision,
            data_error=domain.data_error,
        )

    packet = fetch_evidence_packet_safe(domain.decision.evidence_packet_id if domain.decision else "")

    return assemble_morning_brief_view_model(
        market=domain.market,
        context=domain.context,
        decision=domain.decision,
        decision_source=domain.decision_source,
        broker=broker_snap,
        mis=domain.mis,
        os_report=domain.os_report,
        pins=domain.pins,
        prefs=domain.prefs,
        built_at=domain.built_at,
        scenario=scenario,
        stale=stale,
        stale_reason=stale_reason,
        context_from_cache=domain.context_from_cache,
        context_cache_age=domain.context_cache_age,
        data_error=domain.data_error,
        evidence_packet=packet,
    )


def build_morning_brief(
    *,
    market: str,
    period: str = "1y",
    broker: BrokerSnapshot | None = None,
    deep: bool = False,
    use_cache: bool = True,
) -> MorningBriefViewModel:
    """Public API — returns MorningBriefViewModel."""
    domain = load_morning_brief_domain(
        market=market,
        period=period,
        broker=broker,
        deep=deep,
        use_cache=use_cache,
    )
    return view_model_from_domain(domain, broker=broker or domain.broker)


def domain_to_cache_bundle(domain: MorningBriefDomain) -> dict[str, Any]:
    return domain_bundle_for_cache(
        market=domain.market,
        context=domain.context,
        decision=domain.decision,
        decision_source=domain.decision_source,
        broker=domain.broker,
        mis=domain.mis,
        os_report=domain.os_report,
        pins=domain.pins,
        prefs=domain.prefs,
        built_at=domain.built_at,
        scenario=domain.scenario,
        stale=domain.stale,
        stale_reason=domain.stale_reason,
        context_from_cache=domain.context_from_cache,
        context_cache_age=domain.context_cache_age,
        data_error=domain.data_error,
    )


def domain_from_cache_bundle(bundle: dict[str, Any], *, broker: BrokerSnapshot | None = None) -> MorningBriefDomain:
    broker_snap = broker if broker is not None else load_broker_snapshot()
    snapshot = snapshot_from_cache(bundle["snapshot"])
    decision, decision_source = pick_decision(bundle["mis"], bundle["os_report"])
    scenario = MorningBriefScenario(bundle.get("scenario", MorningBriefScenario.NORMAL.value))
    stale = bool(bundle.get("stale", False))
    stale_reason = str(bundle.get("stale_reason", ""))

    if broker_snap.to_dict() != bundle.get("_broker_at_build"):
        stale, stale_reason = evaluate_stale(
            decision=decision,
            snapshot=snapshot,
            broker=broker_snap,
            context_from_cache=bool(bundle.get("context_from_cache")),
            context_cache_age=bundle.get("context_cache_age"),
        )
        scenario = detect_scenario(
            broker=broker_snap,
            snapshot=snapshot,
            decision=decision,
            data_error=str(bundle.get("data_error", "")),
        )

    return MorningBriefDomain(
        market=str(bundle.get("market", "NSE")),
        context=snapshot,
        decision=decision,
        decision_source=decision_source or str(bundle.get("decision_source", "none")),
        broker=broker_snap,
        mis=bundle["mis"],
        os_report=bundle["os_report"],
        pins=bundle.get("pins") or [],
        prefs=bundle["prefs"],
        built_at=str(bundle.get("built_at", built_at_label())),
        scenario=scenario,
        stale=stale,
        stale_reason=stale_reason,
        context_from_cache=bool(bundle.get("context_from_cache")),
        context_cache_age=bundle.get("context_cache_age"),
        data_error=str(bundle.get("data_error", "")),
    )


# Legacy aliases
brief_result_to_dict = domain_to_cache_bundle
brief_result_from_bundle = domain_from_cache_bundle

MorningBriefResult = MorningBriefViewModel
