"""Decision reasoner — evidence scoring and verdict resolution."""

from __future__ import annotations

from analyzer.decision_engine.models import (
    DecisionContext,
    DecisionVerdict,
    UncertaintyVector,
)
from analyzer.decision_engine.rules import (
    ACT_CONFIDENCE,
    ACT_NET_THRESHOLD,
    PASS_NET_THRESHOLD,
    REDUCE_NET_THRESHOLD,
    STRONG_ACT_CONFIDENCE,
    STRONG_ACT_NET_THRESHOLD,
)
from analyzer.evidence_engine.models import EvidencePacket, EvidenceType


class EvidenceScore:
    def __init__(self, net: float, scored: list[tuple[str, str, float]]):
        self.net = net
        self.scored = scored
        self.supporting_ids: list[str] = []
        self.conflicting_ids: list[str] = []


class DecisionReasoner:
    """Steps 4–7: risk, capital, portfolio evaluation and verdict selection."""

    def score_packet(self, packet: EvidencePacket) -> EvidenceScore:
        scored: list[tuple[str, str, float]] = []
        for item in packet.items:
            if item.type == EvidenceType.GAP:
                continue
            vote = item.metadata.get("vote")
            if vote is not None:
                try:
                    scored.append((item.id, item.label, float(vote) * item.weight))
                    continue
                except (TypeError, ValueError):
                    pass
            score = item.metadata.get("score")
            if score is not None:
                try:
                    scored.append((item.id, item.label, float(score) * item.weight * 0.01))
                    continue
                except (TypeError, ValueError):
                    pass
            sig = str(item.metadata.get("signal", "")).lower()
            if sig == "bullish":
                scored.append((item.id, item.label, 0.5 * item.weight))
            elif sig == "bearish":
                scored.append((item.id, item.label, -0.5 * item.weight))

        total_w = sum(abs(v) for _, _, v in scored) or 1.0
        net = round(sum(v for _, _, v in scored) / total_w, 3)
        result = EvidenceScore(net, scored)
        result.supporting_ids = [iid for iid, _, v in scored if v > 0.2]
        for conflict in packet.conflicts:
            result.conflicting_ids.extend(conflict.item_ids)
        result.conflicting_ids = list(dict.fromkeys(result.conflicting_ids))
        return result

    def risk_block(
        self,
        packet: EvidencePacket,
        context: DecisionContext,
        net: float,
    ) -> tuple[bool, str]:
        if context.risk.loss_streak_days >= context.risk.max_loss_streak_before_pause:
            return True, f"{context.risk.loss_streak_days} loss days — pause new risk"
        if any(c.severity == "high" for c in packet.conflicts):
            return True, "High-severity evidence conflicts"
        if not context.market.allow_new_entries:
            return True, context.market.timing_headline or "New entries blocked"
        if context.risk.require_gate_green and not context.risk.gate_allowed:
            return True, "Entry gate not green"
        if net < -0.5:
            return True, "Strong negative evidence net"
        return False, ""

    def capital_block(self, context: DecisionContext) -> tuple[bool, str]:
        if not context.portfolio.known:
            return True, "Portfolio state unknown"
        if context.portfolio.open_positions >= context.capital.max_trades:
            return True, f"Max concurrent trades ({context.capital.max_trades}) reached"
        if context.capital.daily_loss_cap_inr is not None and context.capital.daily_loss_cap_inr <= 0:
            return True, "Daily loss cap exhausted"
        if context.capital.capital_inr <= 0:
            return True, "Capital constraints invalid"
        return False, ""

    def confidence(
        self,
        net: float,
        scored: list[tuple[str, str, float]],
        packet: EvidencePacket,
        uncertainty_overall: float,
    ) -> float:
        agree_pos = sum(1 for _, _, v in scored if v > 0.2)
        agree_neg = sum(1 for _, _, v in scored if v < -0.2)
        base = 50.0 + net * 22.0 + min(agree_pos * 4, 20) - min(agree_neg * 6, 30)
        base -= len(packet.conflicts) * 6
        base -= packet.gap_count * 3
        base -= uncertainty_overall * 0.15
        return max(0.0, min(100.0, round(base, 1)))

    def resolve_verdict(
        self,
        *,
        net: float,
        confidence: float,
        packet: EvidencePacket,
        context: DecisionContext,
        risk_block: bool,
        risk_reason: str,
        capital_block: bool,
        capital_reason: str,
    ) -> tuple[DecisionVerdict, str, bool, list[str], list[str]]:
        invalidations = [
            c.description[:100] for c in packet.conflicts[:3]
        ] + [g.explanation[:100] for g in packet.gaps[:2]]

        if capital_block:
            return (
                DecisionVerdict.WAIT,
                capital_reason,
                False,
                ["PASS", "DEFENSIVE"],
                invalidations,
            )
        if risk_block:
            if net < PASS_NET_THRESHOLD:
                return (
                    DecisionVerdict.PASS,
                    risk_reason,
                    False,
                    ["WAIT", "DEFENSIVE"],
                    invalidations,
                )
            return (
                DecisionVerdict.WAIT,
                risk_reason,
                False,
                ["PASS", "DEFENSIVE"],
                invalidations,
            )
        cautious = (
            not context.market.allow_aggressive
            or context.preferences.beginner_mode
        )
        if cautious:
            if net >= ACT_NET_THRESHOLD and confidence >= 60:
                return (
                    DecisionVerdict.ACT,
                    "Aligned signals — act with reduced size in cautious regime",
                    confidence >= ACT_CONFIDENCE,
                    ["WAIT"],
                    invalidations,
                )
            if net < REDUCE_NET_THRESHOLD:
                return (
                    DecisionVerdict.DEFENSIVE,
                    "Cautious regime — preserve capital",
                    False,
                    ["PASS", "WAIT"],
                    invalidations,
                )
            return (
                DecisionVerdict.WAIT,
                "Cautious regime — default wait",
                False,
                ["DEFENSIVE", "ACT"],
                invalidations,
            )
        if net < PASS_NET_THRESHOLD:
            return (
                DecisionVerdict.PASS,
                "Negative evidence net — no trade",
                False,
                ["REDUCE", "DEFENSIVE"],
                invalidations,
            )
        if net < REDUCE_NET_THRESHOLD:
            return (
                DecisionVerdict.REDUCE,
                "Lean negative — reduce or avoid adds",
                False,
                ["PASS", "WAIT"],
                invalidations,
            )
        if net >= STRONG_ACT_NET_THRESHOLD and confidence >= STRONG_ACT_CONFIDENCE:
            return (
                DecisionVerdict.ACT,
                "Strong alignment — act with plan and stop",
                True,
                ["WAIT", "DEFENSIVE"],
                invalidations,
            )
        if net >= ACT_NET_THRESHOLD and confidence >= ACT_CONFIDENCE:
            return (
                DecisionVerdict.ACT,
                "Positive alignment — act with defined risk",
                confidence >= ACT_CONFIDENCE,
                ["WAIT", "PASS"],
                invalidations,
            )
        if net >= 0.1:
            return (
                DecisionVerdict.WAIT,
                "Mixed signals — wait for confirmation",
                False,
                ["ACT", "PASS"],
                invalidations,
            )
        return (
            DecisionVerdict.WAIT,
            "Insufficient alignment — default wait",
            False,
            ["PASS", "DEFENSIVE"],
            invalidations,
        )

    def compute_uncertainty(
        self,
        packet: EvidencePacket,
        context: DecisionContext,
        warnings: list[str],
    ) -> UncertaintyVector:
        completeness_unc = max(0.0, 100.0 - packet.completeness_pct)
        conflict_unc = min(100.0, len(packet.conflicts) * 20.0)
        gap_unc = min(100.0, packet.gap_count * 12.0)
        data_quality = min(100.0, gap_unc + len(warnings) * 15.0)
        regime_risk = 70.0 if not context.market.allow_aggressive else 30.0
        if not context.market.allow_new_entries:
            regime_risk = min(100.0, regime_risk + 40.0)
        if not context.market.session_open:
            regime_risk = min(100.0, regime_risk + 30.0)
        headroom = 100.0
        if context.portfolio.open_positions >= context.capital.max_trades:
            headroom = 90.0
        elif context.portfolio.open_positions > 0:
            headroom = 40.0 + context.portfolio.open_positions * 10.0
        overall = min(
            100.0,
            (
                completeness_unc * 0.25
                + conflict_unc * 0.25
                + data_quality * 0.2
                + regime_risk * 0.2
                + headroom * 0.1
            ),
        )
        return UncertaintyVector(
            evidence_completeness=completeness_unc,
            conflict_level=conflict_unc,
            data_quality=data_quality,
            regime_risk=regime_risk,
            capital_headroom=headroom,
            overall=overall,
        )
