"""Shared helpers for Morning Brief use case and assembly."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from ui.broker.state import BrokerSnapshot

IST = ZoneInfo("Asia/Kolkata")

STALE_DECISION_MINUTES_OPEN = 15
STALE_CONTEXT_SECONDS_OPEN = 60


class MorningBriefScenario(str, Enum):
    NORMAL = "normal"
    NO_BROKER = "no_broker"
    BROKER_DISCONNECTED = "broker_disconnected"
    WEEKEND = "weekend"
    MARKET_CLOSED = "market_closed"
    DECISION_UNAVAILABLE = "decision_unavailable"
    DATA_UNAVAILABLE = "data_unavailable"


def built_at_label() -> str:
    return datetime.now(IST).strftime("%H:%M IST")


def session_phase(snapshot: ContextSnapshot) -> str:
    session = dict(snapshot.market_session or {})
    return str(session.get("phase", "") or snapshot.market_phase or "")


def market_is_rest(snapshot: ContextSnapshot) -> bool:
    phase = session_phase(snapshot)
    if snapshot.risk_mode == "CLOSED":
        return True
    return phase in ("weekend", "holiday", "after_hours", "closed")


def is_weekend(snapshot: ContextSnapshot) -> bool:
    return session_phase(snapshot) == "weekend"


def parse_decision_time(raw: str) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(text.replace("+05:30", "+0530"), fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=IST)
            return dt.astimezone(IST)
        except ValueError:
            continue
    return None


def evaluate_stale(
    *,
    decision: DecisionArtifact | None,
    snapshot: ContextSnapshot,
    broker: BrokerSnapshot,
    context_from_cache: bool,
    context_cache_age: float | None,
) -> tuple[bool, str]:
    reasons: list[str] = []
    now = datetime.now(IST)
    market_open = not market_is_rest(snapshot)

    if decision:
        dt = parse_decision_time(decision.timestamp)
        if dt:
            if dt.date() != now.date():
                reasons.append("Recommendation is from a prior session")
            elif market_open and (now - dt) > timedelta(minutes=STALE_DECISION_MINUTES_OPEN):
                reasons.append("Recommendation may be outdated")
    elif market_open:
        reasons.append("No fresh recommendation yet")

    if context_from_cache and market_open:
        age = context_cache_age if context_cache_age is not None else STALE_CONTEXT_SECONDS_OPEN + 1
        if age > STALE_CONTEXT_SECONDS_OPEN:
            reasons.append("Market context refreshing")

    if broker.connected() and broker.state == "limited":
        reasons.append("Broker data is stale")

    if not reasons:
        return False, ""
    return True, "; ".join(reasons)


def detect_scenario(
    *,
    broker: BrokerSnapshot,
    snapshot: ContextSnapshot,
    decision: DecisionArtifact | None,
    data_error: str,
) -> MorningBriefScenario:
    if data_error:
        return MorningBriefScenario.DATA_UNAVAILABLE
    if broker.state == "not_configured":
        return MorningBriefScenario.NO_BROKER
    if not broker.connected():
        return MorningBriefScenario.BROKER_DISCONNECTED
    if is_weekend(snapshot):
        return MorningBriefScenario.WEEKEND
    if market_is_rest(snapshot):
        return MorningBriefScenario.MARKET_CLOSED
    if decision is None:
        return MorningBriefScenario.DECISION_UNAVAILABLE
    return MorningBriefScenario.NORMAL
