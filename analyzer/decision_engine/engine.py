"""Decision Engine — the only component that issues investment verdicts."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import logging

from analyzer.decision_engine.factory import DecisionFactory
from analyzer.decision_engine.history import ImmutableDecisionError, save_decision
from analyzer.decision_engine.models import (
    CapitalConstraints,
    DecisionArtifact,
    DecisionContext,
    DecisionExplainability,
    DecisionRequest,
    DecisionVerdict,
    MarketContext,
    PortfolioState,
    RiskSettings,
    UncertaintyVector,
    UserPreferences,
)
from analyzer.decision_engine.reasoner import DecisionReasoner
from analyzer.decision_engine.validator import DecisionValidator
from analyzer.evidence_engine.models import EvidencePacket
from analyzer.structured_log import log_event

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    8-step pipeline:
    1 Validate EvidencePacket
    2 Reject critical GAP
    3 Evaluate Context
    4 Evaluate Risk
    5 Evaluate Portfolio Constraints
    6 Evaluate Capital Constraints
    7 Generate Verdict
    8 Generate explainable DecisionArtifact
    """

    def __init__(
        self,
        *,
        validator: DecisionValidator | None = None,
        reasoner: DecisionReasoner | None = None,
        factory: DecisionFactory | None = None,
        persist: bool = True,
    ):
        self._validator = validator or DecisionValidator()
        self._reasoner = reasoner or DecisionReasoner()
        self._factory = factory or DecisionFactory()
        self._persist = persist

    def decide(
        self,
        packet: EvidencePacket,
        *,
        market: MarketContext | None = None,
        capital: CapitalConstraints | None = None,
        portfolio: PortfolioState | None = None,
        preferences: UserPreferences | None = None,
        risk: RiskSettings | None = None,
        subject_type: str | None = None,
        persist: bool | None = None,
    ) -> DecisionArtifact:
        context = DecisionContext(
            market=market or MarketContext(),
            capital=capital or CapitalConstraints(),
            portfolio=portfolio or PortfolioState(),
            preferences=preferences or UserPreferences(),
            risk=risk or RiskSettings(),
        )
        subject_type = subject_type or packet.subject_type
        request = DecisionRequest(
            subject=packet.subject,
            subject_type=subject_type,
            evidence_packet_id=packet.packet_id,
            context=context,
        )

        # Step 1 — validate
        errors, warnings, critical_gaps = self._validator.validate_all(packet, request)
        if errors:
            artifact = self._build_validation_failure(
                packet=packet,
                subject_type=subject_type,
                errors=errors,
                warnings=warnings,
            )
            return self._finalize(artifact, persist=persist)

        # Step 2 — critical GAP rejection (verdict determined here, not in factory)
        if critical_gaps:
            artifact = self._build_gap_rejection(
                packet=packet,
                subject_type=subject_type,
                gap_labels=critical_gaps,
            )
            return self._finalize(artifact, persist=persist)

        # Step 3 — evaluate context (warnings inform uncertainty)
        evidence_score = self._reasoner.score_packet(packet)
        uncertainty = self._reasoner.compute_uncertainty(packet, context, warnings)

        # Steps 4–6 — risk, portfolio, capital
        risk_block, risk_reason = self._reasoner.risk_block(packet, context, evidence_score.net)
        capital_block, capital_reason = self._reasoner.capital_block(context)

        confidence = self._reasoner.confidence(
            evidence_score.net,
            evidence_score.scored,
            packet,
            uncertainty.overall,
        )
        conf_errors = self._validator.validate_confidence(confidence)
        if conf_errors and confidence != 0.0:
            logger.warning("confidence validation: %s", conf_errors)

        # Step 7 — verdict (only DecisionEngine selects canonical verdict)
        verdict, reason, trade_allowed, alts, invalidations = self._reasoner.resolve_verdict(
            net=evidence_score.net,
            confidence=confidence,
            packet=packet,
            context=context,
            risk_block=risk_block,
            risk_reason=risk_reason,
            capital_block=capital_block,
            capital_reason=capital_reason,
        )

        # Step 8 — artifact
        artifact = self._factory.build(
            packet=packet,
            subject_type=subject_type,
            context=context,
            evidence_score=evidence_score,
            verdict=verdict,
            reason=reason,
            confidence=confidence,
            uncertainty=uncertainty,
            trade_allowed=trade_allowed,
            alternative_actions=alts,
            invalidation_conditions=invalidations,
            warnings=warnings,
        )
        return self._finalize(artifact, persist=persist)

    def _build_gap_rejection(
        self,
        *,
        packet: EvidencePacket,
        subject_type: str,
        gap_labels: list[str],
    ) -> DecisionArtifact:
        reason = f"Critical evidence gaps: {', '.join(gap_labels[:3])}"
        explain = DecisionExplainability(
            why=reason,
            why_now="Cannot issue ACT — required evidence categories are missing",
            why_not="Insufficient coverage in risk, execution, or market evidence",
        )
        return self._factory.build_deterministic(
            packet=packet,
            subject_type=subject_type,
            verdict=DecisionVerdict.PASS,
            reason=reason,
            explainability=explain,
            uncertainty=UncertaintyVector(
                evidence_completeness=max(0.0, 100.0 - packet.completeness_pct),
                data_quality=min(100.0, len(gap_labels) * 25.0),
                overall=min(100.0, 60.0 + len(gap_labels) * 10.0),
            ),
            capital_recommendation="Zero new capital deployment",
            execution_recommendation="No trade until gaps are filled",
            alternative_actions=["WAIT", "DEFENSIVE"],
            invalidation_conditions=gap_labels[:5],
            metadata={"gap_rejection": True, "gap_count": len(gap_labels)},
        )

    def _build_validation_failure(
        self,
        *,
        packet: EvidencePacket,
        subject_type: str,
        errors: list[str],
        warnings: list[str],
    ) -> DecisionArtifact:
        reason = f"Validation failed: {'; '.join(errors[:3])}"
        explain = DecisionExplainability(
            why=reason,
            why_now="Decision inputs failed validation — default WAIT",
            why_not="Cannot convert evidence to verdict without valid packet and context",
        )
        return self._factory.build_deterministic(
            packet=packet,
            subject_type=subject_type,
            verdict=DecisionVerdict.WAIT,
            reason=reason,
            explainability=explain,
            uncertainty=UncertaintyVector(overall=80.0, evidence_completeness=80.0),
            capital_recommendation="No deployment — validation failed",
            execution_recommendation="Wait until evidence and context are valid",
            alternative_actions=["PASS", "DEFENSIVE"],
            invalidation_conditions=warnings[:3] + errors[:2],
        )

    def _finalize(self, artifact: DecisionArtifact, *, persist: bool | None) -> DecisionArtifact:
        artifact_errors = self._validator.validate_artifact(artifact)
        if artifact_errors:
            logger.error("decision artifact integrity failed: %s", artifact_errors)
            raise ValueError("; ".join(artifact_errors))

        do_persist = self._persist if persist is None else persist
        log_event(
            "decision_issued",
            decision_id=artifact.decision_id,
            subject=artifact.subject,
            verdict=artifact.verdict.value,
            confidence=artifact.confidence,
            evidence_packet_id=artifact.evidence_packet_id,
        )
        if do_persist:
            try:
                save_decision(artifact)
            except ImmutableDecisionError:
                logger.error("immutable decision history violation for %s", artifact.decision_id)
                raise
            except Exception as exc:
                logger.warning("decision persist failed: %s", exc)
        return artifact


def default_decision_engine(*, persist: bool = True) -> DecisionEngine:
    return DecisionEngine(persist=persist)
