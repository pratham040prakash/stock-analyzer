"""Tests for Evidence Engine (Migration Step 2)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.evidence_engine import (
    EvidenceBuilder,
    EvidenceCategory,
    EvidenceConfidence,
    EvidenceEngine,
    EvidenceSource,
    EvidenceType,
    EvidenceValidator,
    build_synthesis_packet,
    evidence_packet_from_json,
    evidence_packet_to_json,
    merge_duplicate_items,
)
from analyzer.evidence_engine.conflicts import EvidenceConflictDetector
from analyzer.evidence_engine.migration import (
    evidence_from_combined,
    evidence_from_data_gaps,
    evidence_from_strategy_votes,
)
from analyzer.evidence_engine.render import format_evidence_report
from analyzer.evidence_engine.store import fetch_evidence_packet, init_evidence_store, save_evidence_packet
from analyzer.strategy_synthesis import StrategyVote


class TestEvidenceValidator(unittest.TestCase):
    def test_unknown_source_cannot_be_fact(self):
        b = EvidenceBuilder()
        item = b.fact(
            category=EvidenceCategory.TECHNICAL,
            label="RSI",
            value=55,
            explanation="RSI reading",
            source=EvidenceSource.UNKNOWN,
        )
        validated = EvidenceValidator().validate(item)
        self.assertNotEqual(validated.type, EvidenceType.FACT)

    def test_empty_value_becomes_gap(self):
        b = EvidenceBuilder()
        item = b.build(
            category=EvidenceCategory.FUNDAMENTAL,
            label="ROE",
            type=EvidenceType.FACT,
            value=None,
            explanation="",
            source=EvidenceSource.YAHOO_FINANCE,
        )
        validated = EvidenceValidator().validate(item)
        self.assertEqual(validated.type, EvidenceType.GAP)

    def test_internal_model_cannot_be_fact(self):
        b = EvidenceBuilder()
        item = b.fact(
            category=EvidenceCategory.TECHNICAL,
            label="RSI",
            value=55,
            explanation="model output",
            source=EvidenceSource.INTERNAL_MODEL,
            confidence=EvidenceConfidence.HIGH,
        )
        validated = EvidenceValidator().validate(item)
        self.assertEqual(validated.type, EvidenceType.ESTIMATE)

    def test_trusted_feed_stays_fact(self):
        b = EvidenceBuilder()
        item = b.fact(
            category=EvidenceCategory.FUNDAMENTAL,
            label="P/E",
            value=18.5,
            explanation="yahoo feed",
            source=EvidenceSource.YAHOO_FINANCE,
            confidence=EvidenceConfidence.HIGH,
        )
        validated = EvidenceValidator().validate(item)
        self.assertEqual(validated.type, EvidenceType.FACT)


class TestEvidenceEngine(unittest.TestCase):
    def test_merge_duplicates(self):
        b = EvidenceBuilder()
        a = b.fact(
            category=EvidenceCategory.TECHNICAL,
            label="RSI",
            value=55,
            explanation="first",
            source=EvidenceSource.YAHOO_FINANCE,
            confidence=EvidenceConfidence.LOW,
        )
        c = b.fact(
            category=EvidenceCategory.TECHNICAL,
            label="RSI",
            value=55,
            explanation="second",
            source=EvidenceSource.YAHOO_FINANCE,
            confidence=EvidenceConfidence.HIGH,
        )
        merged = merge_duplicate_items([a, c])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].confidence, EvidenceConfidence.HIGH)

    def test_injects_category_gaps(self):
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        packet = eng.build_packet(
            subject="TCS",
            subject_type="equity",
            items=[
                b.fact(
                    category=EvidenceCategory.TECHNICAL,
                    label="Trend",
                    value="bullish",
                    explanation="uptrend",
                    source=EvidenceSource.YAHOO_FINANCE,
                )
            ],
        )
        self.assertGreater(packet.gap_count, 0)
        gap_cats = {g.category for g in packet.gaps}
        self.assertIn(EvidenceCategory.FUNDAMENTAL, gap_cats)

    def test_skips_category_gap_when_gap_exists(self):
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        packet = eng.build_packet(
            subject="TCS",
            subject_type="equity",
            items=[
                b.gap(
                    category=EvidenceCategory.FUNDAMENTAL,
                    label="Missing fundamentals",
                    explanation="No feed",
                ),
                b.fact(
                    category=EvidenceCategory.TECHNICAL,
                    label="Trend",
                    value="bullish",
                    explanation="uptrend",
                    source=EvidenceSource.YAHOO_FINANCE,
                ),
            ],
        )
        fund_gaps = [g for g in packet.gaps if g.category == EvidenceCategory.FUNDAMENTAL]
        self.assertEqual(len(fund_gaps), 1)
        self.assertEqual(fund_gaps[0].label, "Missing fundamentals")

    def test_detects_conflicts(self):
        b = EvidenceBuilder()
        bull = b.build(
            category=EvidenceCategory.TECHNICAL,
            label="MACD",
            type=EvidenceType.ESTIMATE,
            value="bullish",
            explanation="bull",
            metadata={"vote": 1.5},
        )
        bear = b.build(
            category=EvidenceCategory.TECHNICAL,
            label="RSI",
            type=EvidenceType.ESTIMATE,
            value="bearish",
            explanation="bear",
            metadata={"vote": -1.5},
        )
        conflicts = EvidenceConflictDetector().detect([bull, bear])
        self.assertGreaterEqual(len(conflicts), 1)

    def test_conflict_dedup(self):
        b = EvidenceBuilder()
        rec_a = b.build(
            category=EvidenceCategory.TECHNICAL,
            label="Combined recommendation",
            type=EvidenceType.ESTIMATE,
            value="BUY",
            explanation="buy",
            metadata={"vote": 1.5},
        )
        rec_b = b.build(
            category=EvidenceCategory.TECHNICAL,
            label="Technical recommendation",
            type=EvidenceType.ESTIMATE,
            value="SELL",
            explanation="sell",
            metadata={"vote": -1.5},
        )
        conflicts = EvidenceConflictDetector().detect([rec_a, rec_b])
        ids = [c.id for c in conflicts]
        self.assertEqual(len(ids), len(set(ids)))

    def test_recommend_from_packet_wait_on_gaps_only(self):
        eng = EvidenceEngine()
        packet = eng.build_packet(subject="X", subject_type="equity", items=[])
        rec = eng.recommend_from_packet(packet)
        self.assertEqual(rec.verdict, "WAIT")
        self.assertFalse(rec.trade_allowed)


class TestMigrationAdapters(unittest.TestCase):
    def test_strategy_votes_to_items(self):
        votes = [
            StrategyVote("mtf", "mtf", 1.2, 0.14, "Bullish MTF", emoji="🟢"),
            StrategyVote("regime", "regime", -0.8, 0.10, "Range-bound", emoji="🟡"),
        ]
        items = evidence_from_strategy_votes(votes)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].type, EvidenceType.ESTIMATE)
        self.assertEqual(items[0].metadata["vote"], 1.2)

    def test_combined_to_items(self):
        tech = MagicMock(
            composite_score=20,
            recommendation="BUY",
            confidence="medium",
            signals=[],
        )
        fund = MagicMock(
            composite_score=15,
            recommendation="BUY",
            metrics=[],
        )
        combined = MagicMock(
            technical=tech,
            fundamental=fund,
            combined_score=18,
            combined_recommendation="BUY",
            technical_weight=0.55,
            fundamental_weight=0.45,
            ticker="TCS.NS",
        )
        items = evidence_from_combined(combined)
        self.assertGreaterEqual(len(items), 3)
        types = {i.label: i.type for i in items}
        self.assertEqual(types["Technical composite score"], EvidenceType.ESTIMATE)

    def test_data_gaps_to_gap_items(self):
        items = evidence_from_data_gaps(["Missing ROE", "No news"])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].type, EvidenceType.GAP)


class TestSerialization(unittest.TestCase):
    def test_round_trip_json(self):
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        packet = eng.build_packet(
            subject="INFY",
            subject_type="research",
            items=[
                b.estimate(
                    category=EvidenceCategory.FUNDAMENTAL,
                    label="P/E",
                    value=24.5,
                    explanation="trailing PE",
                )
            ],
        )
        raw = evidence_packet_to_json(packet)
        restored = evidence_packet_from_json(raw)
        self.assertEqual(restored.packet_id, packet.packet_id)
        self.assertEqual(len(restored.items), len(packet.items))

    def test_round_trip_with_conflicts(self):
        eng = EvidenceEngine()
        b = EvidenceBuilder()
        bull = b.build(
            category=EvidenceCategory.TECHNICAL,
            label="MACD",
            type=EvidenceType.ESTIMATE,
            value="bullish",
            explanation="bull",
            metadata={"vote": 1.5},
        )
        bear = b.build(
            category=EvidenceCategory.TECHNICAL,
            label="RSI",
            type=EvidenceType.ESTIMATE,
            value="bearish",
            explanation="bear",
            metadata={"vote": -1.5},
        )
        packet = eng.build_packet(subject="X", subject_type="equity", items=[bull, bear])
        restored = evidence_packet_from_json(evidence_packet_to_json(packet))
        self.assertGreaterEqual(len(restored.conflicts), 1)
        self.assertEqual(restored.conflicts[0].severity, packet.conflicts[0].severity)

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            evidence_packet_from_json("{not json")

    def test_schema_version_present(self):
        eng = EvidenceEngine()
        packet = eng.build_packet(subject="A", subject_type="equity", items=[])
        data = json.loads(evidence_packet_to_json(packet))
        self.assertEqual(data.get("schema_version"), 1)


class TestEvidenceStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "evidence.db"
        self.p = patch(
            "analyzer.evidence_engine.store.evidence_store_path",
            return_value=self.db,
        )
        self.p.start()
        init_evidence_store()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()

    def test_save_and_fetch(self):
        eng = EvidenceEngine()
        packet = eng.build_packet(
            subject="SBIN",
            subject_type="equity",
            items=evidence_from_data_gaps(["test gap"]),
        )
        save_evidence_packet(packet)
        loaded = fetch_evidence_packet(packet.packet_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.subject, "SBIN")


class TestStrategySynthesisIntegration(unittest.TestCase):
    def test_build_synthesis_packet_from_votes(self):
        votes = [
            StrategyVote("mtf", "mtf", 1.2, 0.14, "Bullish MTF", emoji="🟢"),
            StrategyVote("timing", "timing", 1.0, 0.10, "Session open", emoji="🟢"),
        ]
        packet, rec = build_synthesis_packet("TCS", "equity", votes)
        self.assertIsNotNone(packet.packet_id)
        self.assertGreater(len(packet.items), 0)
        self.assertIn(rec.verdict, ("WAIT", "CAUTION", "BUY", "STRONG_BUY", "NO_TRADE"))


class TestRender(unittest.TestCase):
    def test_format_report_includes_gaps(self):
        eng = EvidenceEngine()
        packet = eng.build_packet(subject="Z", subject_type="equity", items=[])
        md = format_evidence_report(packet)
        self.assertIn("Evidence packet", md)
        self.assertIn("GAP", md)


if __name__ == "__main__":
    unittest.main()
