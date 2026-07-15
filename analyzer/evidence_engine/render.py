"""Render EvidencePacket sections for Alpha AI and UI."""

from __future__ import annotations

from analyzer.evidence_engine.models import EvidenceCategory, EvidencePacket, EvidenceType


def format_evidence_summary(packet: EvidencePacket) -> str:
    """Executive evidence block — labeled claims only."""
    lines = [
        f"**Evidence packet** `{packet.packet_id}` · completeness {packet.completeness_pct:.0f}%",
        f"Categories: {', '.join(packet.categories_present) or 'none'}",
    ]
    if packet.conflicts:
        lines.append(f"**Conflicts ({len(packet.conflicts)}):**")
        for c in packet.conflicts[:5]:
            lines.append(f"- [{c.severity}] {c.description}")
    if packet.gaps:
        lines.append(f"**Gaps ({len(packet.gaps)}):**")
        for g in packet.gaps[:6]:
            lines.append(f"- **GAP** · {g.category.value} · {g.label}: {g.explanation}")
    return "\n".join(lines)


def format_evidence_category(packet: EvidencePacket, category: EvidenceCategory) -> str:
    items = packet.items_by_category(category)
    if not items:
        return f"### {category.value}\n\n*No evidence in this category.*"
    lines = [f"### {category.value}", ""]
    for item in items:
        type_tag = item.type.value
        val = item.value if item.value is not None else "—"
        lines.append(
            f"- **{type_tag}** · {item.label} = `{val}` "
            f"({item.confidence.value}, w={item.weight:.1f}) — {item.explanation}"
        )
    return "\n".join(lines)


def format_evidence_report(packet: EvidencePacket) -> str:
    """Full markdown evidence section for Alpha AI."""
    parts = [format_evidence_summary(packet), ""]
    seen: set[str] = set()
    for item in packet.items:
        cat = item.category.value
        if cat in seen:
            continue
        seen.add(cat)
        parts.append(format_evidence_category(packet, item.category))
        parts.append("")
    return "\n".join(parts).strip()


def render_recommendation_rationale(packet: EvidencePacket) -> tuple[list[str], list[str]]:
    """Positives/negatives from packet for recommendation display."""
    positives: list[str] = []
    negatives: list[str] = []
    for item in packet.items:
        if item.type == EvidenceType.GAP:
            negatives.append(f"GAP: {item.label}")
            continue
        vote = item.metadata.get("vote")
        if vote is not None:
            try:
                v = float(vote)
                line = f"{item.label}: {item.explanation[:100]}"
                if v > 0.3:
                    positives.append(line)
                elif v < -0.3:
                    negatives.append(line)
            except (TypeError, ValueError):
                pass
        elif item.type in (EvidenceType.FACT, EvidenceType.ESTIMATE):
            sig = str(item.metadata.get("signal", "")).lower()
            line = f"[{item.type.value}] {item.label}: {item.explanation[:100]}"
            if sig == "bullish":
                positives.append(line)
            elif sig == "bearish":
                negatives.append(line)
    for c in packet.conflicts:
        negatives.append(f"Conflict: {c.description[:100]}")
    return positives[:8], negatives[:8]
