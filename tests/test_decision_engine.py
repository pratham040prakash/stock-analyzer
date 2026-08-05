"""Tests for Decision Engine (Migration Step 3)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.decision_engine import (
    CapitalConstraints,
    DecisionEngine,
    DecisionVerdict,
    DecisionValidator,
    ImmutableDecisionError,
    MarketContext,
    PortfolioState,
    RiskSettings,
    UserPreferences,
    decide_from_packet,
    decision_artifact_from_json,
    decision_artifact_to_json,
    fetch_decision,
    init_decision_store,
    legacy_advisor_action,
    legacy_mis_verdict,
    legacy_synthesis_verdict,
    save_decision,
)
from analyzer.decision_engine.migration import (
    attach_decision_to_mis_advisory,
    evidence_items_from_advisor_signals,
    evidence_items_from_mis_signals,
    legacy_mis_headline,
)
from analyzer.decision_engine.rules import is_critical_gap
from analyzer.evidence_engine import EvidenceBuilder, EvidenceCategory, EvidenceEngine, EvidenceSource, EvidenceType


def _engine() -> DecisionEngine:
    return DecisionEngine(persist=False)


def _sample_packet(**kwargs):
    eng = EvidenceEngine()
    b = EvidenceBuilder()
    items = [
        b.build(
            category=EvidenceCategory.TECHNICAL,
            label="mtf signal",
            type=EvidenceType.ESTIMATE,
            value="bullish",
            explanation="MTF aligned",
            metadata={"vote": 1.2},
            weight=0.14,
        ),
        b.fact(
            category=EvidenceCategory.FUNDAMENTAL,
            label="P/E",
            value=18.0,
            explanation="yahoo",
            source=EvidenceSource.YAHOO_FINANCE,
        ),
        b.fact(
            category=EvidenceCategory.MARKET,
            label="Session",
            value="open",
            explanation="market session open",
            source=EvidenceSource.INTERNAL_MODEL,
        ),
        b.build(
            category=EvidenceCategory.RISK,
            label="Stop",
            type=EvidenceType.ESTIMATE,
            value="defined",
            explanation="stop set",
            metadata={"vote": 0.5},
        ),
    ]
    return eng.build_packet(subject="TCS", subject_type="equity", items=items, **kwargs)


class TestDecisionValidator(unittest.TestCase):
    def test_rejects_missing_packet(self):
        errors = DecisionValidator().validate_packet(None)
        self.assertIn("Missing EvidencePacket", errors)

    def test_rejects_low_completeness(self):
        eng = EvidenceEngine()
        packet = eng.build_packet(subject="X", subject_type="equity", items=[])
        errors = DecisionValidator().validate_packet(packet)
        self.assertTrue(any("completeness" in e for e in errors))

    def test_rejects_unknown_portfolio(self):
        from analyzer.decision_engine.models import DecisionContext, DecisionRequest

        req = DecisionRequest(
            subject="X",
            subject_type="equity",
            evidence_packet_id="pkt_1",
            context=DecisionContext(portfolio=PortfolioState(known=False)),
        )
        errors = DecisionValidator().validate_request(req)
        self.assertTrue(any("Unknown Portfolio" in e for e in errors))

    def test_finds_critical_gaps(self):
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        gap_item = b.gap(
            category=EvidenceCategory.RISK,
            label="Risk coverage gap",
            explanation="Missing stop-loss evidence",
        )
        packet = eng.build_packet(subject="X", subject_type="equity", items=[gap_item])
        gaps = DecisionValidator().find_critical_gaps(packet)
        self.assertTrue(len(gaps) >= 1)
        self.assertTrue(is_critical_gap(gap_item))


class TestDecisionEngine(unittest.TestCase):
    def test_act_on_strong_positive_evidence(self):
        packet = _sample_packet()
        decision = _engine().decide(
            packet,
            market=MarketContext(allow_new_entries=True, allow_aggressive=True),
            preferences=UserPreferences(beginner_mode=False),
        )
        self.assertIn(decision.verdict, (DecisionVerdict.ACT, DecisionVerdict.WAIT))
        self.assertGreater(decision.confidence, 0)
        self.assertEqual(decision.evidence_packet_id, packet.packet_id)
        self.assertIsNotNone(decision.explainability)
        self.assertTrue(decision.decision_version)

    def test_wait_when_entries_blocked(self):
        packet = _sample_packet()
        decision = _engine().decide(
            packet,
            market=MarketContext(allow_new_entries=False, timing_headline="Wait until 9:45"),
        )
        self.assertIn(decision.verdict, (DecisionVerdict.WAIT, DecisionVerdict.PASS))
        self.assertFalse(decision.trade_allowed)

    def test_pass_on_negative_net(self):
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        packet = eng.build_packet(
            subject="X",
            subject_type="equity",
            items=[
                b.fact(
                    category=EvidenceCategory.MARKET,
                    label="Session",
                    value="open",
                    explanation="open",
                    source=EvidenceSource.INTERNAL_MODEL,
                ),
                b.build(
                    category=EvidenceCategory.TECHNICAL,
                    label="bear",
                    type=EvidenceType.ESTIMATE,
                    value="bearish",
                    explanation="bad",
                    metadata={"vote": -1.8},
                ),
                b.build(
                    category=EvidenceCategory.FUNDAMENTAL,
                    label="P/E",
                    type=EvidenceType.FACT,
                    value=30,
                    explanation="high",
                    source=EvidenceSource.YAHOO_FINANCE,
                ),
                b.build(
                    category=EvidenceCategory.RISK,
                    label="Stop",
                    type=EvidenceType.ESTIMATE,
                    value="set",
                    explanation="stop",
                    metadata={"vote": 0.3},
                ),
            ],
        )
        decision = _engine().decide(
            packet,
            market=MarketContext(allow_new_entries=True, allow_aggressive=True),
        )
        self.assertIn(decision.verdict, (DecisionVerdict.PASS, DecisionVerdict.REDUCE, DecisionVerdict.WAIT))

    def test_critical_gap_rejection(self):
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        items = [
            b.gap(
                category=EvidenceCategory.EXECUTION,
                label="Execution coverage gap",
                explanation="No execution plan",
            ),
            b.fact(
                category=EvidenceCategory.TECHNICAL,
                label="RSI",
                value=55,
                explanation="neutral",
                source=EvidenceSource.INTERNAL_MODEL,
                metadata={"vote": 0.5},
            ),
        ]
        packet = eng.build_packet(subject="X", subject_type="equity", items=items)
        decision = _engine().decide(packet)
        self.assertEqual(decision.verdict, DecisionVerdict.PASS)
        self.assertIn("gap", decision.reason.lower())

    def test_capital_max_trades_blocks(self):
        packet = _sample_packet()
        decision = _engine().decide(
            packet,
            capital=CapitalConstraints(max_trades=2),
            portfolio=PortfolioState(open_positions=2),
        )
        self.assertEqual(decision.verdict, DecisionVerdict.WAIT)

    def test_loss_streak_risk_block(self):
        packet = _sample_packet()
        decision = _engine().decide(
            packet,
            risk=RiskSettings(loss_streak_days=3, max_loss_streak_before_pause=2),
        )
        self.assertIn(decision.verdict, (DecisionVerdict.WAIT, DecisionVerdict.PASS))

    def test_supporting_and_conflicting_ids(self):
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        bull = b.build(
            category=EvidenceCategory.TECHNICAL,
            label="bull",
            type=EvidenceType.ESTIMATE,
            value="up",
            explanation="up",
            metadata={"vote": 1.5},
        )
        bear = b.build(
            category=EvidenceCategory.TECHNICAL,
            label="bear",
            type=EvidenceType.ESTIMATE,
            value="down",
            explanation="down",
            metadata={"vote": -1.2},
        )
        packet = eng.build_packet(
            subject="X",
            subject_type="equity",
            items=[
                b.fact(
                    category=EvidenceCategory.MARKET,
                    label="Session",
                    value="open",
                    explanation="open",
                    source=EvidenceSource.INTERNAL_MODEL,
                ),
                bull,
                bear,
                b.build(
                    category=EvidenceCategory.FUNDAMENTAL,
                    label="P/E",
                    type=EvidenceType.FACT,
                    value=20,
                    explanation="ok",
                    source=EvidenceSource.YAHOO_FINANCE,
                ),
                b.build(
                    category=EvidenceCategory.RISK,
                    label="Stop",
                    type=EvidenceType.ESTIMATE,
                    value="set",
                    explanation="stop",
                    metadata={"vote": 0.2},
                ),
            ],
        )
        decision = _engine().decide(
            packet,
            market=MarketContext(allow_new_entries=True, allow_aggressive=True),
        )
        self.assertTrue(len(decision.supporting_evidence_ids) >= 1)
        if packet.conflicts:
            self.assertTrue(len(decision.conflicting_evidence_ids) >= 1)
        else:
            self.assertGreaterEqual(len(decision.conflicting_evidence_ids), 0)

    def test_explainability_fields(self):
        packet = _sample_packet()
        decision = _engine().decide(packet)
        self.assertIsNotNone(decision.explainability)
        self.assertTrue(decision.explainability.why)
        self.assertTrue(decision.explainability.why_now)
        self.assertTrue(decision.explainability.why_not)


class TestLegacyMapping(unittest.TestCase):
    def test_synthesis_act_maps_buy(self):
        d = MagicMock(verdict=DecisionVerdict.ACT, confidence=80)
        self.assertEqual(legacy_synthesis_verdict(d), "STRONG_BUY")

    def test_advisor_pass_maps_avoid(self):
        d = MagicMock(verdict=DecisionVerdict.PASS, confidence=30, net_score=-0.5)
        self.assertEqual(legacy_advisor_action(d), "AVOID")

    def test_mis_act_maps_trade_ok(self):
        d = MagicMock(verdict=DecisionVerdict.ACT, reason="go")
        self.assertEqual(legacy_mis_verdict(d), "TRADE_OK")
        emoji, headline, _ = legacy_mis_headline(d)
        self.assertEqual(emoji, "🟢")


class TestSerialization(unittest.TestCase):
    def test_round_trip_with_new_fields(self):
        packet = _sample_packet()
        decision = _engine().decide(packet)
        raw = decision_artifact_to_json(decision)
        restored = decision_artifact_from_json(raw)
        self.assertEqual(restored.decision_id, decision.decision_id)
        self.assertEqual(restored.verdict, decision.verdict)
        self.assertEqual(restored.decision_version, decision.decision_version)
        if decision.explainability:
            self.assertIsNotNone(restored.explainability)
            self.assertEqual(restored.explainability.why, decision.explainability.why)

    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            decision_artifact_from_json("{")


class TestDecisionHistory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "decisions.db"
        self.p = patch(
            "analyzer.decision_engine.history.decision_store_path",
            return_value=self.db,
        )
        self.p.start()
        init_decision_store()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()

    def test_save_and_fetch(self):
        packet = _sample_packet()
        decision = _engine().decide(packet)
        save_decision(decision)
        loaded = fetch_decision(decision.decision_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.verdict, decision.verdict)

    def test_immutable_no_overwrite(self):
        packet = _sample_packet()
        decision = _engine().decide(packet)
        save_decision(decision)
        with self.assertRaises(ImmutableDecisionError):
            save_decision(decision)


class TestMigration(unittest.TestCase):
    def test_advisor_signals_are_evidence_not_verdict(self):
        items = evidence_items_from_advisor_signals(
            heuristic_action="BUY",
            conviction="medium",
            bullish=["RSI bounce"],
            bearish=[],
            risks=["gap risk"],
        )
        self.assertGreater(len(items), 0)
        self.assertTrue(all(i.type != EvidenceType.GAP for i in items[:2]))

    def test_mis_signals_are_evidence(self):
        items = evidence_items_from_mis_signals(
            flags=["Late entry"],
            positives=["Gate green"],
            score=72,
            gate_allowed=True,
            regime="Trending",
            loss_streak_days=0,
        )
        self.assertGreaterEqual(len(items), 3)

    def test_decide_from_packet_helper(self):
        packet = _sample_packet()
        decision = decide_from_packet(packet, persist=False)
        self.assertIsNotNone(decision.decision_id)

    def test_attach_mis_advisory(self):
        adv = MagicMock(
            flags=["test flag"],
            positives=["gate ok"],
            score=70,
            gate_allowed=True,
            regime="Trending",
            loss_streak_days=0,
            synthesis_confidence=65,
        )
        attach_decision_to_mis_advisory(adv, session_open=True, pick_label="NIFTY CE 24000")
        self.assertIsNotNone(adv.decision_artifact)
        self.assertIn(adv.verdict, ("TRADE_OK", "CAUTION", "NO_TRADE", "OBSERVE"))


class TestArtifactIntegrity(unittest.TestCase):
    def test_every_decision_has_packet_id_and_explainability(self):
        cases = [
            _sample_packet(),
        ]
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        gap_packet = eng.build_packet(
            subject="GAP",
            subject_type="equity",
            items=[
                b.fact(
                    category=EvidenceCategory.MARKET,
                    label="Session",
                    value="open",
                    explanation="open",
                    source=EvidenceSource.INTERNAL_MODEL,
                ),
                b.gap(
                    category=EvidenceCategory.RISK,
                    label="Risk coverage",
                    explanation="missing",
                ),
            ],
        )
        cases.append(gap_packet)

        for packet in cases:
            decision = _engine().decide(
                packet,
                market=MarketContext(allow_new_entries=True, allow_aggressive=True),
            )
            self.assertTrue(decision.evidence_packet_id)
            self.assertNotEqual(decision.evidence_packet_id, "missing")
            self.assertEqual(decision.evidence_packet_id, packet.packet_id)
            self.assertIsNotNone(decision.explainability)
            self.assertTrue(decision.explainability.why)
            self.assertTrue(decision.explainability.why_now)
            self.assertTrue(decision.explainability.why_not)

    def test_validator_rejects_invalid_artifact(self):
        from analyzer.decision_engine.models import DecisionArtifact, DecisionExplainability, UncertaintyVector

        bad = DecisionArtifact(
            decision_id="dec_test",
            timestamp="now",
            verdict=DecisionVerdict.WAIT,
            reason="test",
            evidence_packet_id="",
            confidence=0,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
        )
        errors = DecisionValidator().validate_artifact(bad)
        self.assertTrue(any("evidence_packet_id" in e for e in errors))


class TestAttachFallbacks(unittest.TestCase):
    def test_synthesis_attach_failure_defaults_wait(self):
        from analyzer.decision_engine.migration import attach_decision_to_synthesis
        from analyzer.strategy_synthesis import StrategySynthesis, StrategyVote

        syn = StrategySynthesis(
            target="X",
            asset_class="equity",
            side="LONG",
            pillars=[StrategyVote("a", "a", 1.0, 0.1, "ok")],
            evidence_packet=_sample_packet(),
            verdict="STRONG_BUY",
        )
        with patch("analyzer.decision_engine.migration.decide_from_packet", side_effect=RuntimeError("fail")):
            attach_decision_to_synthesis(syn)
        self.assertEqual(syn.verdict, "WAIT")
        self.assertFalse(syn.trade_allowed)

    def test_advisor_attach_failure_defaults_hold(self):
        from analyzer.decision_engine.migration import attach_decision_to_advice
        from analyzer.advisor import InvestmentAdvice

        advice = InvestmentAdvice(
            ticker="X",
            name="X",
            final_action="BUY",
            conviction="low",
            time_horizon="medium",
            position_hint="",
            entry_zone="",
            stop_loss="",
            target="",
            risk_reward="",
            score_summary="",
            bullish_factors=[],
            bearish_factors=[],
            risks=[],
            standards_checklist=[],
            summary="",
            portfolio_tips=[],
            evidence_packet=_sample_packet(),
        )
        with patch("analyzer.decision_engine.migration.decide_from_packet", side_effect=RuntimeError("fail")):
            attach_decision_to_advice(advice)
        self.assertEqual(advice.final_action, "HOLD")


class TestArchitectureGuards(unittest.TestCase):
    def test_verdict_enum_only_in_decision_engine_package(self):
        """Canonical DecisionVerdict assignment stays inside decision_engine; use_cases may compare."""
        import ast
        import pathlib

        root = pathlib.Path(__file__).resolve().parent.parent / "analyzer"
        offenders: list[str] = []
        for path in root.rglob("*.py"):
            if "decision_engine" in path.parts:
                continue
            if "use_cases" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    if node.value.id == "DecisionVerdict":
                        offenders.append(f"{path.relative_to(root)}:{node.lineno}")
        self.assertEqual(offenders, [], f"DecisionVerdict used outside decision_engine: {offenders}")

    def test_no_circular_import_engine_migration(self):
        import analyzer.decision_engine.engine as eng_mod
        import analyzer.decision_engine.migration as mig_mod

        self.assertNotIn("migration", eng_mod.__name__)
        self.assertTrue(hasattr(eng_mod, "DecisionEngine"))
        self.assertTrue(hasattr(mig_mod, "decide_from_packet"))


class TestIntegrationHooks(unittest.TestCase):
    def test_attach_decision_to_synthesis(self):
        from analyzer.decision_engine.migration import attach_decision_to_synthesis
        from analyzer.evidence_engine.migration import build_synthesis_packet
        from analyzer.strategy_synthesis import StrategySynthesis, StrategyVote

        votes = [StrategyVote("mtf", "mtf", 1.0, 0.14, "bull", emoji="🟢")]
        packet, _ = build_synthesis_packet("TCS", "equity", votes)
        syn = StrategySynthesis(
            target="TCS",
            asset_class="equity",
            side="LONG",
            pillars=votes,
            evidence_packet=packet,
        )
        with patch("analyzer.decision_engine.migration.decide_from_packet") as mock_decide:
            mock_decide.return_value = MagicMock(
                verdict=DecisionVerdict.ACT,
                confidence=72,
                reason="test",
                net_score=0.8,
                trade_allowed=True,
                alternative_actions=["WAIT"],
            )
            attach_decision_to_synthesis(syn)
        self.assertIsNotNone(syn.decision_artifact)
        self.assertIn(syn.verdict, ("BUY", "STRONG_BUY", "WAIT", "NO_TRADE", "CAUTION"))


if __name__ == "__main__":
    unittest.main()
