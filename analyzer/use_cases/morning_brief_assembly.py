"""Assemble MorningBriefViewModel sections from domain inputs (ETS-003b v0.2)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict
from analyzer.evidence_engine.models import EvidenceConflict, EvidenceItem, EvidencePacket, EvidenceType
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_helpers import (
    MorningBriefScenario,
    STALE_CONTEXT_SECONDS_OPEN,
    STALE_DECISION_MINUTES_OPEN,
    market_is_rest,
    parse_decision_time,
    session_phase,
)
from analyzer.use_cases.morning_brief_models import (
    BriefMetaSection,
    DataFreshnessSection,
    DecisionSection,
    EvidenceLine,
    EvidenceSection,
    MorningBriefViewModel,
    OpportunitySection,
    PortfolioSection,
    PortfolioSyncSection,
    RiskSection,
    TrustSection,
)
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot

IST = __import__("zoneinfo").ZoneInfo("Asia/Kolkata")
_MENTOR_MAX_WORDS = 18
_TYPE_ORDER = {
    EvidenceType.FACT: 0,
    EvidenceType.ESTIMATE: 1,
    EvidenceType.ASSUMPTION: 2,
    EvidenceType.OPINION: 3,
    EvidenceType.GAP: 4,
}


def _strip_md(text: str) -> str:
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", str(text or ""))
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    return cleaned.strip()


def _trim_words(text: str, *, max_words: int = _MENTOR_MAX_WORDS) -> str:
    words = _strip_md(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    clipped = " ".join(words[:max_words]).rstrip(".,;:")
    return f"{clipped}…"


def _decision_reason(decision: DecisionArtifact | None) -> str:
    if not decision:
        return ""
    explain = decision.explainability
    if explain and explain.why:
        return str(explain.why).strip()
    return str(decision.reason or "").strip()


def _conf_numeric(decision: DecisionArtifact | None, snapshot: ContextSnapshot) -> int:
    if decision:
        raw = float(decision.confidence)
        return int(round(raw * 100)) if raw <= 1.0 else int(round(raw))
    raw = float(snapshot.confidence or 0.0)
    return int(round(raw * 100)) if raw <= 1.0 else int(round(raw))


def _confidence_band(decision: DecisionArtifact | None) -> str:
    if not decision:
        return "unknown"
    overall = float(getattr(decision.uncertainty, "overall", 0) or 0)
    if overall <= 30:
        return "high"
    if overall <= 60:
        return "medium"
    return "low"


def _valid_until(decision: DecisionArtifact | None, snapshot: ContextSnapshot) -> str:
    now = datetime.now(IST)
    if market_is_rest(snapshot):
        end = now.replace(hour=23, minute=59, second=0, microsecond=0)
        return end.isoformat()
    if decision:
        dt = parse_decision_time(decision.timestamp)
        if dt:
            return (dt + timedelta(minutes=STALE_DECISION_MINUTES_OPEN)).isoformat()
    return (now + timedelta(minutes=STALE_DECISION_MINUTES_OPEN)).isoformat()


def _decision_age_min(decision: DecisionArtifact | None) -> float | None:
    if not decision:
        return None
    dt = parse_decision_time(decision.timestamp)
    if not dt:
        return None
    return round((datetime.now(IST) - dt).total_seconds() / 60.0, 1)


def _decision_fresh(decision: DecisionArtifact | None, snapshot: ContextSnapshot) -> bool:
    if not decision:
        return False
    now = datetime.now(IST)
    dt = parse_decision_time(decision.timestamp)
    if not dt:
        return False
    if dt.date() != now.date():
        return False
    if not market_is_rest(snapshot):
        return (now - dt) <= timedelta(minutes=STALE_DECISION_MINUTES_OPEN)
    return True


def _broker_sync_state(broker: BrokerSnapshot) -> str:
    if broker.state == "not_configured":
        return "not_configured"
    if not broker.connected():
        return "offline"
    if broker.state == "limited":
        return "stale"
    return "synced"


def _portfolio_scope(broker: BrokerSnapshot) -> tuple[bool, str]:
    if broker.state == "not_configured":
        return False, "market_only"
    if not broker.connected():
        return False, "unavailable"
    if broker.state == "limited":
        return True, "stale"
    return True, "full"


def fetch_evidence_packet_safe(packet_id: str) -> EvidencePacket | None:
    if not packet_id:
        return None
    try:
        from analyzer.evidence_engine import fetch_evidence_packet

        return fetch_evidence_packet(packet_id)
    except Exception:
        return None


def _item_to_line(item: EvidenceItem) -> EvidenceLine:
    etype = item.type.value if hasattr(item.type, "value") else str(item.type)
    conf = item.confidence.value if hasattr(item.confidence, "value") else str(item.confidence)
    source = item.source.value if hasattr(item.source, "value") else str(item.source)
    value = str(item.value if item.value is not None else item.explanation or "")[:100]
    return EvidenceLine(
        label=str(item.label or item.category.value),
        value=value,
        type=etype,
        source=source,
        confidence=conf,
    )


def assemble_evidence_section(
    decision: DecisionArtifact | None,
    packet: EvidencePacket | None,
) -> EvidenceSection:
    key_reasons: list[str] = []
    if decision:
        explain = decision.explainability
        if explain:
            for part in (explain.why, explain.why_now):
                text = _strip_md(str(part or ""))
                if text and text not in key_reasons:
                    key_reasons.append(text)
        reason = _strip_md(decision.reason or "")
        if reason and reason not in key_reasons:
            key_reasons.append(reason)
        for rec in (decision.capital_recommendation, decision.execution_recommendation):
            text = _strip_md(str(rec or ""))
            if text and text not in key_reasons:
                key_reasons.append(text)

    supporting: list[EvidenceLine] = []
    conflicting: list[EvidenceLine] = []
    gap_note = ""
    packet_id = decision.evidence_packet_id if decision else ""
    available = bool(packet and packet.items)

    if packet:
        sorted_items = sorted(
            packet.items,
            key=lambda i: _TYPE_ORDER.get(i.type, 99),
        )
        seen_labels: set[str] = set()
        for item in sorted_items:
            if len(supporting) >= 5:
                break
            line = _item_to_line(item)
            if line.label.lower() in seen_labels:
                continue
            seen_labels.add(line.label.lower())
            supporting.append(line)
        for conflict in packet.conflicts[:3]:
            conflicting.append(_conflict_to_line(conflict, packet))
        if packet.gaps:
            gap_note = f"{len(packet.gaps)} data gap(s) noted"
    elif decision and decision.verdict == DecisionVerdict.ACT:
        gap_note = "Evidence unavailable — wait for proof before acting"
    elif not key_reasons:
        gap_note = "No evidence packet linked"

    return EvidenceSection(
        key_reasons=tuple(key_reasons[:3]),
        supporting_signals=tuple(supporting),
        conflicting_signals=tuple(conflicting),
        evidence_packet_id=packet_id or "",
        evidence_available=available,
        gap_note=gap_note,
    )


def _conflict_to_line(conflict: EvidenceConflict, packet: EvidencePacket) -> EvidenceLine:
    return EvidenceLine(
        label=conflict.category.value,
        value=_strip_md(conflict.description)[:100],
        type="FACT",
        source="internal_model",
        confidence="medium" if conflict.severity == "medium" else conflict.severity,
    )


def _resolve_verdict_display(
    *,
    scenario: MorningBriefScenario,
    broker: BrokerSnapshot,
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    decision: DecisionArtifact | None,
    evidence: EvidenceSection,
) -> tuple[str, str, str, str, str | None]:
    """Return verdict, verdict_display, verdict_key, cta_label, cta_action."""

    def _wait_cta() -> tuple[str, str, str, str]:
        return "WAIT", "Wait", "wait", "You're done for today", "done"

    if scenario == MorningBriefScenario.NO_BROKER:
        return "WAIT", "Connect", "connect", "Connect Zerodha", "connect"
    if scenario == MorningBriefScenario.BROKER_DISCONNECTED:
        return "WAIT", "Connect", "connect", "Connect Zerodha", "connect"
    if scenario == MorningBriefScenario.WEEKEND:
        return "WAIT", "Rest", "rest", "View your week", "week"
    if scenario == MorningBriefScenario.MARKET_CLOSED:
        return "WAIT", "Rest", "rest", "View your week", "week"
    if scenario == MorningBriefScenario.DATA_UNAVAILABLE:
        return "PASS", "Pause", "pause", "Try again", "done"
    if not broker.connected():
        return "WAIT", "Connect", "connect", "Connect Zerodha", "connect"
    if market_is_rest(snapshot):
        return "WAIT", "Rest", "rest", "View your week", "week"
    if mis.loss_streak_days >= 2:
        return "PASS", "Pause", "pause", "You're done for today", "done"
    if decision and decision.verdict in (DecisionVerdict.PASS, DecisionVerdict.DEFENSIVE):
        return decision.verdict.value, "Pause", "pause", "You're done for today", "done"
    if snapshot.risk_mode in ("RISK-OFF", "CLOSED") and len(snapshot.trading_restrictions) >= 2:
        return "WAIT", "Pause", "pause", "You're done for today", "done"

    raw_verdict = decision.verdict.value if decision else "WAIT"

    if decision and decision.verdict == DecisionVerdict.ACT:
        if not evidence.evidence_available:
            return "ACT", "Wait", "wait", "See why we're waiting", "done"
        if _conf_numeric(decision, snapshot) >= 40:
            return "ACT", "Trade", "trade", "See the plan", "plan"

    if decision and decision.verdict == DecisionVerdict.REDUCE:
        return "REDUCE", "Wait", "wait", "You're done for today", "done"

    if scenario == MorningBriefScenario.DECISION_UNAVAILABLE:
        return "WAIT", "Wait", "wait", "See why we're waiting", "done"

    return raw_verdict, *_wait_cta()[1:]


def _mentor_line(
    *,
    scenario: MorningBriefScenario,
    verdict_key: str,
    decision: DecisionArtifact | None,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    snapshot: ContextSnapshot,
    pins: list[PinnedPlan],
    evidence: EvidenceSection,
) -> str:
    if scenario == MorningBriefScenario.NO_BROKER:
        return "Connect Zerodha once — I'll sync positions and tailor today's call."
    if scenario == MorningBriefScenario.BROKER_DISCONNECTED:
        return "Broker offline — reconnect to personalize risk and today's call."
    if scenario == MorningBriefScenario.WEEKEND:
        return "Markets are closed. Rest up; tomorrow's plan builds at open."
    if scenario == MorningBriefScenario.MARKET_CLOSED:
        return "Session closed. Protecting capital today was a valid outcome."
    if scenario == MorningBriefScenario.DATA_UNAVAILABLE:
        return "Some data is unavailable — wait for a fresh read before acting."
    if scenario == MorningBriefScenario.DECISION_UNAVAILABLE:
        return "No setup passes your rules today. The best trade may be the one you don't make."
    if verdict_key == "wait" and evidence.gap_note and "Evidence unavailable" in evidence.gap_note:
        return _trim_words(evidence.gap_note)

    if verdict_key == "connect":
        return "Link Zerodha once — I'll sync positions and tailor today's call."
    if verdict_key == "rest":
        return "Markets are closed. Rest up; tomorrow's plan builds at open."
    if verdict_key == "pause":
        if mis.loss_streak_days >= 2:
            return _trim_words(
                f"{mis.loss_streak_days} rough days in a row — pause today and protect your capital."
            )
        reason = _decision_reason(decision)
        if reason:
            return _trim_words(reason)
        if mis.summary:
            return _trim_words(mis.summary)
        if mis.flags:
            return _trim_words(mis.flags[0])
        return "Too much risk today — pause and protect your capital."
    if verdict_key == "trade":
        sym = (os_report.starred_symbol or "").upper().replace(".NS", "").replace(".BO", "")
        if not sym and pins:
            sym = pins[0].symbol.upper().replace(".NS", "").replace(".BO", "")
        if sym:
            return _trim_words(f"{sym} lines up — one clear plan, sized for your rules.")
        return "One setup is ready — stay within your daily risk limit."
    if verdict_key == "wait":
        if evidence.key_reasons:
            return _trim_words(evidence.key_reasons[0])
        reason = _decision_reason(decision)
        if reason:
            return _trim_words(reason)
        if mis.summary:
            return _trim_words(mis.summary)
        return "Not your moment yet — wait until price confirms the setup."

    reason = _decision_reason(decision)
    if reason:
        return _trim_words(reason)
    return "Not your moment yet — wait until price confirms the setup."


def _why_recommended(
    decision: DecisionArtifact | None,
    evidence: EvidenceSection,
    *,
    verdict_key: str,
) -> str:
    parts: list[str] = []
    if evidence.key_reasons:
        first = evidence.key_reasons[0]
        if not first.upper().startswith(("FACT", "OPINION", "ASSUMPTION", "ESTIMATE")):
            parts.append(f"OPINION: {first}")
        else:
            parts.append(first)
    elif decision:
        reason = _decision_reason(decision)
        if reason:
            parts.append(f"OPINION: {reason}")
    if evidence.conflicting_signals:
        parts.append(f"FACT: {len(evidence.conflicting_signals)} conflicting signal(s) noted.")
    if verdict_key == "wait":
        parts.append("OPINION: Waiting is a valid disciplined choice.")
    text = " ".join(parts[:2])
    return text or "OPINION: Recommendation based on available market and portfolio context."


def _trust_gaps(
    *,
    scenario: MorningBriefScenario,
    decision: DecisionArtifact | None,
    evidence: EvidenceSection,
    broker: BrokerSnapshot,
    personalized: bool,
) -> tuple[str, ...]:
    gaps: list[str] = []
    if scenario == MorningBriefScenario.NO_BROKER:
        gaps.append("Connect Zerodha for personalized risk")
    if scenario == MorningBriefScenario.BROKER_DISCONNECTED:
        gaps.append("Broker offline — reconnect for portfolio-aware call")
    if scenario == MorningBriefScenario.DECISION_UNAVAILABLE:
        gaps.append("No equity recommendation from decision engine")
    if scenario == MorningBriefScenario.DATA_UNAVAILABLE:
        gaps.append("Some market data unavailable")
    if decision and decision.verdict == DecisionVerdict.ACT and not evidence.evidence_available:
        gaps.append("Evidence unavailable for ACT verdict")
    if not personalized and broker.state != "not_configured":
        gaps.append("Portfolio scope limited")
    return tuple(gaps)


def _portfolio_section(broker: BrokerSnapshot, prefs: IntradayPrefs) -> PortfolioSection:
    personalized, scope = _portfolio_scope(broker)
    ready = scope == "full"
    count = broker.holdings_count
    sync = broker.last_sync_at or "recently"
    cash = broker.available_cash_inr or None
    tactical = float(prefs.capital or 0) if prefs and prefs.capital else None

    if not broker.connected():
        summary = (
            "Market context only — connect for your portfolio"
            if broker.state == "not_configured"
            else "Broker offline — connect for personalized risk"
        )
        ready = False
    elif broker.state == "limited":
        summary = f"Holdings as of {sync} — refresh recommended"
        ready = False
    elif cash and cash > 0:
        summary = f"Portfolio synced · {count} holdings · ₹{cash:,.0f} cash · {sync}"
    else:
        summary = f"Portfolio synced · {count} holdings · {sync}"

    return PortfolioSection(
        ready=ready,
        holdings_count=count,
        cash_available_inr=cash,
        tactical_pool_inr=tactical if tactical and tactical > 0 else None,
        sacred_core_excluded=True,
        summary=summary,
    )


def _opportunity_section(
    *,
    verdict_key: str,
    os_report: InvestmentOS,
    pins: list[PinnedPlan],
) -> OpportunitySection:
    if verdict_key != "trade":
        return OpportunitySection(visible=False, symbol="", setup="", lane="MIS")
    sym = (os_report.starred_symbol or "").upper().replace(".NS", "").replace(".BO", "")
    setup = _strip_md(os_report.next_step or "Review trade plan")
    if not sym and pins:
        pin = pins[0]
        sym = pin.symbol.upper().replace(".NS", "").replace(".BO", "")
        setup = f"Entry near ₹{pin.entry:,.0f} · stop ₹{pin.stop_loss:,.0f}"
    if not sym:
        return OpportunitySection(visible=False, symbol="", setup="", lane="MIS")
    return OpportunitySection(
        visible=True,
        symbol=sym,
        setup=_trim_words(setup, max_words=12),
        lane="MIS",
    )


def _risk_section(
    *,
    verdict_key: str,
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
) -> RiskSection:
    warnings: list[str] = []
    if mis.loss_streak_days >= 2:
        warnings.append(f"{mis.loss_streak_days} loss days — pause new risk")
    for flag in (mis.flags or [])[:2]:
        text = _strip_md(flag)
        if text:
            warnings.append(text)
    if snapshot.risk_mode in ("RISK-OFF", "CLOSED"):
        warnings.append(f"Risk mode: {snapshot.risk_mode}")

    if verdict_key == "pause":
        level = "paused"
    elif mis.loss_streak_days >= 2 or snapshot.risk_mode in ("RISK-OFF", "CLOSED"):
        level = "high"
    elif len(snapshot.trading_restrictions) >= 2:
        level = "medium"
    else:
        level = "low"

    ribbon: list[str] = []
    phase = session_phase(snapshot)
    if phase and phase not in ("regular", "unknown"):
        ribbon.append(phase.replace("_", " ").title())
    if snapshot.risk_mode and snapshot.risk_mode != "NEUTRAL":
        ribbon.append(snapshot.risk_mode)
    for restriction in snapshot.trading_restrictions[:2]:
        ribbon.append(_strip_md(restriction)[:40])

    return RiskSection(level=level, warnings=tuple(warnings[:3]), session_ribbon=tuple(ribbon[:4]))


def assemble_morning_brief_view_model(
    *,
    market: str,
    context: ContextSnapshot,
    decision: DecisionArtifact | None,
    decision_source: str,
    broker: BrokerSnapshot,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    pins: list[PinnedPlan],
    prefs: IntradayPrefs,
    built_at: str,
    scenario: MorningBriefScenario,
    stale: bool,
    stale_reason: str,
    context_from_cache: bool,
    context_cache_age: float | None,
    data_error: str,
    evidence_packet: EvidencePacket | None,
) -> MorningBriefViewModel:
    evidence = assemble_evidence_section(decision, evidence_packet)
    verdict, verdict_display, verdict_key, cta_label, cta_action = _resolve_verdict_display(
        scenario=scenario,
        broker=broker,
        snapshot=context,
        mis=mis,
        decision=decision,
        evidence=evidence,
    )
    reason = _mentor_line(
        scenario=scenario,
        verdict_key=verdict_key,
        decision=decision,
        mis=mis,
        os_report=os_report,
        snapshot=context,
        pins=pins,
        evidence=evidence,
    )
    portfolio = _portfolio_section(broker, prefs)
    personalized, scope = _portfolio_scope(broker)

    decision_fresh = _decision_fresh(decision, context)
    context_fresh = True
    if context_from_cache and context_cache_age is not None:
        context_fresh = context_cache_age <= STALE_CONTEXT_SECONDS_OPEN
    elif context_from_cache:
        context_fresh = False

    trust_gaps = _trust_gaps(
        scenario=scenario,
        decision=decision,
        evidence=evidence,
        broker=broker,
        personalized=personalized,
    )
    stale_label = stale_reason if stale else ""
    if stale and not stale_label:
        stale_label = "Updating recommendation"

    trust = TrustSection(
        why_this_is_recommended=_why_recommended(decision, evidence, verdict_key=verdict_key),
        recommendation_confidence=_confidence_band(decision),
        data_freshness=DataFreshnessSection(
            context_fresh=context_fresh,
            context_age_sec=context_cache_age,
            decision_fresh=decision_fresh,
            decision_age_min=_decision_age_min(decision),
            broker_sync_state=_broker_sync_state(broker),
            broker_last_sync=broker.last_sync_at or "",
        ),
        portfolio_sync_status=PortfolioSyncSection(
            personalized=personalized,
            scope=scope,
            summary=portfolio.summary,
        ),
        stale=stale,
        stale_label=stale_label,
        gaps=trust_gaps,
    )

    last_updated = built_at
    if decision and decision.timestamp:
        last_updated = str(decision.timestamp)[:19] or built_at

    decision_section = DecisionSection(
        verdict=verdict,
        verdict_display=verdict_display,
        verdict_key=verdict_key,
        reason=reason,
        confidence_level=_conf_numeric(decision, context),
        confidence_band=_confidence_band(decision),
        last_updated=last_updated,
        valid_until=_valid_until(decision, context),
        cta_label=cta_label,
        cta_action=cta_action,
        decision_id=decision.decision_id if decision else "",
        decision_source=decision_source,
    )

    failure_message: str | None = None
    if scenario == MorningBriefScenario.DATA_UNAVAILABLE:
        failure_message = data_error or "Data temporarily unavailable"
    elif scenario == MorningBriefScenario.DECISION_UNAVAILABLE:
        failure_message = "Decision engine returned no equity recommendation"

    return MorningBriefViewModel(
        meta=BriefMetaSection(
            built_at=built_at,
            scenario=scenario.value,
            market=market,
            session_phase=session_phase(context),
        ),
        decision=decision_section,
        evidence=evidence,
        trust=trust,
        opportunity=_opportunity_section(verdict_key=verdict_key, os_report=os_report, pins=pins),
        portfolio=portfolio,
        risk=_risk_section(verdict_key=verdict_key, snapshot=context, mis=mis),
        failure_message=failure_message,
    )


def domain_bundle_for_cache(
    *,
    market: str,
    context: ContextSnapshot,
    decision: DecisionArtifact | None,
    decision_source: str,
    broker: BrokerSnapshot,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    pins: list[PinnedPlan],
    prefs: IntradayPrefs,
    built_at: str,
    scenario: MorningBriefScenario,
    stale: bool,
    stale_reason: str,
    context_from_cache: bool,
    context_cache_age: float | None,
    data_error: str,
) -> dict[str, Any]:
    """Domain fields for Streamlit cache — view model rebuilt on read."""
    from analyzer.use_cases.snapshot_cache import snapshot_to_cache

    return {
        "snapshot": snapshot_to_cache(context),
        "_broker_at_build": broker.to_dict(),
        "mis": mis,
        "os_report": os_report,
        "pins": pins,
        "prefs": prefs,
        "built_at": built_at,
        "market": market,
        "decision_source": decision_source,
        "scenario": scenario.value,
        "stale": stale,
        "stale_reason": stale_reason,
        "context_from_cache": context_from_cache,
        "context_cache_age": context_cache_age,
        "data_error": data_error,
    }
