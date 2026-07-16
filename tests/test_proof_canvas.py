"""Proof Canvas mapper and SVG tests."""

from __future__ import annotations

import re
import unittest
from unittest.mock import MagicMock, patch

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.proof_mapper import build_structure_proof, _assert_human_label
from ui.components.proof_models import StructureProof, ZoneAnnotation, PriceMarkers
from ui.components.proof_svg import render_proof_svg

_BANNED = re.compile(r"\b(support|resistance|ema|rsi|macd|fibonacci)\b", re.I)


def _cached(*, verdict_key: str = "trade") -> dict:
    snap = ContextSnapshot(
        timestamp="t",
        market_regime="n",
        market_phase="regular",
        market_breadth="m",
        volatility_state="n",
        liquidity_state="n",
        market_session={"phase": "regular"},
        sector_strength={},
        industry_strength={},
        macro_state={},
        global_market_state={},
        risk_mode="NEUTRAL",
        trading_restrictions=(),
        confidence=0.8,
    )
    decision = DecisionArtifact(
        decision_id="d1",
        timestamp="",
        verdict=DecisionVerdict.ACT,
        reason="Momentum confirms after opening range.",
        evidence_packet_id="",
        confidence=0.8,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        trade_allowed=True,
    )
    pin = PinnedPlan(
        symbol="RELIANCE",
        entry=2850.0,
        stop_loss=2815.0,
        target=2930.0,
        prep_date="2026-07-16",
        side="LONG",
    )
    mis = MisTradeAdvisory(
        verdict="TRADE_OK",
        emoji="",
        headline="",
        summary="Balanced.",
        score=70,
        flags=(),
        loss_streak_days=0,
    )
    os_report = InvestmentOS(starred_symbol="RELIANCE", next_step="")
    setattr(os_report, "decision_artifact", decision)
    broker = BrokerSnapshot(state="connected")
    return {
        "snapshot": snap.as_dict(),
        "mis": mis,
        "os_report": os_report,
        "pins": [pin],
        "prefs": IntradayPrefs(capital=100_000, max_risk_pct=1.8),
        "broker": broker.to_dict(),
        "built_at": "14:32 IST",
    }


class ProofMapperTest(unittest.TestCase):
    @patch("ui.components.proof_mapper._fetch_candles", return_value=())
    @patch("ui.components.proof_mapper._current_price", return_value=2862.0)
    def test_trade_mode_mentor_before_zones(self, *_mocks):
        proof = build_structure_proof(
            market="india",
            cached=_cached(),
            proof_mode="trade",
            origin="trades",
        )
        self.assertEqual(proof.proof_mode, "trade")
        self.assertIn("Buyers regained control", proof.mentor_line)
        self.assertTrue(proof.zones)
        self.assertIsNotNone(proof.markers.entry)
        self.assertEqual(proof.primary_label, "Back to Trades")

    @patch("ui.components.proof_mapper._fetch_candles", return_value=())
    @patch("ui.components.proof_mapper._current_price", return_value=2862.0)
    def test_wait_mode_danger_zone(self, *_mocks):
        cached = _cached()
        cached["mis"] = MisTradeAdvisory(
            verdict="NO_TRADE",
            emoji="",
            headline="",
            summary="Wait.",
            score=40,
            flags=("Extended tape",),
            loss_streak_days=0,
        )
        setattr(cached["os_report"], "decision_artifact", None)
        proof = build_structure_proof(
            market="india",
            cached=cached,
            proof_mode="wait",
            origin="today",
        )
        kinds = {z.kind for z in proof.zones}
        self.assertIn("danger", kinds)
        for z in proof.zones:
            self.assertFalse(_BANNED.search(z.human_label))

    @patch("ui.components.proof_mapper._fetch_candles", return_value=())
    @patch("ui.components.proof_mapper._current_price", return_value=100.0)
    def test_fossil_mode(self, *_mocks):
        proof = build_structure_proof(
            market="india",
            cached=_cached(),
            proof_mode="fossil",
            origin="trust",
            fossil_date="2026-07-10",
            miss_note="tightened my breakout confirmation rule",
        )
        self.assertEqual(proof.proof_mode, "fossil")
        self.assertIsNotNone(proof.fossil_badge)
        self.assertIn("rallied anyway", proof.mentor_line.lower())

    def test_human_label_bans_jargon(self):
        self.assertNotIn("support", _assert_human_label("Support at 100").lower())

    def test_svg_renders_zones(self):
        proof = StructureProof(
            symbol="RELIANCE",
            verdict_state="trade",
            proof_mode="trade",
            echo_line="echo",
            mentor_line="mentor",
            action_line="action",
            zones=(
                ZoneAnnotation("reward", 2930, 2850, "This is where buyers regain control"),
            ),
            markers=PriceMarkers(entry=2850, stop=2815, target=2930, current=2862),
            price_min=2800,
            price_max=2950,
        )
        html_out = render_proof_svg(proof)
        self.assertIn("proof-frame", html_out)
        self.assertIn("buyers regain control", html_out)
        self.assertNotIn("Resistance", html_out)


if __name__ == "__main__":
    unittest.main()
