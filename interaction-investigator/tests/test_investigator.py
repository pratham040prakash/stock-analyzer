"""Tests for interaction-investigator."""

from pathlib import Path

from investigator.parser import parse_logs
from investigator.rca import generate_rca
from investigator.report import build_markdown_report
from investigator.timeline import build_timeline

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "demo_interaction.log"


def test_demo_log_produces_failed_desktop_stage():
    parsed = parse_logs(SAMPLE.read_text(encoding="utf-8"))
    timeline = build_timeline(parsed)
    desktop = next(s for s in timeline.stages if s.stage == "desktop")
    assert desktop.status == "failed"
    assert desktop.error_count >= 1


def test_rule_rca_and_report():
    parsed = parse_logs(SAMPLE.read_text(encoding="utf-8"))
    timeline = build_timeline(parsed)
    rca = generate_rca(timeline, symptom="desktop failed", use_ai=False)
    assert rca.primary_cause is not None
    assert rca.primary_cause.stage == "desktop"
    report = build_markdown_report(
        interaction_id="demo-123",
        symptom="desktop failed",
        timeline=timeline,
        rca=rca,
    )
    assert "Interaction Investigation Report" in report
    assert "Desktop" in report
