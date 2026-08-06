"""Research Journal — presentation contracts and projection (V3-202)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from analyzer.decision_engine.models import DecisionArtifact
from ui.components.research_workspace_ui import (
    DISPOSITION_LABELS,
    ResearchWorkspaceContract,
)
from ui.components.understand_popover import UnderstandContract, UnderstandSection

_DECISION_TEXT_KEY = "research_investment_decision_text"
_DISPOSITION_KEY = "research_disposition"
_REVIEWED_QUESTIONS_KEY = "research_reviewed_question_keys"
ENTRY_TYPE_RESEARCH = "research_decision"
SOURCE_RESEARCH = "Research"


@dataclass(frozen=True)
class ResearchJournalDraftContract:
    entry_id: str
    entry_type: str
    symbol: str
    recorded_at: str
    recorded_at_label: str
    user_narrative: str
    disposition: str
    disposition_label: str
    investment_view_label: str
    investment_view_summary: str
    system_summary_lines: tuple[str, ...]
    questions_reviewed: tuple[bool, ...]
    decision_id: str
    evidence_packet_id: str
    bundle_built_at: str
    bundle_version: str
    portfolio_held: bool
    portfolio_weight_label: str
    portfolio_health_label: str
    portfolio_flag_label: str
    review_theme_key: str
    research_back_tab: str
    research_back_subtab: str
    show_proof: bool
    understand: UnderstandContract
    prior_entry_id: str
    supersedes_entry_id: str


@dataclass(frozen=True)
class ResearchDecisionEntryContract:
    entry_id: str
    entry_type: str
    symbol: str
    recorded_at: str
    recorded_at_label: str
    user_narrative: str
    disposition: str
    disposition_label: str
    investment_view_label: str
    investment_view_summary: str
    system_summary_lines: tuple[str, ...]
    questions_reviewed: tuple[bool, ...]
    decision_id: str
    evidence_packet_id: str
    bundle_built_at: str
    bundle_version: str
    portfolio_held: bool
    portfolio_weight_label: str
    portfolio_health_label: str
    portfolio_flag_label: str
    review_theme_key: str
    research_back_tab: str
    research_back_subtab: str
    show_proof: bool
    understand: UnderstandContract
    prior_entry_id: str
    supersedes_entry_id: str
    follow_up_of_entry_id: str
    source_label: str


def _decision_from_cache(cached: dict[str, Any]) -> DecisionArtifact | None:
    decision = cached.get("decision")
    if isinstance(decision, DecisionArtifact):
        return decision
    os_report = cached.get("os_report")
    if os_report is not None:
        artifact = getattr(os_report, "decision_artifact", None)
        if isinstance(artifact, DecisionArtifact):
            return artifact
    return None


def _now_labels() -> tuple[str, str]:
    now = datetime.now(timezone.utc).astimezone()
    return now.isoformat(), now.strftime("%d %b %Y, %H:%M %Z")


def _questions_reviewed_flags(*, symbol: str, session: dict[str, Any]) -> tuple[bool, ...]:
    raw = session.get(_REVIEWED_QUESTIONS_KEY, set())
    reviewed = set(raw) if isinstance(raw, set) else set(raw or [])
    prefix = f"{symbol.upper()}:"
    flags: list[bool] = []
    for index in range(1, 8):
        flags.append(f"{prefix}{index}" in reviewed)
    return tuple(flags)


def _session_decision_fields(*, symbol: str, session: dict[str, Any], default_disposition: str) -> tuple[str, str]:
    text_key = f"{_DECISION_TEXT_KEY}_{symbol}"
    disposition_key = f"{_DISPOSITION_KEY}_{symbol}"
    narrative = str(session.get(text_key, "") or "").strip()
    disposition = str(session.get(disposition_key, default_disposition) or default_disposition)
    if disposition not in DISPOSITION_LABELS:
        disposition = default_disposition
    return narrative, disposition


def research_journal_draft_from_workspace(
    *,
    contract: ResearchWorkspaceContract,
    session: dict[str, Any],
    cached: dict[str, Any] | None = None,
    prior_entry_id: str = "",
) -> ResearchJournalDraftContract:
    """Projection-only draft from Research Workbench + session Q7."""
    symbol = contract.symbol
    narrative, disposition = _session_decision_fields(
        symbol=symbol,
        session=session,
        default_disposition=contract.decision.default_disposition,
    )
    recorded_at, recorded_at_label = _now_labels()
    decision = _decision_from_cache(cached) if cached else None
    bundle_built_at = str((cached or {}).get("built_at", "") or "")
    bundle_version = str((cached or {}).get("_context_bundle_version", "") or "")
    review_theme_key = str(session.get("research_review_theme_key", "") or "")
    research_back_tab = str(session.get("research_back_tab", "My Portfolio") or "My Portfolio")
    research_back_subtab = str(session.get("research_back_subtab", "") or "")
    return ResearchJournalDraftContract(
        entry_id=str(uuid.uuid4()),
        entry_type=ENTRY_TYPE_RESEARCH,
        symbol=symbol,
        recorded_at=recorded_at,
        recorded_at_label=recorded_at_label,
        user_narrative=narrative,
        disposition=disposition,
        disposition_label=DISPOSITION_LABELS[disposition],
        investment_view_label=contract.hero.view_label,
        investment_view_summary=contract.hero.summary,
        system_summary_lines=contract.decision.system_summary_lines,
        questions_reviewed=_questions_reviewed_flags(symbol=symbol, session=session),
        decision_id=decision.decision_id if decision else "",
        evidence_packet_id=contract.evidence_packet_id,
        bundle_built_at=bundle_built_at,
        bundle_version=bundle_version,
        portfolio_held=contract.context.held,
        portfolio_weight_label=contract.context.weight_label,
        portfolio_health_label=contract.context.health_label,
        portfolio_flag_label=contract.context.flag_label,
        review_theme_key=review_theme_key,
        research_back_tab=research_back_tab,
        research_back_subtab=research_back_subtab,
        show_proof=contract.show_proof,
        understand=contract.understand,
        prior_entry_id=prior_entry_id,
        supersedes_entry_id="",
    )


def draft_to_confirmed_entry(
    draft: ResearchJournalDraftContract,
    *,
    supersedes_entry_id: str = "",
    follow_up_of_entry_id: str = "",
) -> ResearchDecisionEntryContract:
    confirm_at, confirm_label = _now_labels()
    return ResearchDecisionEntryContract(
        entry_id=draft.entry_id,
        entry_type=draft.entry_type,
        symbol=draft.symbol,
        recorded_at=confirm_at,
        recorded_at_label=confirm_label,
        user_narrative=draft.user_narrative,
        disposition=draft.disposition,
        disposition_label=draft.disposition_label,
        investment_view_label=draft.investment_view_label,
        investment_view_summary=draft.investment_view_summary,
        system_summary_lines=draft.system_summary_lines,
        questions_reviewed=draft.questions_reviewed,
        decision_id=draft.decision_id,
        evidence_packet_id=draft.evidence_packet_id,
        bundle_built_at=draft.bundle_built_at,
        bundle_version=draft.bundle_version,
        portfolio_held=draft.portfolio_held,
        portfolio_weight_label=draft.portfolio_weight_label,
        portfolio_health_label=draft.portfolio_health_label,
        portfolio_flag_label=draft.portfolio_flag_label,
        review_theme_key=draft.review_theme_key,
        research_back_tab=draft.research_back_tab,
        research_back_subtab=draft.research_back_subtab,
        show_proof=draft.show_proof,
        understand=draft.understand,
        prior_entry_id=draft.prior_entry_id,
        supersedes_entry_id=supersedes_entry_id or draft.supersedes_entry_id,
        follow_up_of_entry_id=follow_up_of_entry_id,
        source_label=SOURCE_RESEARCH,
    )


def prior_confirmed_entry_id(*, symbol: str, entries: tuple[ResearchDecisionEntryContract, ...]) -> str:
    for entry in reversed(entries):
        if entry.symbol.upper() == symbol.upper():
            return entry.entry_id
    return ""


def symbol_entry_chain(
    *,
    symbol: str,
    entries: tuple[ResearchDecisionEntryContract, ...],
) -> tuple[ResearchDecisionEntryContract, ...]:
    clean = symbol.upper()
    matched = [entry for entry in entries if entry.symbol.upper() == clean]
    return tuple(sorted(matched, key=lambda item: item.recorded_at, reverse=True))


def understand_from_entry(entry: ResearchDecisionEntryContract | ResearchJournalDraftContract) -> UnderstandContract:
    return entry.understand


def fallback_understand() -> UnderstandContract:
    return UnderstandContract(
        sections=(UnderstandSection(title="Journal", lines=("Decision memory only — no live recompute.",)),),
    )
