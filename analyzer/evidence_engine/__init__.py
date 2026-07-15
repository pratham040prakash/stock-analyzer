"""Evidence Engine — canonical investment evidence layer (Migration Step 2)."""

from analyzer.evidence_engine.builder import EvidenceBuilder, evidence_item_id
from analyzer.evidence_engine.conflicts import EvidenceConflictDetector, merge_duplicate_items
from analyzer.evidence_engine.engine import EvidenceEngine, SCOPE_REQUIRED_CATEGORIES, default_engine
from analyzer.evidence_engine.migration import (
    attach_synthesis_evidence,
    build_equity_research_packet,
    build_synthesis_packet,
    evidence_from_advice,
    evidence_from_combined,
    evidence_from_data_gaps,
    evidence_from_data_health,
    evidence_from_market_pulse,
    evidence_from_relative_strength,
    evidence_from_strategy_votes,
)
from analyzer.evidence_engine.models import (
    ALL_CATEGORIES,
    EvidenceCategory,
    EvidenceConfidence,
    EvidenceConflict,
    EvidenceItem,
    EvidencePacket,
    EvidenceSource,
    EvidenceType,
    RecommendationFromEvidence,
)
from analyzer.evidence_engine.render import (
    format_evidence_category,
    format_evidence_report,
    format_evidence_summary,
    render_recommendation_rationale,
)
from analyzer.evidence_engine.serialization import (
    evidence_item_from_dict,
    evidence_item_to_dict,
    evidence_packet_from_dict,
    evidence_packet_from_json,
    evidence_packet_to_dict,
    evidence_packet_to_json,
)
from analyzer.evidence_engine.store import (
    fetch_evidence_packet,
    init_evidence_store,
    save_evidence_packet,
)
from analyzer.evidence_engine.validator import EvidenceValidator

__all__ = [
    "ALL_CATEGORIES",
    "EvidenceBuilder",
    "EvidenceCategory",
    "EvidenceConfidence",
    "EvidenceConflict",
    "EvidenceConflictDetector",
    "EvidenceEngine",
    "EvidenceItem",
    "EvidencePacket",
    "EvidenceSource",
    "EvidenceType",
    "EvidenceValidator",
    "RecommendationFromEvidence",
    "SCOPE_REQUIRED_CATEGORIES",
    "attach_synthesis_evidence",
    "build_equity_research_packet",
    "build_synthesis_packet",
    "default_engine",
    "evidence_from_advice",
    "evidence_from_combined",
    "evidence_from_data_gaps",
    "evidence_from_data_health",
    "evidence_from_market_pulse",
    "evidence_from_relative_strength",
    "evidence_from_strategy_votes",
    "evidence_item_from_dict",
    "evidence_item_id",
    "evidence_item_to_dict",
    "evidence_packet_from_dict",
    "evidence_packet_from_json",
    "evidence_packet_to_dict",
    "evidence_packet_to_json",
    "fetch_evidence_packet",
    "format_evidence_category",
    "format_evidence_report",
    "format_evidence_summary",
    "init_evidence_store",
    "merge_duplicate_items",
    "render_recommendation_rationale",
    "save_evidence_packet",
]
