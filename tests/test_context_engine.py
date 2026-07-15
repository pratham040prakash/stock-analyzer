"""Context Engine tests — snapshot, composer, normalizer, cache, migration."""

from __future__ import annotations

import threading
import unittest
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.context_engine import (
    SCHEMA_VERSION,
    build_context_snapshot,
    clear_cache,
    market_context_from_snapshot,
)
from analyzer.context_engine.cache import LIVE_TTL_SEC, get_cached, put_cached
from analyzer.context_engine.models import ContextSnapshot
from analyzer.context_engine.normalizer import (
    normalize_market_phase,
    normalize_regime,
    normalize_risk_mode,
    normalize_volatility,
    validate_snapshot_fields,
)
from analyzer.context_engine.migration import evidence_items_from_snapshot


class TestContextSnapshot(unittest.TestCase):
    def test_immutable_frozen(self):
        snap = ContextSnapshot.create(
            timestamp="2026-01-01 10:00 IST",
            market_regime="Trending Bullish",
            market_phase="mid_session",
            market_breadth="unknown",
            volatility_state="normal",
            liquidity_state="normal",
            market_session={"is_open": True, "phase": "open"},
            sector_strength={"leader": "IT", "laggard": "FMCG", "ranked": []},
            industry_strength={"status": "GAP"},
            macro_state={"vix_regime": "Normal"},
            global_market_state={"bias": "BULLISH", "spillover_score": 12.0},
            risk_mode="RISK-ON",
            trading_restrictions=["test"],
            confidence=75.0,
        )
        self.assertTrue(snap.snapshot_id.startswith("ctx_"))
        self.assertEqual(len(snap.context_hash), 64)
        self.assertEqual(snap.schema_version, SCHEMA_VERSION)
        with self.assertRaises(Exception):
            snap.risk_mode = "NEUTRAL"  # type: ignore[misc]

    def test_mapping_proxy_immutable(self):
        snap = ContextSnapshot.create(
            timestamp="t",
            market_regime="Unknown",
            market_phase="closed",
            market_breadth="unknown",
            volatility_state="unknown",
            liquidity_state="unknown",
            market_session={"is_open": False},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={},
            risk_mode="CLOSED",
            trading_restrictions=[],
            confidence=50.0,
        )
        self.assertIsInstance(snap.market_session, MappingProxyType)


class TestNormalizer(unittest.TestCase):
    def test_normalize_regime_unknown(self):
        self.assertEqual(normalize_regime(None), "Unknown")

    def test_normalize_volatility_from_vix(self):
        self.assertEqual(normalize_volatility(None, vix_price=22.0), "high_fear")

    def test_normalize_risk_mode_closed(self):
        self.assertEqual(
            normalize_risk_mode(
                session_open=False,
                session_phase="weekend",
                regime="Trending Bullish",
                spillover_score=20.0,
                volatility_state="low",
                allow_new_entries=False,
            ),
            "CLOSED",
        )

    def test_validate_rejects_invalid(self):
        with self.assertRaises(ValueError):
            validate_snapshot_fields(
                market_regime="Bogus",
                market_phase="mid_session",
                market_breadth="unknown",
                volatility_state="unknown",
                liquidity_state="unknown",
                risk_mode="NEUTRAL",
            )


class TestCache(unittest.TestCase):
    def setUp(self):
        clear_cache()

    def test_single_cache_hit(self):
        snap = ContextSnapshot.create(
            timestamp="t",
            market_regime="Unknown",
            market_phase="closed",
            market_breadth="unknown",
            volatility_state="unknown",
            liquidity_state="unknown",
            market_session={"is_open": False},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={},
            risk_mode="CLOSED",
            trading_restrictions=[],
            confidence=50.0,
        )
        put_cached("india", True, snap)
        hit = get_cached("india", True)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.snapshot_id, snap.snapshot_id)

    def test_thread_safe_writes(self):
        errors: list[str] = []

        def writer(i: int):
            try:
                snap = ContextSnapshot.create(
                    timestamp=f"t{i}",
                    market_regime="Unknown",
                    market_phase="closed",
                    market_breadth="unknown",
                    volatility_state="unknown",
                    liquidity_state="unknown",
                    market_session={"is_open": False},
                    sector_strength={},
                    industry_strength={},
                    macro_state={},
                    global_market_state={},
                    risk_mode="CLOSED",
                    trading_restrictions=[],
                    confidence=50.0,
                )
                put_cached("india", True, snap)
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])


class TestComposer(unittest.TestCase):
    def setUp(self):
        clear_cache()

    @patch("analyzer.global_impact.build_india_impact_report")
    @patch("analyzer.india_macro.build_india_macro_snapshot")
    @patch("analyzer.market_regime.detect_nifty_regime")
    @patch("analyzer.intraday_beginner_tips.session_timing_advice")
    @patch("analyzer.market_session.market_session_status")
    def test_compose_from_producers(self, mock_session, mock_timing, mock_regime, mock_macro, mock_global):
        from analyzer.context_engine.composer import compose_context_snapshot
        from analyzer.market_regime import MarketRegime

        mock_session.return_value = {"is_open": True, "phase": "open", "status": "Market OPEN"}
        mock_timing.return_value = MagicMock(
            phase="core", headline="Core session", allow_new_entries=True, prefer_exit=False
        )
        mock_regime.return_value = MarketRegime(
            symbol="^NSEI",
            adx=28.0,
            plus_di=25.0,
            minus_di=18.0,
            regime="Trending Bullish",
            allow_aggressive_intraday=True,
            allow_aggressive_swing=True,
            message="Trend up",
            banner="Bull",
        )
        mock_macro.return_value = MagicMock(
            fetched_at="t",
            vix_regime="Normal",
            india_vix=MagicMock(price=14.0),
            fii_dii=MagicMock(summary="FII bought"),
            premarket_note="",
            sectors=[],
            errors=[],
            sector_leader="IT",
            sector_laggard="FMCG",
        )
        mock_global.return_value = MagicMock(
            fetched_at="t",
            predicted_nifty_bias="Bullish",
            spillover_score=15.0,
            predicted_move_pct=0.3,
            confidence="medium",
            india_action="Lean long",
            drivers=["US"],
            risks=[],
        )

        with (
            patch("analyzer.data_health.build_data_health", return_value=MagicMock(ok_for_live_cockpit=True, warning="")),
            patch("analyzer.prep_status.prep_status_for", return_value={"equity": True, "options": True, "telegram": True, "selection": True}),
            patch("analyzer.earnings_calendar.upcoming_within_days", return_value=[]),
            patch("analyzer.earnings_calendar.fetch_nifty50_earnings", return_value=[]),
        ):
            snap = compose_context_snapshot(include_global=True)
        self.assertIn(snap.risk_mode, {"RISK-ON", "NEUTRAL", "RISK-OFF", "CLOSED"})
        self.assertEqual(snap.market_regime, "Trending Bullish")
        self.assertTrue(snap.snapshot_id)


class TestMigration(unittest.TestCase):
    def test_market_context_from_snapshot(self):
        snap = ContextSnapshot.create(
            timestamp="t",
            market_regime="Trending Bullish",
            market_phase="mid_session",
            market_breadth="unknown",
            volatility_state="normal",
            liquidity_state="normal",
            market_session={"is_open": True},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={"bias": "Bullish"},
            risk_mode="RISK-ON",
            trading_restrictions=["Core session"],
            confidence=80.0,
            metadata={"allow_new_entries": True},
        )
        mc = market_context_from_snapshot(snap)
        self.assertEqual(mc.regime, "Trending Bullish")
        self.assertTrue(mc.session_open)
        self.assertTrue(mc.allow_new_entries)

    def test_evidence_items_from_snapshot(self):
        snap = ContextSnapshot.create(
            timestamp="t",
            market_regime="Range-bound",
            market_phase="mid_session",
            market_breadth="unknown",
            volatility_state="elevated",
            liquidity_state="thin",
            market_session={"is_open": True},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={"spillover_score": -10},
            risk_mode="RISK-OFF",
            trading_restrictions=["Wait"],
            confidence=60.0,
            metadata={"allow_new_entries": False},
        )
        items = evidence_items_from_snapshot(snap)
        self.assertGreaterEqual(len(items), 3)

    def test_decision_metadata_snapshot_id(self):
        from analyzer.decision_engine.migration import attach_decision_to_synthesis
        from analyzer.evidence_engine.models import EvidencePacket
        from analyzer.strategy_synthesis import StrategySynthesis, StrategyVote

        snap = ContextSnapshot.create(
            timestamp="t",
            market_regime="Trending Bullish",
            market_phase="mid_session",
            market_breadth="unknown",
            volatility_state="normal",
            liquidity_state="normal",
            market_session={"is_open": True},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={"bias": "Bullish"},
            risk_mode="RISK-ON",
            trading_restrictions=[],
            confidence=80.0,
            metadata={"allow_new_entries": True},
        )
        syn = StrategySynthesis(
            target="NIFTY CE 24000",
            asset_class="options",
            side="CE",
            pillars=[
                StrategyVote(
                    pillar="timing",
                    category="timing",
                    vote=1.0,
                    weight=0.14,
                    detail="Core session",
                )
            ],
            evidence_packet=EvidencePacket(
                packet_id="pkt_test",
                subject="NIFTY CE 24000",
                subject_type="options",
                created_at="t",
                items=[],
                metadata={},
            ),
        )
        with patch("analyzer.context_engine.build_context_snapshot", return_value=snap):
            attach_decision_to_synthesis(syn)
        if syn.decision_artifact is not None:
            self.assertEqual(syn.decision_artifact.metadata.get("context_snapshot_id"), snap.snapshot_id)


class TestBuildContextSnapshot(unittest.TestCase):
    def setUp(self):
        clear_cache()

    @patch("analyzer.context_engine.compose_context_snapshot")
    def test_build_uses_cache(self, mock_compose):
        snap = ContextSnapshot.create(
            timestamp="t",
            market_regime="Unknown",
            market_phase="closed",
            market_breadth="unknown",
            volatility_state="unknown",
            liquidity_state="unknown",
            market_session={"is_open": False},
            sector_strength={},
            industry_strength={},
            macro_state={},
            global_market_state={},
            risk_mode="CLOSED",
            trading_restrictions=[],
            confidence=50.0,
        )
        mock_compose.return_value = snap
        first = build_context_snapshot(use_cache=True)
        second = build_context_snapshot(use_cache=True)
        self.assertEqual(first.snapshot_id, second.snapshot_id)
        mock_compose.assert_called_once()


class TestBackwardCompat(unittest.TestCase):
    def test_live_ttl_constant(self):
        self.assertEqual(LIVE_TTL_SEC, 60.0)


if __name__ == "__main__":
    unittest.main()
