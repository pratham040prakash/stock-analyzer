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
    broker_sync: dict | None = None


def run_eod_learning_cycle(*, send_telegram_alert: bool = True) -> EodLearningResult:
    """
    Full post-close loop:
    1. Sync broker truth from Zerodha (executed trades)
    2. Score pending suggestions vs market
    3. Build learning report
    4. Auto-tune Pulse score thresholds
    5. Optional Telegram scorecard
    """
    broker_sync = None
    try:
        from analyzer.broker_truth.learning import sync_broker_truth_for_learning

        broker_sync = sync_broker_truth_for_learning()
    except Exception:
        pass

    validation = validate_pending_suggestions()
    report = build_learning_report()
    tuning = apply_threshold_tuning(report)

    insights = list(report.insights)
    if broker_sync and broker_sync.get("connected"):
        insights.insert(
            0,
            f"Broker truth: **{broker_sync.get('records', 0)}** completed trades "
            f"({broker_sync.get('matched', 0)} matched to plans).",
        )

    result = EodLearningResult(
        validated=validation["validated"],
        errors=validation["errors"],
        report=report,
        tuning=tuning,
        insights=insights,
        broker_sync=broker_sync,
    )

    if send_telegram_alert and telegram_configured():
        msg = format_track_record_telegram(report, tuning, validation)
        ok, err = send_telegram_broadcast(msg, alert_type="eod")
        result.telegram_sent = ok
        result.telegram_error = err if not ok else ""

    return result
