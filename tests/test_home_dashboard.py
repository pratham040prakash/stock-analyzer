"""Home dashboard helper tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.context_engine.models import ContextSnapshot
from ui.components.home_dashboard import (
    _mentor_one_liner,
    _pick_decision,
    _resolve_verdict_state,
    _snapshot_from_cache,
    _snapshot_to_cache,
    _trim_words,
    VerdictCanvasState,
)
from ui.broker.state import BrokerSnapshot


class HomeDashboardHelpersTest(unittest.TestCase):
    def test_trim_words_caps_mentor_length(self):
        long = " ".join(["word"] * 30)
        trimmed = _trim_words(long, max_words=18)
        self.assertLessEqual(len(trimmed.split()), 18)
        self.assertTrue(trimmed.endswith("…"))

    def test_resolve_verdict_connect_when_broker_offline(self):
        broker = BrokerSnapshot(state="disconnected")
        snapshot = MagicMock(risk_mode="NEUTRAL", market_session={}, market_phase="opening")
        mis = MagicMock(loss_streak_days=0)
        state = _resolve_verdict_state(broker, snapshot, mis, None)
        self.assertEqual(state.key, "connect")

    def test_resolve_verdict_trade_on_act(self):
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
        broker = BrokerSnapshot(state="connected")
        snapshot = MagicMock(
            risk_mode="NEUTRAL",
            market_session={"phase": "regular"},
            market_phase="regular",
            trading_restrictions=(),
            confidence=0.8,
        )
        mis = MagicMock(loss_streak_days=0)
        state = _resolve_verdict_state(broker, snapshot, mis, artifact)
        self.assertEqual(state.key, "trade")
        self.assertEqual(state.cta_label, "See the plan")

    def test_mentor_one_liner_is_short(self):
        state = VerdictCanvasState("wait", "Wait", "You're done for today", "done")
        line = _mentor_one_liner(
            state,
            decision=None,
            mis=MagicMock(summary="", flags=()),
            os_report=MagicMock(next_step=""),
            snapshot=MagicMock(trading_restrictions=()),
            pins=[],
        )
        self.assertLessEqual(len(line.split()), 18)

    def test_pick_decision_prefers_starred_equity(self):
        artifact = DecisionArtifact(
            decision_id="d1",
            timestamp="",
            verdict=DecisionVerdict.ACT,
            reason="ok",
            evidence_packet_id="ep1",
            confidence=80.0,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=True,
        )
        os_report = MagicMock(starred_symbol="RELIANCE", decision_artifact=artifact)
        mis = MagicMock(decision_artifact=artifact)
        picked, source = _pick_decision(mis, os_report)
        self.assertEqual(picked, artifact)
        self.assertEqual(source, "equity")

    def test_pick_decision_falls_back_to_mis(self):
        mis_artifact = DecisionArtifact(
            decision_id="d2",
            timestamp="",
            verdict=DecisionVerdict.WAIT,
            reason="wait",
            evidence_packet_id="ep2",
            confidence=50.0,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            subject_type="equity",
        )
        os_report = MagicMock(starred_symbol="", decision_artifact=None)
        mis = MagicMock(decision_artifact=mis_artifact)
        picked, source = _pick_decision(mis, os_report)
        self.assertEqual(picked, mis_artifact)
        self.assertEqual(source, "session")

    def test_pick_decision_skips_options_session_on_equity_home(self):
        options_artifact = DecisionArtifact(
            decision_id="d3",
            timestamp="",
            verdict=DecisionVerdict.WAIT,
            reason="NIFTY CE",
            evidence_packet_id="ep3",
            confidence=50.0,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            subject_type="options",
        )
        os_report = MagicMock(starred_symbol="", decision_artifact=None)
        mis = MagicMock(decision_artifact=options_artifact)
        picked, source = _pick_decision(mis, os_report)
        self.assertIsNone(picked)
        self.assertEqual(source, "none")

    def test_snapshot_cache_roundtrip_is_pickle_safe(self):
        import pickle
        from types import MappingProxyType

        snap = ContextSnapshot(
            timestamp="2026-07-15T09:00:00+05:30",
            market_regime="Neutral trend",
            market_phase="opening",
            market_breadth="mixed",
            volatility_state="normal",
            liquidity_state="normal",
            market_session=MappingProxyType({"is_open": True, "date": "2026-07-15"}),
            sector_strength=MappingProxyType({"leader": "IT"}),
            industry_strength=MappingProxyType({}),
            macro_state=MappingProxyType({"vix_regime": "normal"}),
            global_market_state=MappingProxyType({"bias": "NEUTRAL"}),
            risk_mode="NEUTRAL",
            trading_restrictions=("Wait for 9:45",),
            confidence=0.72,
            snapshot_id="ctx_abc123",
            context_hash="deadbeef",
            metadata=MappingProxyType({"allow_new_entries": False}),
        )
        cached = _snapshot_to_cache(snap)
        pickle.dumps(cached)
        restored = _snapshot_from_cache(cached)
        self.assertEqual(restored.market_regime, snap.market_regime)
        self.assertEqual(dict(restored.market_session), dict(snap.market_session))
        self.assertEqual(restored.snapshot_id, snap.snapshot_id)


if __name__ == "__main__":
    unittest.main()
