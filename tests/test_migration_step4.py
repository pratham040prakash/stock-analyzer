"""Migration Step 4 — legacy verdict elimination tests."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.combined import analyze_combined
from analyzer.decision_engine import DecisionVerdict
from analyzer.decision_engine.verdict_bridge import (
    attach_decision_to_combined,
    attach_decision_to_live_chart,
    evidence_items_from_score,
    legacy_chart_action,
    legacy_equity_recommendation,
    legacy_investment_os_verdict,
    legacy_options_action,
    resolve_verdict,
)
from analyzer.decision_engine.models import DecisionArtifact, UncertaintyVector
from analyzer.evidence_engine import EvidenceBuilder, EvidenceCategory, EvidenceEngine, EvidenceSource


def _decision(verdict: DecisionVerdict, *, confidence: float = 60.0, net: float = 0.5, trade_allowed: bool = True):
    return DecisionArtifact(
        decision_id="dec_test",
        timestamp="2026-01-01 10:00 IST",
        verdict=verdict,
        reason="test",
        evidence_packet_id="pkt_test",
        confidence=confidence,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        trade_allowed=trade_allowed,
        net_score=net,
    )


class TestLegacyMappers(unittest.TestCase):
    def test_legacy_equity_recommendation_act(self):
        self.assertEqual(legacy_equity_recommendation(_decision(DecisionVerdict.ACT, confidence=75)), "STRONG BUY")
        self.assertEqual(legacy_equity_recommendation(_decision(DecisionVerdict.ACT, confidence=55)), "BUY")

    def test_legacy_equity_recommendation_wait(self):
        self.assertEqual(legacy_equity_recommendation(_decision(DecisionVerdict.WAIT)), "HOLD")

    def test_legacy_chart_action_pass(self):
        self.assertEqual(legacy_chart_action(_decision(DecisionVerdict.PASS, net=-0.8)), "STRONG SELL")

    def test_legacy_options_no_trade(self):
        self.assertEqual(legacy_options_action(_decision(DecisionVerdict.WAIT)), "NO TRADE")
        self.assertEqual(legacy_options_action(_decision(DecisionVerdict.ACT), directional_hint="bullish"), "BUY CE")

    def test_legacy_investment_os_prep_closed(self):
        d = _decision(DecisionVerdict.ACT, trade_allowed=True)
        self.assertEqual(legacy_investment_os_verdict(d, has_star=False, session_open=True), "PREP")
        self.assertEqual(legacy_investment_os_verdict(d, has_star=True, session_open=False), "CLOSED")
        self.assertEqual(legacy_investment_os_verdict(d, has_star=True, session_open=True), "TRADE OK")


class TestEvidenceBridge(unittest.TestCase):
    def test_evidence_items_from_score_has_vote(self):
        items = evidence_items_from_score(42.0, label="test score")
        self.assertEqual(len(items), 1)
        self.assertIn("vote", items[0].metadata)
        self.assertIn("score", items[0].metadata)

    def test_resolve_verdict_returns_legacy_string(self):
        items = evidence_items_from_score(35.0)
        decision, legacy = resolve_verdict("TCS", "equity", items, legacy_equity_recommendation, persist=False)
        self.assertIsNotNone(decision)
        self.assertIn(legacy, {"STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"})


class TestModuleWiring(unittest.TestCase):
    def test_combined_routes_through_decision_engine(self):
        tech = MagicMock(composite_score=30.0, recommendation="HOLD")
        fund = MagicMock(composite_score=20.0, recommendation="HOLD")
        result = MagicMock(
            ticker="TCS",
            technical=tech,
            fundamental=fund,
            combined_score=25.0,
            combined_recommendation="HOLD",
        )
        with patch("analyzer.decision_engine.verdict_bridge.decide_from_packet") as mock_decide:
            mock_decide.return_value = _decision(DecisionVerdict.ACT, confidence=72)
            attach_decision_to_combined(result)
        self.assertEqual(result.combined_recommendation, "STRONG BUY")
        mock_decide.assert_called_once()

    def test_live_chart_routes_through_decision_engine(self):
        from analyzer.candle_narrative import LiveChartVerdict

        verdict = LiveChartVerdict(
            ticker="TCS",
            interval="5m",
            action="WAIT",
            confidence="low",
            summary="test",
            directional_score=2.5,
            reasons=["bullish candle"],
        )
        with patch("analyzer.decision_engine.verdict_bridge.decide_from_packet") as mock_decide:
            mock_decide.return_value = _decision(DecisionVerdict.ACT, confidence=80)
            attach_decision_to_live_chart(verdict)
        self.assertEqual(verdict.action, "STRONG BUY")
        mock_decide.assert_called_once()


class TestArchitectureGuard(unittest.TestCase):
    """Only decision_engine may assign DecisionVerdict."""

    VERDICT_ASSIGN_PATTERNS = (
        "DecisionVerdict.ACT",
        "DecisionVerdict.WAIT",
        "DecisionVerdict.PASS",
        "DecisionVerdict.REDUCE",
        "DecisionVerdict.DEFENSIVE",
    )

    def test_decision_verdict_only_in_decision_engine(self):
        root = Path(__file__).resolve().parent.parent / "analyzer"
        offenders: list[str] = []
        allowed_roots = (
            root / "decision_engine",
        )
        for path in root.rglob("*.py"):
            if any(str(path).startswith(str(a)) for a in allowed_roots):
                continue
            text = path.read_text(encoding="utf-8")
            for pat in self.VERDICT_ASSIGN_PATTERNS:
                if pat in text and "legacy_" not in path.name:
                    offenders.append(f"{path.relative_to(root.parent)}: {pat}")
        self.assertEqual(offenders, [], f"DecisionVerdict assigned outside decision_engine: {offenders}")

    def test_no_direct_score_to_rec_in_combined(self):
        combined_src = (Path(__file__).parent.parent / "analyzer" / "combined.py").read_text()
        self.assertNotIn("combined_recommendation=_score_to_rec", combined_src)

    def test_strategy_synthesis_no_verdict_from_score_call(self):
        syn_src = (Path(__file__).parent.parent / "analyzer" / "strategy_synthesis.py").read_text()
        self.assertNotIn("_verdict_from_score(net", syn_src)


class TestCombinedIntegration(unittest.TestCase):
    """Smoke test with mocked fundamentals path."""

    def test_analyze_combined_sets_decision_artifact(self):
        import pandas as pd

        n = 60
        df = pd.DataFrame({
            "Close": [100 + i * 0.1 for i in range(n)],
            "High": [101 + i * 0.1 for i in range(n)],
            "Low": [99 + i * 0.1 for i in range(n)],
            "Open": [100 + i * 0.1 for i in range(n)],
            "Volume": [1_000_000] * n,
        })
        with patch("analyzer.combined.analyze_fundamentals") as mock_fund:
            from analyzer.fundamentals import FundamentalResult

            mock_fund.return_value = FundamentalResult(
                ticker="TCS",
                recommendation="HOLD",
                composite_score=10.0,
                metrics=[],
                raw={},
            )
            with patch("analyzer.combined.analyze") as mock_tech:
                from analyzer.signals import AnalysisResult

                mock_tech.return_value = AnalysisResult(
                    ticker="TCS",
                    recommendation="BUY",
                    composite_score=20.0,
                    confidence="medium",
                    current_price=106.0,
                )
                result = analyze_combined(df, "TCS", yf_info={"symbol": "TCS.NS"})
        self.assertIn(result.combined_recommendation, {"STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"})


if __name__ == "__main__":
    unittest.main()
