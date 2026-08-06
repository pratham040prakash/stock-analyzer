"""Load MorningBriefViewModel from dashboard cache — UI projection entry point."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.decision_context_bundle import DecisionContextBundle
from analyzer.use_cases.morning_brief_helpers import parse_decision_time
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.canvas_utils import VerdictCanvasState, _strip_md, _trim_words

IST = ZoneInfo("Asia/Kolkata")


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


@dataclass(frozen=True)
class InvestmentThesisContract:
    """APS-004 investment thesis sections (projection only)."""

    thesis_statement: str
    status_key: str
    status_label: str
    strengths: tuple[str, ...]
    concerns: tuple[str, ...]
    watch_closely: tuple[str, ...]
    sell_conditions: tuple[str, ...]
    level3_evidence: tuple[str, ...]


@dataclass(frozen=True)
class BusinessHealthContract:
    """APS-005 business health sections (projection only)."""

    summary: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    health_indicators: tuple[tuple[str, str], ...]
    monitor_next: tuple[str, ...]
    level3_evidence: tuple[str, ...]


@dataclass(frozen=True)
class RiskMonitorContract:
    """APS-006 risk monitor sections (projection only)."""

    summary: str
    key_business_risks: tuple[str, ...]
    watch_carefully: tuple[str, ...]
    thesis_breakers: tuple[str, ...]
    supporting_evidence: tuple[str, ...]


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
    key, label = recommendation_action_from_brief(brief)
    if key == "hold":
        return "pass", "Pass"
    return key, label


def recommendation_action_from_brief(
    brief: MorningBriefViewModel,
    *,
    decision: DecisionArtifact | None = None,
) -> tuple[str, str]:
    """Shared presentation mapping → buy / hold / wait / reduce / sell."""
    if decision is not None:
        verdict = decision.verdict
        if verdict == DecisionVerdict.REDUCE:
            return "reduce", "Reduce"
        if verdict == DecisionVerdict.ACT:
            return "buy", "Buy"
        if verdict in (DecisionVerdict.WAIT, DecisionVerdict.PASS):
            return "wait", "Wait"
        if verdict == DecisionVerdict.DEFENSIVE:
            return "hold", "Hold"

    display = (brief.decision.verdict_display or "").strip().lower()
    for token, key, label in (
        ("strong sell", "sell", "Sell"),
        ("sell", "sell", "Sell"),
        ("reduce", "reduce", "Reduce"),
        ("strong buy", "buy", "Buy"),
        ("buy", "buy", "Buy"),
        ("accumulate", "buy", "Buy"),
        ("hold", "hold", "Hold"),
        ("wait", "wait", "Wait"),
        ("pass", "wait", "Wait"),
    ):
        if token in display:
            return key, label

    key_map = {
        "trade": ("buy", "Buy"),
        "wait": ("wait", "Wait"),
        "pause": ("hold", "Hold"),
        "connect": ("wait", "Wait"),
        "rest": ("hold", "Hold"),
        "prepare": ("wait", "Wait"),
    }
    return key_map.get(brief.decision.verdict_key, ("wait", "Wait"))


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


def _dedupe_thesis_lines(lines: list[str], *, limit: int = 6) -> tuple[str, ...]:
    out: list[str] = []
    for raw in lines:
        text = _strip_md(raw)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return tuple(out)


def _thesis_statement_from_brief(
    brief: MorningBriefViewModel,
    contract: RecommendationContract,
) -> str:
    if brief.evidence.key_reasons:
        return _strip_md(brief.evidence.key_reasons[0])
    if contract.help_business:
        return _strip_md(contract.help_business[0])
    if contract.why:
        return _strip_md(contract.why[0])
    trust = _strip_md(brief.trust.why_this_is_recommended)
    for prefix in ("OPINION:", "FACT:", "ASSUMPTION:", "ESTIMATE:"):
        if trust.upper().startswith(prefix):
            return trust[len(prefix) :].strip()
    return trust


def _concern_lines_from_contract(contract: RecommendationContract) -> tuple[str, ...]:
    return _dedupe_thesis_lines(list(contract.trade_offs) + list(contract.risks))


def _level3_evidence_from_contract(contract: RecommendationContract) -> tuple[str, ...]:
    level3 = contract.help_professional or tuple(
        dict.fromkeys(contract.evidence + contract.trade_offs + contract.risks)
    )[:12]
    return tuple(level3) if level3 else tuple()


def _monitor_lines_from_brief(
    brief: MorningBriefViewModel,
    contract: RecommendationContract,
    *,
    include_suggested_steps: bool = False,
    supporting_limit: int = 3,
    conflicting_limit: int = 0,
) -> tuple[str, ...]:
    monitor: list[str] = []
    if include_suggested_steps:
        monitor.extend(contract.suggested_next_step)
    monitor.extend(brief.trust.gaps)
    for item in brief.evidence.supporting_signals[:supporting_limit]:
        monitor.append(item.label)
    for item in brief.evidence.conflicting_signals[:conflicting_limit]:
        monitor.append(item.label)
    return _dedupe_thesis_lines(monitor, limit=5)


def investment_thesis_contract_from_brief(
    brief: MorningBriefViewModel,
    contract: RecommendationContract,
    *,
    mis: MisTradeAdvisory | None = None,
) -> InvestmentThesisContract:
    """Project MorningBriefViewModel + RecommendationContract → APS-004 thesis sections."""
    strengths: list[str] = []
    for item in brief.evidence.supporting_signals:
        strengths.append(f"{item.label}: {item.value}")
    if mis:
        strengths.extend(mis.positives[:4])

    concerns = _concern_lines_from_contract(contract)
    watch = _monitor_lines_from_brief(
        brief,
        contract,
        include_suggested_steps=True,
        supporting_limit=3,
    )

    sell_conditions = _dedupe_thesis_lines(list(contract.what_could_change), limit=5)
    level3 = _level3_evidence_from_contract(contract)

    return InvestmentThesisContract(
        thesis_statement=_thesis_statement_from_brief(brief, contract),
        status_key="",
        status_label="",
        strengths=_dedupe_thesis_lines(strengths),
        concerns=concerns,
        watch_closely=watch,
        sell_conditions=sell_conditions,
        level3_evidence=level3,
    )


def _business_health_summary(
    brief: MorningBriefViewModel,
    contract: RecommendationContract,
) -> str:
    if len(contract.help_business) > 1:
        return _strip_md(contract.help_business[1])
    if contract.help_business:
        return _strip_md(contract.help_business[0])
    if brief.portfolio.summary and brief.portfolio.ready:
        return _strip_md(brief.portfolio.summary)
    if contract.why:
        return _strip_md(contract.why[0])
    return ""


def _health_indicators_from_brief(
    brief: MorningBriefViewModel,
) -> tuple[tuple[str, str], ...]:
    indicators: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in brief.evidence.supporting_signals + brief.evidence.conflicting_signals:
        label = _strip_md(f"{item.label}: {item.value}")
        if not label or label in seen:
            continue
        seen.add(label)
        key = item.label.lower().replace(" ", "-").replace("/", "-")[:32] or "indicator"
        indicators.append((key, label))
        if len(indicators) >= 6:
            break
    return tuple(indicators)


def business_health_contract_from_brief(
    brief: MorningBriefViewModel,
    contract: RecommendationContract,
    thesis: InvestmentThesisContract,
) -> BusinessHealthContract:
    """Project MorningBriefViewModel + contracts → APS-005 business health sections."""
    return BusinessHealthContract(
        summary=_business_health_summary(brief, contract),
        strengths=thesis.strengths,
        weaknesses=thesis.concerns,
        health_indicators=_health_indicators_from_brief(brief),
        monitor_next=_monitor_lines_from_brief(
            brief,
            contract,
            supporting_limit=4,
            conflicting_limit=2,
        ),
        level3_evidence=thesis.level3_evidence,
    )


def _risk_summary_from_brief(
    brief: MorningBriefViewModel,
    thesis: InvestmentThesisContract,
) -> str:
    if brief.risk.warnings:
        return _strip_md(brief.risk.warnings[0])
    if thesis.concerns:
        return _strip_md(thesis.concerns[0])
    if brief.evidence.gap_note:
        return _strip_md(brief.evidence.gap_note)
    return ""


def risk_monitor_contract_from_brief(
    brief: MorningBriefViewModel,
    thesis: InvestmentThesisContract,
    health: BusinessHealthContract,
) -> RiskMonitorContract:
    """Project existing contracts → APS-006 risk monitor sections."""
    return RiskMonitorContract(
        summary=_risk_summary_from_brief(brief, thesis),
        key_business_risks=thesis.concerns,
        watch_carefully=health.monitor_next,
        thesis_breakers=thesis.sell_conditions,
        supporting_evidence=thesis.level3_evidence,
    )


def human_review_freshness_label(
    *,
    built_at: str,
    last_updated: str,
    stale: bool,
    stale_label: str,
    refreshing: bool,
    offline: bool = False,
) -> str:
    """Human-friendly review timestamp for hero surfaces (presentation only)."""
    if refreshing:
        return "Reviewed just now · updating"
    if offline:
        return "Reviewed offline · reconnect to refresh"
    if stale and stale_label:
        return f"Reviewed · {stale_label}"

    now = datetime.now(IST)
    for raw in (last_updated,):
        if not raw:
            continue
        dt = parse_decision_time(raw)
        if dt is None:
            continue
        delta = now - dt
        if delta < timedelta(minutes=1):
            return "Reviewed just now"
        mins = int(delta.total_seconds() // 60)
        if mins < 60:
            suffix = "s" if mins != 1 else ""
            return f"Reviewed {mins} minute{suffix} ago"
        if dt.date() == now.date():
            return f"Reviewed at {dt.strftime('%H:%M IST')}"
        if (now.date() - dt.date()).days == 1:
            return "Reviewed yesterday"
        return f"Reviewed {dt.strftime('%d %b')}"

    if built_at:
        return f"Reviewed at {built_at}"
    return "Review freshness updating"
