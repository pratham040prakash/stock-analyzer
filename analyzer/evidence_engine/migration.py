"""Migration adapters — legacy analyzer outputs → EvidenceItems."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.evidence_engine.builder import EvidenceBuilder
from analyzer.evidence_engine.engine import EvidenceEngine, default_engine
from analyzer.evidence_engine.models import (
    EvidenceCategory,
    EvidenceConfidence,
    EvidenceItem,
    EvidencePacket,
    EvidenceSource,
    EvidenceType,
    RecommendationFromEvidence,
)

IST = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)

_PILLAR_CATEGORY: dict[str, EvidenceCategory] = {
    "timing": EvidenceCategory.EXECUTION,
    "or_gate": EvidenceCategory.EXECUTION,
    "mtf": EvidenceCategory.TECHNICAL,
    "intraday": EvidenceCategory.TECHNICAL,
    "short_term": EvidenceCategory.TECHNICAL,
    "regime": EvidenceCategory.MARKET,
    "sector": EvidenceCategory.MARKET,
    "macro": EvidenceCategory.MACRO,
    "global": EvidenceCategory.MACRO,
    "checklist": EvidenceCategory.RISK,
    "plan": EvidenceCategory.EXECUTION,
    "flow": EvidenceCategory.OPTIONS,
    "reversal": EvidenceCategory.TECHNICAL,
    "iv": EvidenceCategory.OPTIONS,
}


def _builder() -> EvidenceBuilder:
    return EvidenceBuilder()


def evidence_from_strategy_votes(votes) -> list[EvidenceItem]:
    """Convert StrategyVote pillars to EvidenceItems."""
    b = _builder()
    items: list[EvidenceItem] = []
    for v in votes:
        cat = _PILLAR_CATEGORY.get(v.pillar, EvidenceCategory.TECHNICAL)
        items.append(
            b.build(
                category=cat,
                label=f"{v.pillar} signal",
                type=EvidenceType.ESTIMATE,
                value=v.detail[:200],
                explanation=v.detail,
                source=EvidenceSource.INTERNAL_MODEL,
                confidence=EvidenceConfidence.MEDIUM if abs(v.vote) < 1.0 else EvidenceConfidence.HIGH,
                weight=v.weight,
                metadata={"vote": v.vote, "pillar": v.pillar, "category": v.category},
            )
        )
    return items


def evidence_from_combined(combined) -> list[EvidenceItem]:
    """Convert CombinedResult to EvidenceItems."""
    b = _builder()
    items: list[EvidenceItem] = []
    tech = combined.technical
    fund = combined.fundamental

    items.append(
        b.estimate(
            category=EvidenceCategory.TECHNICAL,
            label="Technical composite score",
            value=tech.composite_score,
            explanation=f"Technical recommendation: {tech.recommendation}",
            source=EvidenceSource.INTERNAL_MODEL,
            confidence=EvidenceConfidence.MEDIUM,
            weight=combined.technical_weight,
            metadata={"score": tech.composite_score, "signal": _rec_to_signal(tech.recommendation)},
        )
    )
    items.append(
        b.estimate(
            category=EvidenceCategory.FUNDAMENTAL,
            label="Fundamental composite score",
            value=fund.composite_score,
            explanation=f"Fundamental recommendation: {fund.recommendation}",
            source=EvidenceSource.INTERNAL_MODEL,
            confidence=EvidenceConfidence.MEDIUM,
            weight=combined.fundamental_weight,
            metadata={"score": fund.composite_score, "signal": _rec_to_signal(fund.recommendation)},
        )
    )
    items.append(
        b.estimate(
            category=EvidenceCategory.TECHNICAL,
            label="Combined recommendation",
            value=combined.combined_recommendation,
            explanation=f"Weighted score {combined.combined_score}",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"score": combined.combined_score, "signal": _rec_to_signal(combined.combined_recommendation)},
        )
    )

    for sig in getattr(tech, "signals", []) or []:
        items.append(
            b.build(
                category=EvidenceCategory.TECHNICAL,
                label=sig.name,
                type=EvidenceType.ESTIMATE,
                value=sig.signal,
                explanation=sig.detail,
                source=EvidenceSource.INTERNAL_MODEL,
                confidence=EvidenceConfidence.MEDIUM,
                weight=0.5,
                metadata={"vote": sig.score, "signal": sig.signal},
            )
        )

    for m in getattr(fund, "metrics", []) or []:
        items.append(
            b.build(
                category=EvidenceCategory.FUNDAMENTAL,
                label=m.name,
                type=EvidenceType.FACT if m.value != "N/A" else EvidenceType.GAP,
                value=m.value,
                explanation=m.detail,
                source=EvidenceSource.YAHOO_FINANCE,
                confidence=EvidenceConfidence.MEDIUM,
                weight=0.4,
                metadata={"vote": m.score, "signal": m.signal},
            )
        )
    return items


def _rec_to_signal(rec: str) -> str:
    r = rec.upper()
    if "BUY" in r or "ACCUMULATE" in r:
        return "bullish"
    if "SELL" in r or "AVOID" in r or "REDUCE" in r:
        return "bearish"
    return "neutral"


def evidence_from_advice(advice) -> list[EvidenceItem]:
    """Convert InvestmentAdvice to EvidenceItems."""
    b = _builder()
    items = [
        b.opinion(
            category=EvidenceCategory.TECHNICAL,
            label="Final action",
            value=advice.final_action,
            explanation=advice.summary or advice.final_action,
            confidence=_conviction_to_confidence(advice.conviction),
            weight=1.5,
            metadata={"signal": _rec_to_signal(advice.final_action)},
        ),
        b.estimate(
            category=EvidenceCategory.EXECUTION,
            label="Entry zone",
            value=advice.entry_zone,
            explanation="Suggested entry from advisor",
            weight=0.8,
        ),
        b.estimate(
            category=EvidenceCategory.RISK,
            label="Stop loss",
            value=advice.stop_loss,
            explanation="Risk boundary from advisor",
            weight=1.0,
        ),
        b.estimate(
            category=EvidenceCategory.EXECUTION,
            label="Target",
            value=advice.target,
            explanation=f"Risk/reward {advice.risk_reward}",
            weight=0.8,
        ),
    ]
    for factor in advice.bullish_factors[:5]:
        items.append(
            b.opinion(
                category=EvidenceCategory.TECHNICAL,
                label="Bullish factor",
                value=factor[:120],
                explanation=factor,
                weight=0.5,
                metadata={"signal": "bullish"},
            )
        )
    for factor in advice.bearish_factors[:5]:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Bearish factor",
                value=factor[:120],
                explanation=factor,
                weight=0.5,
                metadata={"signal": "bearish"},
            )
        )
    for risk in advice.risks[:5]:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Risk",
                value=risk[:120],
                explanation=risk,
                weight=0.6,
                metadata={"signal": "bearish"},
            )
        )
    return items


def _conviction_to_confidence(conviction: str) -> EvidenceConfidence:
    c = conviction.lower()
    if c == "high":
        return EvidenceConfidence.HIGH
    if c == "low":
        return EvidenceConfidence.LOW
    return EvidenceConfidence.MEDIUM


def evidence_from_data_health(health) -> list[EvidenceItem]:
    """Convert DataHealth to EvidenceItems."""
    b = _builder()
    items = [
        b.fact(
            category=EvidenceCategory.MARKET,
            label="Primary data source",
            value=health.primary,
            explanation=health.detail or health.primary,
            source=EvidenceSource.DATA_HEALTH,
            confidence=EvidenceConfidence.HIGH,
        ),
        b.fact(
            category=EvidenceCategory.EXECUTION,
            label="Live cockpit ready",
            value=health.ok_for_live_cockpit,
            explanation="Whether live Kite quotes are available for cockpit",
            source=EvidenceSource.DATA_HEALTH,
            confidence=EvidenceConfidence.HIGH,
        ),
    ]
    if health.warning:
        items.append(
            b.build(
                category=EvidenceCategory.MARKET,
                label="Data health warning",
                type=EvidenceType.GAP,
                value=health.warning,
                explanation=health.warning,
                source=EvidenceSource.DATA_HEALTH,
                confidence=EvidenceConfidence.NONE,
                weight=1.2,
            )
        )
    return items


def evidence_from_data_gaps(gaps: list[str]) -> list[EvidenceItem]:
    b = _builder()
    return [
        b.gap(
            category=EvidenceCategory.FUNDAMENTAL,
            label=f"Data gap {idx + 1}",
            explanation=g[:200],
            source=EvidenceSource.UNKNOWN,
        )
        for idx, g in enumerate(gaps[:12])
    ]


def evidence_from_relative_strength(rs) -> list[EvidenceItem]:
    if rs is None:
        return []
    b = _builder()
    return [
        b.fact(
            category=EvidenceCategory.MARKET,
            label="Relative strength vs benchmark",
            value=rs.verdict,
            explanation=rs.detail,
            source=EvidenceSource.YAHOO_FINANCE,
            metadata={"score": rs.rs_score, "signal": _rec_to_signal(rs.verdict)},
        )
    ]


def evidence_from_market_pulse(pulse) -> list[EvidenceItem]:
    if pulse is None:
        return []
    b = _builder()
    items = []
    if getattr(pulse, "market_verdict", None):
        items.append(
            b.estimate(
                category=EvidenceCategory.MARKET,
                label="Market verdict",
                value=pulse.market_verdict,
                explanation="India market pulse aggregate",
                source=EvidenceSource.MACRO_FEED,
                metadata={"signal": _rec_to_signal(pulse.market_verdict)},
            )
        )
    if getattr(pulse, "regime", None):
        reg = pulse.regime
        items.append(
            b.estimate(
                category=EvidenceCategory.MARKET,
                label="Market regime",
                value=reg.regime,
                explanation=getattr(reg, "banner", reg.regime),
                source=EvidenceSource.INTERNAL_MODEL,
            )
        )
    return items


def build_synthesis_packet(
    target: str,
    asset_class: str,
    votes,
    *,
    engine: EvidenceEngine | None = None,
    context_snapshot=None,
) -> tuple[EvidencePacket, RecommendationFromEvidence]:
    """Build packet from strategy votes; derive recommendation from packet only."""
    eng = engine or default_engine()
    items = evidence_from_strategy_votes(votes)
    snapshot_id = ""
    if context_snapshot is not None:
        try:
            from analyzer.context_engine.migration import evidence_items_from_snapshot

            items = evidence_items_from_snapshot(context_snapshot) + items
            snapshot_id = context_snapshot.snapshot_id
        except Exception:
            pass
    packet = eng.build_packet(
        subject=target,
        subject_type=asset_class,
        items=items,
        metadata={
            "origin": "strategy_synthesis",
            "context_snapshot_id": snapshot_id or None,
        },
    )
    rec = eng.recommend_from_packet(packet)
    return packet, rec


def build_equity_research_packet(
    symbol: str,
    *,
    combined=None,
    advice=None,
    gaps: list[str] | None = None,
    rs=None,
    market_pulse=None,
    data_health=None,
    engine: EvidenceEngine | None = None,
) -> EvidencePacket:
    """Assemble research evidence for Alpha AI / advisor."""
    eng = engine or default_engine()
    items: list[EvidenceItem] = []
    if combined is not None:
        items.extend(evidence_from_combined(combined))
    if advice is not None:
        items.extend(evidence_from_advice(advice))
    if gaps:
        items.extend(evidence_from_data_gaps(gaps))
    if rs is not None:
        items.extend(evidence_from_relative_strength(rs))
    if market_pulse is not None:
        items.extend(evidence_from_market_pulse(market_pulse))
    if data_health is not None:
        items.extend(evidence_from_data_health(data_health))

    return eng.build_packet(
        subject=symbol,
        subject_type="research",
        items=items,
        metadata={"origin": "alpha_ai_research"},
    )


def attach_synthesis_evidence(synthesis) -> None:
    """Mutate StrategySynthesis in-place with evidence_packet from pillars."""
    try:
        context_snapshot = None
        try:
            from analyzer.context_engine import build_context_snapshot

            context_snapshot = build_context_snapshot(use_cache=True)
        except Exception:
            pass
        packet, rec = build_synthesis_packet(
            synthesis.target,
            synthesis.asset_class,
            synthesis.pillars,
            context_snapshot=context_snapshot,
        )
        synthesis.evidence_packet = packet
        synthesis.recommendation_from_evidence = rec
    except Exception as exc:
        logger.warning("evidence synthesis attach failed: %s", exc)
        synthesis.evidence_packet = None
        synthesis.recommendation_from_evidence = None
