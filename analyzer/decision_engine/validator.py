"""Validate decision inputs before verdict issuance."""

from __future__ import annotations

import logging

from analyzer.decision_engine.models import DecisionContext, DecisionRequest
from analyzer.decision_engine.rules import (
    CRITICAL_GAP_CATEGORIES,
    MAX_CONFIDENCE,
    MIN_COMPLETENESS_PCT,
    MIN_CONFIDENCE,
    is_critical_gap,
)
from analyzer.evidence_engine.models import EvidencePacket

logger = logging.getLogger(__name__)


class DecisionValidationError(ValueError):
    """Raised when decision inputs fail validation."""


class DecisionValidator:
    """Step 1 — gate the decision pipeline."""

    def validate_packet(self, packet: EvidencePacket | None) -> list[str]:
        errors: list[str] = []
        if packet is None:
            errors.append("Missing EvidencePacket")
            return errors
        if not packet.packet_id:
            errors.append("Invalid EvidencePacket: missing packet_id")
        if not packet.subject:
            errors.append("Invalid EvidencePacket: missing subject")
        if packet.completeness_pct < MIN_COMPLETENESS_PCT:
            errors.append(
                f"Invalid EvidencePacket: completeness {packet.completeness_pct:.0f}% "
                f"below minimum {MIN_COMPLETENESS_PCT:.0f}%"
            )
        return errors

    def find_critical_gaps(self, packet: EvidencePacket) -> list[str]:
        """Step 2 — critical GAP items block positive verdicts."""
        labels: list[str] = []
        for item in packet.items:
            if is_critical_gap(item):
                labels.append(item.label or item.id)
        for gap in packet.gaps:
            cat = gap.category
            if cat in CRITICAL_GAP_CATEGORIES:
                labels.append(gap.label or gap.explanation[:60])
        return list(dict.fromkeys(labels))

    def validate_context(self, context: DecisionContext) -> list[str]:
        errors: list[str] = []
        if context.market is None:
            errors.append("Missing Context: market")
        if context.capital is None:
            errors.append("Missing Context: capital")
        if context.portfolio is None:
            errors.append("Missing Context: portfolio")
        elif not context.portfolio.known:
            errors.append("Unknown Portfolio State")
        if context.risk is None:
            errors.append("Missing Risk Constraints")
        elif context.risk.max_risk_pct <= 0 or context.risk.max_risk_pct > 50:
            errors.append("Invalid Risk Constraints: max_risk_pct out of range")
        return errors

    def validate_request(self, request: DecisionRequest) -> list[str]:
        errors: list[str] = []
        if not request.subject:
            errors.append("DecisionRequest missing subject")
        if not request.evidence_packet_id:
            errors.append("DecisionRequest missing evidence_packet_id")
        errors.extend(self.validate_context(request.context))
        if request.capital.capital_inr <= 0:
            errors.append("Capital must be positive")
        return errors

    def validate_confidence(self, confidence: float) -> list[str]:
        if confidence < MIN_CONFIDENCE or confidence > MAX_CONFIDENCE:
            return [f"Invalid Confidence: {confidence} not in [{MIN_CONFIDENCE}, {MAX_CONFIDENCE}]"]
        return []

    def validate_artifact(self, artifact) -> list[str]:
        """Post-build integrity checks — evidence link and explainability."""
        errors: list[str] = []
        packet_id = (artifact.evidence_packet_id or "").strip()
        if not packet_id:
            errors.append("DecisionArtifact missing evidence_packet_id")
        if packet_id == "missing":
            errors.append("DecisionArtifact has invalid evidence_packet_id")
        exp = artifact.explainability
        if exp is None:
            errors.append("DecisionArtifact missing explainability")
        elif not (exp.why and exp.why_now and exp.why_not):
            errors.append("DecisionArtifact explainability incomplete")
        return errors

    def context_warnings(self, context: DecisionContext) -> list[str]:
        warnings: list[str] = []
        if not context.market.allow_new_entries:
            warnings.append("Session blocks new entries")
        if not context.market.allow_aggressive:
            warnings.append("Regime disallows aggressive intraday")
        if not context.market.session_open:
            warnings.append("Market session closed")
        return warnings

    def validate_all(
        self,
        packet: EvidencePacket | None,
        request: DecisionRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        errors = self.validate_packet(packet) + self.validate_request(request)
        warnings = self.context_warnings(request.context)
        critical_gaps: list[str] = []
        if packet is not None and not errors:
            critical_gaps = self.find_critical_gaps(packet)
        if errors:
            logger.info("decision validation errors: %s", errors)
        return errors, warnings, critical_gaps
