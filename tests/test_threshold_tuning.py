"""Tests for auto threshold tuning from journal outcomes."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.suggestion_learning import LearningReport, PerformanceSlice
from analyzer.threshold_tuning import (
    DEFAULT_THRESHOLDS,
    apply_threshold_tuning,
    get_pulse_thresholds,
    load_threshold_state,
    reset_thresholds,
)


def _slice(label: str, scored: int, wins: int, losses: int) -> PerformanceSlice:
    wr = round(wins / scored * 100, 1) if scored else 0.0
    return PerformanceSlice(
        label=label,
        total=scored,
        scored=scored,
        wins=wins,
        losses=losses,
        win_rate_pct=wr,
        avg_return_1d=0.5,
        avg_alpha_1d=0.2,
    )


class TestThresholdTuning(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "thresholds.json"
        self.patcher = patch(
            "analyzer.threshold_tuning.thresholds_path",
            return_value=self.path,
        )
        self.patcher.start()
        reset_thresholds()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.tmp.cleanup()

    def test_defaults_when_no_file(self) -> None:
        self.assertEqual(get_pulse_thresholds(), DEFAULT_THRESHOLDS)

    def test_tighten_on_low_win_rate(self) -> None:
        report = LearningReport(
            total_suggestions=20,
            validated_count=20,
            pending_count=0,
            overall_win_rate_pct=38.0,
            slices=[
                _slice("Horizon: intraday", scored=10, wins=3, losses=7),
            ],
        )
        result = apply_threshold_tuning(report)
        self.assertTrue(result.applied)
        self.assertEqual(len(result.changes), 1)
        self.assertGreater(result.thresholds["intraday"], DEFAULT_THRESHOLDS["intraday"])
        self.assertEqual(get_pulse_thresholds()["intraday"], result.thresholds["intraday"])

    def test_no_change_insufficient_samples(self) -> None:
        report = LearningReport(
            total_suggestions=5,
            validated_count=5,
            pending_count=0,
            overall_win_rate_pct=20.0,
            slices=[_slice("Horizon: intraday", scored=3, wins=0, losses=3)],
        )
        result = apply_threshold_tuning(report)
        self.assertFalse(result.applied)
        self.assertEqual(result.thresholds, DEFAULT_THRESHOLDS)

    def test_relax_on_high_win_rate(self) -> None:
        report = LearningReport(
            total_suggestions=20,
            validated_count=20,
            pending_count=0,
            overall_win_rate_pct=70.0,
            slices=[
                _slice("Horizon: short", scored=12, wins=9, losses=3),
            ],
        )
        result = apply_threshold_tuning(report)
        self.assertTrue(result.applied)
        self.assertLess(result.thresholds["short"], DEFAULT_THRESHOLDS["short"])

    def test_persists_history(self) -> None:
        report = LearningReport(
            total_suggestions=20,
            validated_count=20,
            pending_count=0,
            overall_win_rate_pct=35.0,
            slices=[_slice("Horizon: long", scored=10, wins=3, losses=7)],
        )
        apply_threshold_tuning(report)
        state = load_threshold_state()
        self.assertTrue(state["history"])
        self.assertTrue(self.path.exists())
        data = json.loads(self.path.read_text())
        self.assertIn("thresholds", data)


if __name__ == "__main__":
    unittest.main()
