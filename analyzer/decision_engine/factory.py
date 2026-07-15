"""Decision factory — assembles DecisionArtifact; verdict supplied by DecisionEngine only."""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.decision_engine.models import (
    DECISION_VERSION,
    DecisionArtifact,
    DecisionContext,
    DecisionExplainability,
    DecisionVerdict,
    UncertaintyVector,
)
from analyzer.decision_engine.reasoner import EvidenceScore
from analyzer.evidence_engine.models import EvidencePacket

IST = ZoneInfo("Asia/Kolkata")


class DecisionFactory:
    """Step 8 — assemble canonical DecisionArtifact with explainability."""

    def build(
        self,
        *,
        packet: EvidencePacket,
        subject_type: str,
        context: DecisionContext,
        evidence_score: EvidenceScore,
        verdict: DecisionVerdict,
        reason: str,
        confidence: float,
        uncertainty: UncertaintyVector,
        trade_allowed: bool,
        alternative_actions: list[str],
        invalidation_conditions: list[str],
        warnings: list[str],
    ) -> DecisionArtifact:
        explain = self._explainability(
            verdict=verdict,
            reason=reason,
            packet=packet,
            context=context,
            evidence_score=evidence_score,
            alternative_actions=alternative_actions,
        )
        return DecisionArtifact(
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
            verdict=verdict,
            reason=reason,
            evidence_packet_id=packet.packet_id,
            confidence=confidence,
            uncertainty=uncertainty,
            capital_recommendation=self._capital_recommendation(verdict, context, confidence),
            execution_recommendation=self._execution_recommendation(verdict, context, packet),
            supporting_evidence_ids=evidence_score.supporting_ids,
            conflicting_evidence_ids=evidence_score.conflicting_ids,
            alternative_actions=alternative_actions,
            invalidation_conditions=invalidation_conditions,
            explainability=explain,
            decision_version=DECISION_VERSION,
            subject=packet.subject,
            subject_type=subject_type,
            trade_allowed=trade_allowed,
            net_score=evidence_score.net,
            metadata={"warning_count": len(warnings), "gap_count": packet.gap_count},
        )

    def build_deterministic(
        self,
        *,
        packet: EvidencePacket,
        subject_type: str,
        verdict: DecisionVerdict,
        reason: str,
        explainability: DecisionExplainability,
        uncertainty: UncertaintyVector,
        capital_recommendation: str,
        execution_recommendation: str,
        alternative_actions: list[str],
        invalidation_conditions: list[str],
        metadata: dict | None = None,
        trade_allowed: bool = False,
        confidence: float = 0.0,
        net_score: float = 0.0,
    ) -> DecisionArtifact:
        """Assemble artifact for engine-determined verdicts (gap/validation paths)."""
        return DecisionArtifact(
            decision_id=f"dec_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
            verdict=verdict,
            reason=reason,
            evidence_packet_id=packet.packet_id,
            confidence=confidence,
            uncertainty=uncertainty,
            capital_recommendation=capital_recommendation,
            execution_recommendation=execution_recommendation,
            supporting_evidence_ids=[],
            conflicting_evidence_ids=[],
            alternative_actions=alternative_actions,
            invalidation_conditions=invalidation_conditions,
            explainability=explainability,
            decision_version=DECISION_VERSION,
            subject=packet.subject,
            subject_type=subject_type,
            trade_allowed=trade_allowed,
            net_score=net_score,
            metadata=metadata or {},
        )

    def _explainability(
        self,
        *,
        verdict: DecisionVerdict,
        reason: str,
        packet: EvidencePacket,
        context: DecisionContext,
        evidence_score: EvidenceScore,
        alternative_actions: list[str],
    ) -> DecisionExplainability:
        support = evidence_score.supporting_ids[:3]
        conflict = evidence_score.conflicting_ids[:3]
        why = reason
        why_now_parts = []
        if context.market.timing_headline:
            why_now_parts.append(context.market.timing_headline)
        if context.market.regime:
            why_now_parts.append(f"Regime: {context.market.regime}")
        why_now_parts.append(f"Evidence net {evidence_score.net:+.2f}")
        why_now = " — ".join(why_now_parts) if why_now_parts else f"Verdict {verdict.value} from current evidence"

        why_not_parts = []
        if alternative_actions:
            why_not_parts.append(f"Alternatives: {', '.join(alternative_actions[:3])}")
        if conflict:
            why_not_parts.append(f"Conflicts: {len(conflict)} evidence item(s)")
        if packet.gap_count:
            why_not_parts.append(f"{packet.gap_count} gap(s) in packet")
        why_not = "; ".join(why_not_parts) if why_not_parts else "No stronger alternative under current constraints"
        if support:
            why = f"{reason} (supported by {len(support)} evidence item(s))"
        return DecisionExplainability(why=why, why_now=why_now, why_not=why_not)

    def _capital_recommendation(
        self,
        verdict: DecisionVerdict,
        context: DecisionContext,
        confidence: float,
    ) -> str:
        risk_inr = round(context.capital.capital_inr * context.capital.max_risk_pct / 100)
        alloc = context.capital.allocation_pct
        if verdict == DecisionVerdict.ACT:
            size = "1 lot" if context.preferences.beginner_mode else "plan-sized"
            return (
                f"Risk ≤ ₹{risk_inr:,} ({context.capital.max_risk_pct:.1f}% of "
                f"₹{context.capital.capital_inr:,.0f}), {size}, alloc {alloc:.0f}%"
            )
        if verdict == DecisionVerdict.REDUCE:
            return f"Trim toward ≤ {context.capital.max_risk_pct:.1f}% risk budget; do not add"
        if verdict == DecisionVerdict.DEFENSIVE:
            return "Preserve capital; no new risk beyond existing stops"
        if verdict == DecisionVerdict.PASS:
            return "Zero new capital deployment"
        return f"Hold fire — max risk ₹{risk_inr:,} reserved; confidence {confidence:.0f}%"

    def _execution_recommendation(
        self,
        verdict: DecisionVerdict,
        context: DecisionContext,
        packet: EvidencePacket,
    ) -> str:
        if verdict == DecisionVerdict.ACT:
            gate = "after OR gate" if packet.subject_type in ("equity", "options") else "on plan"
            return f"Enter {gate}; hard stop mandatory; respect session timing"
        if verdict == DecisionVerdict.WAIT:
            return "No entry — monitor triggers; reassess each session"
        if verdict == DecisionVerdict.PASS:
            return "No trade — remove from active watch until evidence improves"
        if verdict == DecisionVerdict.REDUCE:
            return "Scale down or tighten stops on existing position"
        return "Defensive posture — widen cash buffer, review gaps in evidence"
