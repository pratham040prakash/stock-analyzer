"""Load MorningBriefViewModel from dashboard cache — UI projection entry point."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.decision_context_bundle import DecisionContextBundle
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.canvas_utils import VerdictCanvasState, _strip_md, _trim_words


@dataclass(frozen=True)
class RecommendationContract:
    """APS-001 / MASTER_PROMPT recommendation sections (projection only)."""

    why: tuple[str, ...]
    evidence: tuple[str, ...]
    trade_offs: tuple[str, ...]
    risks: tuple[str, ...]
    what_could_change: tuple[str, ...]
    suggested_next_step: tuple[str, ...]
    help_simple: tuple[str, ...]
    help_business: tuple[str, ...]
    help_professional: tuple[str, ...]


def load_brief_from_cache(
    cached: dict[str, Any],
    *,
    broker: BrokerSnapshot | None = None,
) -> MorningBriefViewModel:
    _ = broker  # UI projection only — frozen context is authoritative (E0.6)
    return DecisionContextBundle.from_cache_dict(cached).assemble_view_model(record_snapshot=False)


def verdict_state_from_brief(brief: MorningBriefViewModel) -> VerdictCanvasState:
    d = brief.decision
    return VerdictCanvasState(d.verdict_key, d.verdict_display, d.cta_label, d.cta_action)


def market_is_rest_from_brief(brief: MorningBriefViewModel) -> bool:
    return brief.meta.scenario in ("weekend", "market_closed")


def mentor_line_from_brief(brief: MorningBriefViewModel, *, max_words: int = 18) -> str:
    text = brief.decision.reason or brief.trust.why_this_is_recommended
    return _trim_words(text, max_words=max_words)


def why_primary_from_brief(brief: MorningBriefViewModel) -> list[str]:
    if brief.evidence.key_reasons:
        return list(brief.evidence.key_reasons)[:6]
    reason = _strip_md(brief.decision.reason)
    if reason:
        return [reason]
    return ["Conditions are mixed — patience beats forcing a trade."]


def why_advanced_from_brief(
    brief: MorningBriefViewModel,
    *,
    mis: MisTradeAdvisory | None = None,
    snapshot: ContextSnapshot | None = None,
    pins: list[PinnedPlan] | None = None,
) -> list[str]:
    bullets: list[str] = []
    for line in brief.evidence.supporting_signals:
        text = f"{line.label}: {line.value}"
        if text not in bullets:
            bullets.append(text)
    for conflict in brief.evidence.conflicting_signals:
        text = f"Conflict: {conflict.label} — {conflict.value}"
        if text not in bullets:
            bullets.append(text)
    if brief.evidence.gap_note:
        text = _strip_md(brief.evidence.gap_note)
        if text and text not in bullets:
            bullets.append(text)
    if mis:
        for pillar in (getattr(mis, "synthesis_pillars", None) or [])[:5]:
            text = _strip_md(str(pillar))
            if text and text not in bullets:
                bullets.append(text)
        for flag in (mis.flags or ())[:3]:
            text = _strip_md(flag)
            if text not in bullets:
                bullets.append(text)
    if snapshot:
        for restriction in snapshot.trading_restrictions[:2]:
            text = _strip_md(restriction)
            if text not in bullets:
                bullets.append(text)
    if pins:
        pin = pins[0]
        sym = pin.symbol.upper().replace(".NS", "")
        bullets.append(f"Watch {sym} near ₹{pin.entry:,.0f} with stop ₹{pin.stop_loss:,.0f}.")
    return bullets


def why_bullets_from_brief(
    brief: MorningBriefViewModel,
    *,
    mis: MisTradeAdvisory | None = None,
    snapshot: ContextSnapshot | None = None,
    pins: list[PinnedPlan] | None = None,
) -> list[str]:
    return why_primary_from_brief(brief) + why_advanced_from_brief(
        brief, mis=mis, snapshot=snapshot, pins=pins
    )


def evidence_teaser_lines(brief: MorningBriefViewModel, *, limit: int = 2) -> list[str]:
    lines: list[str] = []
    for item in brief.evidence.supporting_signals[:limit]:
        text = _strip_md(f"{item.label}: {item.value}")
        if text and text not in lines:
            lines.append(text)
    return lines


def answer_key_from_brief(brief: MorningBriefViewModel) -> tuple[str, str]:
    mapping = {
        "trade": ("buy", "Buy"),
        "wait": ("wait", "Wait"),
        "pause": ("pass", "Pass"),
        "connect": ("pass", "Pass"),
        "rest": ("pass", "Pass"),
        "prepare": ("wait", "Wait"),
    }
    return mapping.get(brief.decision.verdict_key, ("wait", "Wait"))


def recommendation_contract_from_brief(
    brief: MorningBriefViewModel,
    *,
    decision: DecisionArtifact | None = None,
    mis: MisTradeAdvisory | None = None,
    snapshot: ContextSnapshot | None = None,
    pins: list[PinnedPlan] | None = None,
) -> RecommendationContract:
    """Project MorningBriefViewModel → fixed recommendation contract order."""
    why = tuple(why_primary_from_brief(brief))
    evidence = tuple(why_advanced_from_brief(brief, mis=mis, snapshot=snapshot, pins=pins))

    trade_offs: list[str] = []
    for conflict in brief.evidence.conflicting_signals:
        text = _strip_md(f"{conflict.label}: {conflict.value}")
        if text and text not in trade_offs:
            trade_offs.append(text)
    if decision and decision.explainability and decision.explainability.why_not:
        text = _strip_md(decision.explainability.why_not)
        if text and text not in trade_offs:
            trade_offs.append(text)

    risks = tuple(_strip_md(w) for w in brief.risk.warnings if _strip_md(w))

    what_could_change: list[str] = []
    if decision:
        for item in decision.invalidation_conditions[:4]:
            text = _strip_md(str(item or ""))
            if text and text not in what_could_change:
                what_could_change.append(text)
        for alt in decision.alternative_actions[:2]:
            text = _strip_md(str(alt or ""))
            if text and text not in what_could_change:
                what_could_change.append(text)
    if brief.evidence.gap_note:
        text = _strip_md(brief.evidence.gap_note)
        if text and text not in what_could_change:
            what_could_change.append(text)

    suggested: list[str] = []
    if brief.decision.cta_label:
        suggested.append(brief.decision.cta_label)
    if decision:
        for rec in (decision.capital_recommendation, decision.execution_recommendation):
            text = _strip_md(str(rec or ""))
            if text and text not in suggested:
                suggested.append(text)

    simple: list[str] = []
    if why:
        simple.append(why[0])
    elif brief.decision.reason:
        simple.append(_trim_words(brief.decision.reason, max_words=12))

    business: list[str] = []
    if brief.decision.reason:
        business.append(_trim_words(brief.decision.reason, max_words=18))
    business.extend(list(why)[1:3])
    business.extend(list(evidence)[:2])

    professional = list(why) + list(evidence)
    if trade_offs:
        professional.extend(trade_offs)
    if risks:
        professional.extend(list(risks))
    if what_could_change:
        professional.extend(what_could_change)

    return RecommendationContract(
        why=why,
        evidence=evidence,
        trade_offs=tuple(trade_offs),
        risks=risks,
        what_could_change=tuple(what_could_change),
        suggested_next_step=tuple(suggested),
        help_simple=tuple(simple[:2]),
        help_business=tuple(business[:5]),
        help_professional=tuple(professional[:12]),
    )
