"""End-of-day pipeline: validate → learn → tune thresholds → notify."""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.suggestion_learning import LearningReport, build_learning_report
from analyzer.suggestion_validator import validate_pending_suggestions
from analyzer.telegram_notify import (
    format_track_record_telegram,
    send_telegram_broadcast,
    telegram_configured,
)
from analyzer.threshold_tuning import TuningResult, apply_threshold_tuning


@dataclass
class EodLearningResult:
    validated: int = 0
    errors: int = 0
    report: LearningReport | None = None
    tuning: TuningResult | None = None
    telegram_sent: bool = False
    telegram_error: str = ""
    insights: list[str] = field(default_factory=list)


def run_eod_learning_cycle(*, send_telegram_alert: bool = True) -> EodLearningResult:
    """
    Full post-close loop:
    1. Score pending suggestions vs market
    2. Build learning report
    3. Auto-tune Pulse score thresholds
    4. Optional Telegram scorecard
    """
    validation = validate_pending_suggestions()
    report = build_learning_report()
    tuning = apply_threshold_tuning(report)

    result = EodLearningResult(
        validated=validation["validated"],
        errors=validation["errors"],
        report=report,
        tuning=tuning,
        insights=list(report.insights),
    )

    if send_telegram_alert and telegram_configured():
        msg = format_track_record_telegram(report, tuning, validation)
        ok, err = send_telegram_broadcast(msg, alert_type="eod")
        result.telegram_sent = ok
        result.telegram_error = err if not ok else ""

    return result
