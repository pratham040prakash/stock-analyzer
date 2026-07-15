"""Tests for unified strategy synthesis."""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from analyzer.strategy_synthesis import (
    StrategySynthesis,
    _confidence_pct,
    _weighted_net,
    format_synthesis_terminal,
    synthesize_options,
)

IST = ZoneInfo("Asia/Kolkata")


def _mock_context(*, allow_entries: bool = False, regime: str = "Range-bound"):
    from analyzer.context_engine.models import ContextSnapshot

    return ContextSnapshot.create(
        timestamp="2026-07-13 09:30 IST",
        market_regime=regime,
        market_phase="opening",
        market_breadth="unknown",
        volatility_state="normal",
        liquidity_state="normal",
        market_session={"is_open": True, "phase": "open"},
        sector_strength={},
        industry_strength={},
        macro_state={"vix_regime": "Normal"},
        global_market_state={"bias": "Neutral", "india_action": "NEUTRAL — wait"},
        risk_mode="NEUTRAL",
        trading_restrictions=["Before 9:45 — observe"] if not allow_entries else [],
        confidence=70.0,
        metadata={
            "allow_new_entries": allow_entries,
            "prefer_exit": False,
            "regime_detail": {"adx": 12.0},
        },
    )


class TestStrategySynthesis(unittest.TestCase):
    def test_weighted_net_empty(self):
        self.assertEqual(_weighted_net([]), 0.0)

    def test_confidence_pct_bounds(self):
        self.assertGreaterEqual(_confidence_pct(0.0, []), 0)
        self.assertLessEqual(_confidence_pct(0.0, []), 100)

    def test_format_synthesis_terminal(self):
        syn = StrategySynthesis(
            target="NIFTY CE 24000",
            asset_class="options",
            side="CE",
            verdict="WAIT",
            confidence_pct=40,
            headline="Wait",
            pillars=[],
        )
        lines = format_synthesis_terminal(syn)
        self.assertTrue(any("SYNTHESIS" in ln for ln in lines))

    @patch("analyzer.decision_engine.migration.attach_decision_to_synthesis")
    @patch("analyzer.evidence_engine.migration.attach_synthesis_evidence")
    @patch("analyzer.sideways_options_advisor.advise_from_chain")
    @patch("analyzer.nse_options.fetch_option_chain")
    @patch("analyzer.gift_nifty.fetch_gift_nifty_cue", return_value=None)
    @patch("analyzer.options_flow_snapshot.fetch_index_flow")
    @patch("analyzer.multi_timeframe.index_mtf")
    @patch("analyzer.options_entry_gate.assess_option_entry_gate")
    @patch("analyzer.opening_range_confirm.fetch_symbol_opening_range", return_value=(100.0, 99.0))
    @patch("analyzer.providers.get_live_ltp", return_value=(100.5, None))
    @patch("analyzer.context_engine.build_context_snapshot")
    @patch("analyzer.options_reversal_alerts.assess_option_index_thesis")
    def test_synthesize_options_blocks_before_gate(
        self,
        mock_rev,
        mock_ctx,
        mock_ltp,
        mock_or,
        mock_gate,
        mock_mtf,
        mock_flow,
        mock_gift,
        mock_chain,
        mock_side,
        _mock_evidence,
        mock_decision,
    ):
        from analyzer.multi_timeframe import MultiTimeframeReport, TimeframeSnapshot
        from analyzer.options_entry_gate import OptionsEntryGate
        from analyzer.options_flow_snapshot import OptionsFlowSnapshot
        from analyzer.options_reversal_alerts import IndexReversalStatus

        mock_ctx.return_value = _mock_context(allow_entries=False)
        mock_gate.return_value = OptionsEntryGate(
            fno_symbol="NIFTY",
            option_type="CE",
            strike=24000.0,
            spot=100.5,
            or_high=100.0,
            or_low=99.0,
            otm_pct=0.5,
            phase="observe",
            allowed=False,
            emoji="🟡",
            headline="Before 9:45",
            detail="",
            action="WAIT",
        )
        mock_mtf.return_value = MultiTimeframeReport(
            symbol="NIFTY",
            label="NIFTY",
            frames=[
                TimeframeSnapshot(
                    interval="5m",
                    action="WAIT",
                    confidence="low",
                    score=0.0,
                    vwap=None,
                    session_bias="",
                    candle_type="",
                    volume_note="",
                    error=None,
                )
            ],
            alignment_pct=40,
            consensus_action="WAIT",
            summary="Mixed",
        )
        mock_flow.return_value = OptionsFlowSnapshot(
            fno_symbol="NIFTY",
            pcr_oi=1.0,
            pcr_change=0.0,
            iv_rank=70.0,
            iv_band="expensive",
            summary="IV high",
        )
        mock_rev.return_value = IndexReversalStatus(
            fno_symbol="NIFTY",
            option_type="CE",
            strike=24000.0,
            index_label="NIFTY",
            spot=100.5,
            or_high=100.0,
            or_low=99.0,
            phase="observe",
            label="Observe",
            emoji="🟡",
            detail="Wait for OR break",
            opposite_side="PE",
            action="WAIT",
        )
        mock_side.return_value = MagicMock(blocks_directional=False, headline="OK")

        def _apply_decision(syn):
            syn.verdict = "WAIT"
            syn.trade_allowed = False
            syn.confidence_pct = 40

        mock_decision.side_effect = _apply_decision

        syn = synthesize_options(
            "NIFTY",
            "CE",
            24000.0,
            now=datetime(2026, 7, 13, 9, 30, tzinfo=IST),
        )
        self.assertEqual(syn.asset_class, "options")
        self.assertIn(syn.verdict, ("NO_TRADE", "CAUTION", "WAIT"))
        self.assertLess(syn.confidence_pct, 55)
        self.assertGreaterEqual(len(syn.pillars), 5)
        self.assertFalse(syn.trade_allowed)


if __name__ == "__main__":
    unittest.main()
