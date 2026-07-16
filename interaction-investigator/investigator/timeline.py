"""Build a vertical interaction journey from parsed log events."""

from __future__ import annotations

from dataclasses import dataclass, field

from investigator.parser import LogEvent, ParseResult

JOURNEY_STAGES = [
    "customer",
    "carrier",
    "sbc",
    "ivr",
    "routing",
    "queue",
    "agent",
    "desktop",
    "recording",
    "crm",
    "disconnect",
]

_STAGE_LABELS = {
    "customer": "Customer",
    "carrier": "Carrier",
    "sbc": "SBC",
    "ivr": "IVR",
    "routing": "Routing",
    "queue": "Queue",
    "agent": "Agent",
    "desktop": "Desktop",
    "recording": "Recording",
    "crm": "CRM",
    "disconnect": "Disconnect",
}


@dataclass
class StageSummary:
    stage: str
    label: str
    status: str  # healthy | warning | failed | unknown
    event_count: int
    error_count: int
    warning_count: int
    first_seen: str | None
    last_seen: str | None
    highlights: list[str] = field(default_factory=list)


@dataclass
class Timeline:
    stages: list[StageSummary]
    total_events: int
    total_errors: int
    interaction_ids: list[str]
    chronology: list[LogEvent]


def _stage_status(errors: int, warnings: int, events: int) -> str:
    if errors > 0:
        return "failed"
    if warnings > 0:
        return "warning"
    if events > 0:
        return "healthy"
    return "unknown"


def _fmt_ts(event: LogEvent) -> str | None:
    if not event.timestamp:
        return None
    return event.timestamp.strftime("%H:%M:%S.%f")[:-3]


def build_timeline(parsed: ParseResult) -> Timeline:
    by_stage: dict[str, list[LogEvent]] = {s: [] for s in JOURNEY_STAGES}
    unassigned: list[LogEvent] = []

    for event in parsed.events:
        if event.stage and event.stage in by_stage:
            by_stage[event.stage].append(event)
        else:
            unassigned.append(event)

    stages: list[StageSummary] = []
    for stage in JOURNEY_STAGES:
        items = by_stage[stage]
        errors = sum(1 for e in items if e.severity in {"error", "critical"})
        warnings = sum(1 for e in items if e.severity == "warning")
        highlights = [e.message[:160] for e in items if e.severity != "info"][:5]
        if not highlights and items:
            highlights = [items[0].message[:160]]

        timestamps = [e for e in items if e.timestamp]
        first_seen = _fmt_ts(timestamps[0]) if timestamps else None
        last_seen = _fmt_ts(timestamps[-1]) if timestamps else None

        stages.append(
            StageSummary(
                stage=stage,
                label=_STAGE_LABELS[stage],
                status=_stage_status(errors, warnings, len(items)),
                event_count=len(items),
                error_count=errors,
                warning_count=warnings,
                first_seen=first_seen,
                last_seen=last_seen,
                highlights=highlights,
            )
        )

    chronology = sorted(
        parsed.events,
        key=lambda e: (e.timestamp or e.line_no, e.line_no),
    )

    return Timeline(
        stages=stages,
        total_events=len(parsed.events),
        total_errors=parsed.error_count,
        interaction_ids=parsed.interaction_ids,
        chronology=chronology[:200],
    )
