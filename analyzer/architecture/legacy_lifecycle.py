"""APEX-012 legacy module lifecycle registry.

Lifecycle: ACTIVE → QUARANTINED → DORMANT → (2 weeks Founder dogfood) → DELETE

No module may skip a stage. Phase 0 marks only — no deletions.
"""

from __future__ import annotations

from enum import Enum
from typing import TypedDict


class LegacyLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    DORMANT = "DORMANT"


LIFECYCLE_MARKER_PREFIX = "APEX-012-LIFECYCLE:"


def lifecycle_marker(state: LegacyLifecycle) -> str:
    return f"{LIFECYCLE_MARKER_PREFIX} {state.value}"


class LegacyModuleRecord(TypedDict):
    lifecycle: LegacyLifecycle
    owner: str
    replacement: str
    removal_criteria: str
    tier: str


# Canonical stack — ACTIVE (inputs or authoritative assembly)
LEGACY_MODULE_REGISTRY: dict[str, LegacyModuleRecord] = {
    "analyzer/decision_engine/engine.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Decision Engine",
        "replacement": "N/A — sole verdict enum owner",
        "removal_criteria": "Never — canonical boundary",
        "tier": "engine",
    },
    "analyzer/evidence_engine/engine.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Evidence Engine",
        "replacement": "N/A — sole evidence packet builder for DE",
        "removal_criteria": "Never — canonical boundary",
        "tier": "engine",
    },
    "analyzer/use_cases/morning_brief_assembly.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Morning Brief use case",
        "replacement": "N/A — assembles MorningBriefViewModel",
        "removal_criteria": "Never — canonical daily contract",
        "tier": "use_case",
    },
    "analyzer/use_cases/morning_brief_models.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Morning Brief use case",
        "replacement": "N/A — root DTO schema",
        "removal_criteria": "Never — canonical contract",
        "tier": "use_case",
    },
    "ui/components/morning_brief_ui.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Projection layer",
        "replacement": "N/A — brief loader + projection helpers",
        "removal_criteria": "Never — Tier A entry point",
        "tier": "tier_a_projection",
    },
    "ui/components/decision_card.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Projection layer",
        "replacement": "N/A — hero projection from MorningBriefViewModel",
        "removal_criteria": "Never — Tier A projection",
        "tier": "tier_a_projection",
    },
    "ui/components/home_dashboard.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Projection layer",
        "replacement": "N/A — Today orchestration",
        "removal_criteria": "Never — Tier A surface",
        "tier": "tier_a_projection",
    },
    "ui/components/plan_canvas.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Projection layer — Trades",
        "replacement": "N/A — Phase 3 migrates to brief-only inputs",
        "removal_criteria": "Never — Tier A surface",
        "tier": "tier_a_projection",
    },
    "ui/components/answer_canvas.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Projection layer — Ask",
        "replacement": "N/A — Phase 3 migrates to brief-only inputs",
        "removal_criteria": "Never — Tier A surface",
        "tier": "tier_a_projection",
    },
    "ui/components/proof_mapper.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Projection layer — Proof",
        "replacement": "N/A — Tier B; must not override brief verdict",
        "removal_criteria": "Never — Tier B surface",
        "tier": "tier_b_projection",
    },
    "ui/components/trust_canvas.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Tier B — Trust depth",
        "replacement": "brief.trust + journal overlay (APEX-012 Phase 4)",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "tier_b_projection",
    },
    "ui/components/reflection_canvas.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Tier B — Reflection",
        "replacement": "brief.meta.scenario + journal (APEX-012 Phase 4)",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "tier_b_projection",
    },
    "ui/components/today_intelligence.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Legacy Today intel",
        "replacement": "MorningBriefViewModel projection (APEX-012 Phase 2)",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "duplicate",
    },
    "ui/components/investment_os_ui.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Legacy OS verdict tile",
        "replacement": "Today hero via project_decision_card",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "duplicate",
    },
    "ui/components/mis_trade_advisory.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Legacy MIS strip UI",
        "replacement": "brief.risk + brief.trust sections",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "duplicate",
    },
    "analyzer/investment_os.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Legacy daily OS builder",
        "replacement": "MorningBriefViewModel assembly inputs only (no user-facing verdict)",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "legacy_input",
    },
    "analyzer/evidence_engine/engine.py:recommend_from_packet": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Evidence Engine",
        "replacement": "DecisionEngine.decide only",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "duplicate_verdict",
    },
    "ui/pages/alpha_ai.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Research — Alpha AI",
        "replacement": "Labeled Research; must not override Today",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "research",
    },
    "ui/pages/daily_advisor.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Research — Daily Advisor",
        "replacement": "Today Morning Brief",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "research",
    },
    "ui/pages/single_stock.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Research Workbench (V3-201)",
        "replacement": "Guided research questions + Investment Decision",
        "removal_criteria": "N/A — active V3 pillar surface",
        "tier": "research",
    },
    "ui/pages/research_journal.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Research Journal Integration (V3-202)",
        "replacement": "Decision memory — draft confirm immutable entry",
        "removal_criteria": "N/A — active V3 pillar surface",
        "tier": "journal",
    },
    "ui/components/research_journal_ui.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Research Journal contracts (V3-202)",
        "replacement": "Projection-only journal draft/entry contracts",
        "removal_criteria": "N/A — active V3 pillar surface",
        "tier": "journal",
    },
    "ui/components/research_journal_experience.py": {
        "lifecycle": LegacyLifecycle.ACTIVE,
        "owner": "Research Journal experience (V3-202)",
        "replacement": "Timeline · Drafts · Confirm · Entry Detail render",
        "removal_criteria": "N/A — active V3 pillar surface",
        "tier": "journal",
    },
    "ui/pages/intraday.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Research — Intraday",
        "replacement": "Today + Trades for daily execution",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "research",
    },
    "ui/pages/live_charts.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Research — Live Charts",
        "replacement": "Proof overlay for structure",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "research",
    },
    "ui/pages/live_options_advisor.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Research — Options Coach",
        "replacement": "Out of scope for daily equity brief",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "research",
    },
    "ui/pages/market_pulse.py": {
        "lifecycle": LegacyLifecycle.QUARANTINED,
        "owner": "Research — Market Pulse",
        "replacement": "brief.meta / market section on Today",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "research",
    },
    # DORMANT — rarely used; candidate for deletion after quarantine period
    "analyzer/morning_briefing.py": {
        "lifecycle": LegacyLifecycle.DORMANT,
        "owner": "CLI legacy briefing",
        "replacement": "analyzer.use_cases.morning_brief.build_morning_brief",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "obsolete",
    },
    "scripts/morning_briefing.py": {
        "lifecycle": LegacyLifecycle.DORMANT,
        "owner": "CLI wrapper",
        "replacement": "build_morning_brief CLI",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "obsolete",
    },
    "ui/components/morning_cockpit.py": {
        "lifecycle": LegacyLifecycle.DORMANT,
        "owner": "Legacy morning dashboard",
        "replacement": "Home / Today partner shell",
        "removal_criteria": "Two weeks successful Founder dogfood after DORMANT",
        "tier": "obsolete",
    },
}

# Tier A — Decision projections (APEX-012 Amendment 2)
TIER_A_DECISION_PROJECTION: tuple[str, ...] = (
    "ui/components/home_dashboard.py",
    "ui/components/decision_card.py",
    "ui/components/morning_brief_ui.py",
    "ui/components/plan_canvas.py",
    "ui/components/answer_canvas.py",
)

# Tier B — Reflective projections
TIER_B_REFLECTIVE_PROJECTION: tuple[str, ...] = (
    "ui/components/proof_mapper.py",
    "ui/components/trust_canvas.py",
    "ui/components/reflection_canvas.py",
)

# Pre-Phase-1 baseline: known Tier A imports that must shrink in Phase 3, never expand
TIER_A_IMPORT_BASELINE: frozenset[str] = frozenset({
    "ui/components/plan_canvas.py",
    "ui/components/answer_canvas.py",
})

UI_FORBIDDEN_DECISION_ENGINE_IMPORTS: tuple[str, ...] = (
    "analyzer.decision_engine.engine",
    "analyzer.decision_engine.reasoner",
    "analyzer.decision_engine.migration",
    "analyzer.decision_engine.factory",
)

UI_FORBIDDEN_DECISION_ENGINE_CALLS: tuple[str, ...] = (
    "decide_from_packet(",
    "DecisionEngine(",
)

UI_MIS_BUILD_ALLOWLIST: frozenset[str] = frozenset({
    "ui/components/partner_data.py",
    "ui/components/mis_trade_advisory.py",
})

OPPORTUNITY_RANKING_FUNCTION_NAMES: frozenset[str] = frozenset({
    "_build_opportunity_views",
    "_pick_best",
    "_pick_next_watch",
})
