"""Home dashboard helper tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from ui.components.canvas_utils import _trim_words
from ui.components.home_dashboard import _pick_decision


class HomeDashboardHelpersTest(unittest.TestCase):
    def test_trim_words_caps_mentor_length(self):
        long = " ".join(["word"] * 30)
        trimmed = _trim_words(long, max_words=18)
        self.assertLessEqual(len(trimmed.split()), 18)
        self.assertTrue(trimmed.endswith("…"))

    def test_pick_decision_prefers_starred_equity(self):
        artifact = DecisionArtifact(
            decision_id="d1",
            timestamp="",
            verdict=DecisionVerdict.ACT,
            reason="ok",
            evidence_packet_id="ep1",
            confidence=0.8,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=True,
        )
        os_report = MagicMock(starred_symbol="TCS", decision_artifact=artifact)
        mis = MagicMock(decision_artifact=None)
        picked, source = _pick_decision(mis, os_report)
        self.assertEqual(picked, artifact)
        self.assertEqual(source, "equity")

    def test_pick_decision_falls_back_to_mis(self):
        artifact = DecisionArtifact(
            decision_id="d1",
            timestamp="",
            verdict=DecisionVerdict.WAIT,
            reason="ok",
            evidence_packet_id="ep1",
            confidence=0.5,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=False,
        )
        os_report = MagicMock(starred_symbol="", decision_artifact=None)
        mis = MagicMock(decision_artifact=artifact)
        picked, source = _pick_decision(mis, os_report)
        self.assertEqual(picked, artifact)
        self.assertEqual(source, "session")

    def test_pick_decision_skips_non_equity_mis(self):
        artifact = DecisionArtifact(
            decision_id="d1",
            timestamp="",
            verdict=DecisionVerdict.ACT,
            reason="ok",
            evidence_packet_id="ep1",
            confidence=0.8,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=True,
            subject_type="options",
        )
        os_report = MagicMock(starred_symbol="", decision_artifact=None)
        mis = MagicMock(decision_artifact=artifact)
        picked, source = _pick_decision(mis, os_report)
        self.assertIsNone(picked)
        self.assertEqual(source, "none")


if __name__ == "__main__":
    unittest.main()
