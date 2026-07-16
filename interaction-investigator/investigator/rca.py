"""Root-cause analysis — rule-based fallback plus optional OpenAI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from investigator.timeline import Timeline

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


@dataclass
class RCAFinding:
    stage: str
    label: str
    confidence: str
    summary: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class RCAResult:
    primary_cause: RCAFinding | None
    hypotheses: list[RCAFinding]
    recommended_actions: list[str]
    customer_update_draft: str
    method: str  # rules | ai


def _rule_based_rca(timeline: Timeline, symptom: str) -> RCAResult:
    failed = [s for s in timeline.stages if s.status == "failed"]
    warned = [s for s in timeline.stages if s.status == "warning"]

    hypotheses: list[RCAFinding] = []
    for stage in failed + warned:
        confidence = "high" if stage.error_count else "medium"
        hypotheses.append(
            RCAFinding(
                stage=stage.stage,
                label=stage.label,
                confidence=confidence,
                summary=f"{stage.label} shows {stage.error_count} error(s) and {stage.warning_count} warning(s).",
                evidence=stage.highlights[:3],
            )
        )

    if not hypotheses:
        hypotheses.append(
            RCAFinding(
                stage="unknown",
                label="Inconclusive",
                confidence="low",
                summary="No clear failure stage detected. Review full chronology and verify log completeness.",
                evidence=[],
            )
        )

    primary = hypotheses[0]
    actions = [
        f"Inspect {primary.label} events first and validate timestamps against the reported symptom.",
        "Compare with a known-good interaction from the same time window.",
        "Check for recent deployments or configuration changes near the failure time.",
    ]
    if primary.stage == "desktop":
        actions.insert(0, "Validate agent desktop bundle/version and browser console errors.")
    if primary.stage == "recording":
        actions.insert(0, "Validate media path, RTP quality, and recorder service health.")
    if primary.stage == "crm":
        actions.insert(0, "Check CRM/API latency, auth tokens, and downstream database health.")

    customer_draft = (
        f"We investigated interaction logs for: {symptom or 'reported issue'}. "
        f"Initial analysis points to {primary.label} ({primary.confidence} confidence). "
        f"Next steps: {actions[0]}"
    )

    return RCAResult(
        primary_cause=primary,
        hypotheses=hypotheses[:5],
        recommended_actions=actions,
        customer_update_draft=customer_draft,
        method="rules",
    )


def _timeline_context(timeline: Timeline, symptom: str) -> str:
    stage_lines = []
    for s in timeline.stages:
        if s.event_count == 0:
            continue
        stage_lines.append(
            f"- {s.label}: status={s.status}, errors={s.error_count}, warnings={s.warning_count}, "
            f"samples={s.highlights[:2]}"
        )
    chronology = "\n".join(f"  {e.message[:200]}" for e in timeline.chronology[:40])
    return (
        f"Symptom: {symptom or 'not provided'}\n"
        f"Interaction IDs: {', '.join(timeline.interaction_ids) or 'none detected'}\n"
        f"Stage summary:\n" + "\n".join(stage_lines) + "\n"
        f"Chronology (sample):\n{chronology}"
    )


def _ai_rca(timeline: Timeline, symptom: str) -> RCAResult:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key or OpenAI is None:
        return _rule_based_rca(timeline, symptom)

    client = OpenAI(api_key=api_key)
    prompt = (
        "You are a senior contact-center escalation engineer. "
        "Analyze the timeline and return JSON only with keys: "
        "primary_cause {stage, label, confidence, summary, evidence[]}, "
        "hypotheses[] (same shape, max 5), recommended_actions[] (max 5), "
        "customer_update_draft (2-3 sentences, professional). "
        "Use stages: customer, carrier, sbc, ivr, routing, queue, agent, desktop, recording, crm, disconnect. "
        "Base conclusions on evidence only; say inconclusive if logs are insufficient.\n\n"
        + _timeline_context(timeline, symptom)
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return valid JSON only. No markdown."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        payload = json.loads(response.choices[0].message.content or "{}")
    except Exception:
        fallback = _rule_based_rca(timeline, symptom)
        fallback.recommended_actions.insert(
            0, "AI analysis unavailable — showing rule-based RCA. Check OPENAI_API_KEY."
        )
        return fallback

    def _finding(data: dict) -> RCAFinding:
        return RCAFinding(
            stage=str(data.get("stage", "unknown")),
            label=str(data.get("label", "Unknown")),
            confidence=str(data.get("confidence", "medium")),
            summary=str(data.get("summary", "")),
            evidence=[str(x) for x in data.get("evidence", [])][:5],
        )

    primary_raw = payload.get("primary_cause") or {}
    hypotheses_raw = payload.get("hypotheses") or []
    return RCAResult(
        primary_cause=_finding(primary_raw) if primary_raw else None,
        hypotheses=[_finding(h) for h in hypotheses_raw[:5]],
        recommended_actions=[str(a) for a in payload.get("recommended_actions", [])][:5],
        customer_update_draft=str(payload.get("customer_update_draft", "")),
        method="ai",
    )


def generate_rca(timeline: Timeline, symptom: str = "", use_ai: bool = True) -> RCAResult:
    if use_ai and os.getenv("OPENAI_API_KEY", "").strip():
        return _ai_rca(timeline, symptom)
    return _rule_based_rca(timeline, symptom)
