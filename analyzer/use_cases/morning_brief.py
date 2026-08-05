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
from analyzer.use_cases.decision_context_bundle import DecisionContextBundle
from analyzer.use_cases.morning_brief_helpers import (
    MorningBriefScenario,
    built_at_label,
    detect_scenario,
    evaluate_stale,
)
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from analyzer.use_cases.morning_brief_assembly import fetch_evidence_packet_safe  # re-export for tests
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


def view_model_from_domain(
    domain: MorningBriefDomain,
    *,
    broker: BrokerSnapshot | None = None,
    record_snapshot: bool = False,
) -> MorningBriefViewModel:
    """Assemble view model from frozen context — live broker overrides rejected (E0.6)."""
    _ = broker  # retained for API compat; frozen domain.broker is authoritative
    return DecisionContextBundle.freeze(domain).assemble_view_model(record_snapshot=record_snapshot)


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
    return view_model_from_domain(domain, broker=broker or domain.broker, record_snapshot=True)


def domain_to_cache_bundle(domain: MorningBriefDomain) -> dict[str, Any]:
    return DecisionContextBundle.freeze(domain).to_cache_dict()


def domain_from_cache_bundle(bundle: dict[str, Any], *, broker: BrokerSnapshot | None = None) -> MorningBriefDomain:
    _ = broker  # retained for API compat; frozen bundle broker is authoritative (E0.6)
    return DecisionContextBundle.from_cache_dict(bundle).to_domain()  # type: ignore[return-value]


# Legacy aliases
brief_result_to_dict = domain_to_cache_bundle
brief_result_from_bundle = domain_from_cache_bundle

MorningBriefResult = MorningBriefViewModel
