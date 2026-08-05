"""Immutable Decision Context Bundle — APEX-013 E0.6 context determinism."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_assembly import (
    assemble_morning_brief_view_model,
    fetch_evidence_packet_safe,
)
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from analyzer.use_cases.snapshot_cache import snapshot_from_cache, snapshot_to_cache
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot

CONTEXT_BUNDLE_VERSION = "1"


@dataclass(frozen=True)
class DecisionContextBundle:
    """Frozen decision context — single source of truth for brief + ledger + UI."""

    market: str
    context: ContextSnapshot
    decision: DecisionArtifact | None
    decision_source: str
    broker: BrokerSnapshot
    mis: MisTradeAdvisory
    os_report: InvestmentOS
    pins: tuple[PinnedPlan, ...]
    prefs: IntradayPrefs
    built_at: str
    scenario: MorningBriefScenario
    stale: bool
    stale_reason: str
    context_from_cache: bool
    context_cache_age: float | None
    data_error: str

    @classmethod
    def freeze(cls, domain: object) -> DecisionContextBundle:
        """Capture domain inputs at production — no live overrides downstream."""
        from analyzer.use_cases.morning_brief import MorningBriefDomain

        if not isinstance(domain, MorningBriefDomain):
            raise TypeError(f"Expected MorningBriefDomain, got {type(domain)!r}")
        return cls(
            market=domain.market,
            context=domain.context,
            decision=domain.decision,
            decision_source=domain.decision_source,
            broker=domain.broker,
            mis=domain.mis,
            os_report=domain.os_report,
            pins=tuple(domain.pins),
            prefs=domain.prefs,
            built_at=domain.built_at,
            scenario=domain.scenario,
            stale=domain.stale,
            stale_reason=domain.stale_reason,
            context_from_cache=domain.context_from_cache,
            context_cache_age=domain.context_cache_age,
            data_error=domain.data_error,
        )

    def to_domain(self) -> object:
        from analyzer.use_cases.morning_brief import MorningBriefDomain

        return MorningBriefDomain(
            market=self.market,
            context=self.context,
            decision=self.decision,
            decision_source=self.decision_source,
            broker=self.broker,
            mis=self.mis,
            os_report=self.os_report,
            pins=list(self.pins),
            prefs=self.prefs,
            built_at=self.built_at,
            scenario=self.scenario,
            stale=self.stale,
            stale_reason=self.stale_reason,
            context_from_cache=self.context_from_cache,
            context_cache_age=self.context_cache_age,
            data_error=self.data_error,
        )

    def assemble_view_model(self, *, record_snapshot: bool = False) -> MorningBriefViewModel:
        """Single assembly path — frozen context only, no live broker recompute."""
        packet = fetch_evidence_packet_safe(
            self.decision.evidence_packet_id if self.decision else ""
        )
        brief = assemble_morning_brief_view_model(
            market=self.market,
            context=self.context,
            decision=self.decision,
            decision_source=self.decision_source,
            broker=self.broker,
            mis=self.mis,
            os_report=self.os_report,
            pins=list(self.pins),
            prefs=self.prefs,
            built_at=self.built_at,
            scenario=self.scenario,
            stale=self.stale,
            stale_reason=self.stale_reason,
            context_from_cache=self.context_from_cache,
            context_cache_age=self.context_cache_age,
            data_error=self.data_error,
            evidence_packet=packet,
        )
        if record_snapshot:
            from analyzer.intelligence_lab.snapshot_store import persist_decision_snapshot_safe

            persist_decision_snapshot_safe(brief, domain=self.to_domain(), broker=self.broker)
        return brief

    def to_cache_dict(self) -> dict[str, Any]:
        return {
            "_context_bundle_version": CONTEXT_BUNDLE_VERSION,
            "snapshot": snapshot_to_cache(self.context),
            "broker": self.broker.to_dict(),
            "_broker_at_build": self.broker.to_dict(),
            "decision": self.decision,
            "mis": self.mis,
            "os_report": self.os_report,
            "pins": list(self.pins),
            "prefs": self.prefs,
            "built_at": self.built_at,
            "market": self.market,
            "decision_source": self.decision_source,
            "scenario": self.scenario.value,
            "stale": self.stale,
            "stale_reason": self.stale_reason,
            "context_from_cache": self.context_from_cache,
            "context_cache_age": self.context_cache_age,
            "data_error": self.data_error,
        }

    @classmethod
    def from_cache_dict(cls, data: dict[str, Any]) -> DecisionContextBundle:
        """Rehydrate frozen context — never applies live broker overrides."""
        from analyzer.use_cases.morning_brief import pick_decision

        broker_raw = data.get("broker") or data.get("_broker_at_build") or {}
        broker = BrokerSnapshot.from_dict(broker_raw)
        snapshot = snapshot_from_cache(data["snapshot"])
        frozen_decision = data.get("decision")
        if frozen_decision is not None:
            decision = frozen_decision
            decision_source = str(data.get("decision_source", "none"))
        else:
            decision, decision_source = pick_decision(data["mis"], data["os_report"])
        return cls(
            market=str(data.get("market", "NSE")),
            context=snapshot,
            decision=decision,
            decision_source=decision_source or str(data.get("decision_source", "none")),
            broker=broker,
            mis=data["mis"],
            os_report=data["os_report"],
            pins=tuple(data.get("pins") or []),
            prefs=data["prefs"],
            built_at=str(data.get("built_at", "")),
            scenario=MorningBriefScenario(data.get("scenario", MorningBriefScenario.NORMAL.value)),
            stale=bool(data.get("stale", False)),
            stale_reason=str(data.get("stale_reason", "")),
            context_from_cache=bool(data.get("context_from_cache")),
            context_cache_age=data.get("context_cache_age"),
            data_error=str(data.get("data_error", "")),
        )


def context_bundle_from_cache(data: dict[str, Any]) -> DecisionContextBundle:
    return DecisionContextBundle.from_cache_dict(data)
