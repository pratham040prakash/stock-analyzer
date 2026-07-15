"""Home dashboard helper tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.context_engine.models import ContextSnapshot
from ui.components.home_dashboard import (
    _pick_decision,
    _risk_reward,
    _snapshot_from_cache,
    _snapshot_to_cache,
)


class HomeDashboardHelpersTest(unittest.TestCase):
    def test_risk_reward(self):
        self.assertEqual(_risk_reward(100.0, 95.0, 110.0), 2.0)
        self.assertIsNone(_risk_reward(100.0, 100.0, 110.0))

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
        )
        os_report = MagicMock(starred_symbol="", decision_artifact=None)
        mis = MagicMock(decision_artifact=mis_artifact)
        picked, source = _pick_decision(mis, os_report)
        self.assertEqual(picked, mis_artifact)
        self.assertEqual(source, "session")

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
