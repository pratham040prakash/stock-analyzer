"""Decision Card — hero projection of MorningBriefViewModel (ETS-003b v0.2)."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.use_cases.morning_brief_models import MorningBriefViewModel


@dataclass(frozen=True)
class BestOpportunityView:
    symbol: str
    setup: str
    visible: bool


@dataclass(frozen=True)
class DecisionCardViewModel:
    """Hero slice — derived only from MorningBriefViewModel."""

    verdict_word: str
    verdict_key: str
    reason: str
    confidence_level: int
    confidence_band: str
    last_updated: str
    valid_until: str
    portfolio_ready: bool
    portfolio_status: str
    sync_label: str
    sync_state: str
    best_opportunity: BestOpportunityView | None
    risk_level: str
    coach_message: str
    cta_label: str
    cta_action: str
    scenario: str
    stale: bool
    stale_label: str
    trust_summary: str
    evidence_teaser: tuple[str, ...]
    broker_connected: bool
    cash_available_inr: float | None
    last_sync: str
    decision_verdict: str | None
    failure_message: str | None


def _coach_message(brief: MorningBriefViewModel) -> str:
    key = brief.decision.verdict_key
    if brief.meta.scenario == "weekend":
        return "Patience is part of your edge."
    if brief.meta.scenario == "market_closed":
        return "Protecting capital is also a winning decision."
    if key == "wait":
        return "The best trade today may be the one you don't make."
    if key == "trade":
        return "Size matters more than speed — review the plan before Kite."
    if key == "pause":
        return "Discipline compounds. So does inconsistency."
    return ""


def _sync_label(state: str) -> str:
    return {
        "synced": "Synced",
        "stale": "Stale",
        "offline": "Offline",
        "not_configured": "Offline",
    }.get(state, "Offline")


def project_decision_card(brief: MorningBriefViewModel) -> DecisionCardViewModel:
    """Project root view model → hero card. No business logic."""
    d = brief.decision
    t = brief.trust
    p = brief.portfolio
    o = brief.opportunity
    sync_state = t.data_freshness.broker_sync_state
    if sync_state == "synced":
        sync_css = "ok"
    elif sync_state == "stale":
        sync_css = "warn"
    else:
        sync_css = "off"

    best: BestOpportunityView | None = None
    if o.visible:
        best = BestOpportunityView(symbol=o.symbol, setup=o.setup, visible=True)

    return DecisionCardViewModel(
        verdict_word=d.verdict_display,
        verdict_key=d.verdict_key,
        reason=d.reason,
        confidence_level=d.confidence_level,
        confidence_band=d.confidence_band,
        last_updated=d.last_updated,
        valid_until=d.valid_until,
        portfolio_ready=p.ready,
        portfolio_status=p.summary,
        sync_label=_sync_label(sync_state),
        sync_state=sync_css,
        best_opportunity=best,
        risk_level=brief.risk.level,
        coach_message=_coach_message(brief),
        cta_label=d.cta_label,
        cta_action=d.cta_action,
        scenario=brief.meta.scenario,
        stale=t.stale,
        stale_label=t.stale_label,
        trust_summary=t.why_this_is_recommended,
        evidence_teaser=brief.evidence.key_reasons[:1],
        broker_connected=t.portfolio_sync_status.personalized,
        cash_available_inr=p.cash_available_inr,
        last_sync=t.data_freshness.broker_last_sync,
        decision_verdict=d.verdict,
        failure_message=brief.failure_message,
    )


def canvas_state_from_view_model(vm: DecisionCardViewModel) -> tuple[str, str, str, str]:
    return vm.verdict_key, vm.verdict_word, vm.cta_label, vm.cta_action


# Legacy alias
build_decision_card_view = project_decision_card
