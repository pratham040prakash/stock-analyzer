"""Generic log parsing for contact-center style investigation logs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

# Common timestamp patterns in telephony / app logs
_TS_PATTERNS = [
    re.compile(
        r"(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:?\d{2})?)"
    ),
    re.compile(r"(?P<ts>\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}(?:\.\d{3})?)"),
    re.compile(r"(?P<ts>\d{2}:\d{2}:\d{2}(?:\.\d{3})?)"),
]

_STAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "customer": ("customer", "caller", "ani", "dnis", "inbound call"),
    "carrier": ("carrier", "pstn", "trunk", "sip trunk"),
    "sbc": ("sbc", "session border", "border controller"),
    "ivr": ("ivr", "menu", "prompt", "dtmf", "self-service"),
    "routing": ("routing", "route", "dialed", "script", "flow"),
    "queue": ("queue", "ewt", "skill", "overflow", "waiting", "acd"),
    "agent": ("agent", "answered", "wrap", "not ready", "available"),
    "desktop": ("desktop", "browser", "javascript", "bundle", "finesse", "cti"),
    "recording": ("recording", "recorder", "media stream", "rtp", "packet loss", "codec"),
    "crm": ("crm", "salesforce", "case", "api timeout", "rest ", "graphql"),
    "disconnect": ("disconnect", "hangup", "bye", "terminated", "ended", "abandoned"),
}

_ERROR_KEYWORDS = (
    "error",
    "fail",
    "failed",
    "exception",
    "timeout",
    "refused",
    "unavailable",
    "mismatch",
    "degraded",
    "critical",
    "warn",
    "warning",
)


@dataclass
class LogEvent:
    line_no: int
    raw: str
    timestamp: datetime | None
    stage: str | None
    severity: str
    message: str


@dataclass
class ParseResult:
    events: list[LogEvent] = field(default_factory=list)
    interaction_ids: list[str] = field(default_factory=list)
    error_count: int = 0


def _parse_timestamp(text: str) -> datetime | None:
    for pattern in _TS_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        raw = match.group("ts")
        normalized = raw.replace(" ", "T") if " " in raw and "T" not in raw else raw
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S.%f",
            "%m/%d/%Y %H:%M:%S",
            "%H:%M:%S.%f",
            "%H:%M:%S",
        ):
            try:
                parsed = datetime.strptime(normalized.replace("Z", ""), fmt.replace("Z", ""))
                return parsed
            except ValueError:
                continue
    return None


def _keyword_matches(line_lower: str, keyword: str) -> bool:
    """Match whole words for short tokens that appear inside other words (e.g. script/javascript)."""
    if " " in keyword or len(keyword) <= 4:
        return keyword in line_lower
    return bool(re.search(rf"\b{re.escape(keyword)}\b", line_lower))


def _detect_stage(line_lower: str) -> str | None:
    # Prefer later journey stages when multiple keywords match (more specific hop).
    for stage in reversed(list(_STAGE_KEYWORDS.keys())):
        keywords = _STAGE_KEYWORDS[stage]
        if any(_keyword_matches(line_lower, kw) for kw in keywords):
            return stage
    return None


def _detect_severity(line_lower: str) -> str:
    if any(k in line_lower for k in ("critical", "fatal", "severe")):
        return "critical"
    if any(k in line_lower for k in ("error", "fail", "exception", "refused")):
        return "error"
    if any(k in line_lower for k in ("warn", "degraded", "timeout")):
        return "warning"
    return "info"


def _extract_interaction_ids(text: str) -> list[str]:
    patterns = [
        r"(?:interaction|call|contact|session)[\s_-]?id[=:\s]+([a-zA-Z0-9_-]{8,})",
        r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b",
        r"\b(\d{15,20})\b",
    ]
    found: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            found.add(match.group(1))
    return sorted(found)


def parse_logs(text: str) -> ParseResult:
    """Parse raw log text into structured events."""
    events: list[LogEvent] = []
    error_count = 0
    lines = text.splitlines()

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lower = stripped.lower()
        severity = _detect_severity(lower)
        if severity in {"error", "critical", "warning"}:
            error_count += 1
        events.append(
            LogEvent(
                line_no=idx,
                raw=stripped,
                timestamp=_parse_timestamp(stripped),
                stage=_detect_stage(lower),
                severity=severity,
                message=stripped,
            )
        )

    return ParseResult(
        events=events,
        interaction_ids=_extract_interaction_ids(text),
        error_count=error_count,
    )


def merge_log_sources(sources: Iterable[str]) -> str:
    return "\n".join(s for s in sources if s and s.strip())
