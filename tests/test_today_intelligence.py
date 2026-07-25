"""P0 Today Command Center tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.home_dashboard import VerdictCanvasState
from ui.components.today_intelligence import (
    _market_gate,
    _market_support_line,
    _pick_best,
    _pick_next_watch,
    _risk_warning_lines,
    _selection_reason,
    build_today_command_center,
    _build_opportunity_views,
)


def _connected_broker() -> BrokerSnapshot:
    return BrokerSnapshot(state="connected", holdings_count=2, last_sync_at="09:15 IST")


class TodayCommandCenterTest(unittest.TestCase):
    def test_build_opportunity_views(self):
        pins = [PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16")]
        rows = _build_opportunity_views(pins, None)
        self.assertEqual(rows[0].ticker, "RELIANCE")
        self.assertEqual(rows[0].rr, 2.3)

    def test_pick_best_prefers_starred(self):
        rows = _build_opportunity_views(
            [
                PinnedPlan("TCS", 100, 95, 110, "2026-07-16"),
                PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16"),
            ],
            None,
        )
        os_report = MagicMock(starred_symbol="RELIANCE")
        best = _pick_best(rows, os_report)
        self.assertIsNotNone(best)
        assert best is not None
        self.assertEqual(best.ticker, "RELIANCE")

    def test_next_watch_is_single_alternate(self):
        rows = _build_opportunity_views(
            [
                PinnedPlan("TCS", 100, 95, 110, "2026-07-16"),
                PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16"),
            ],
            None,
        )
        best = rows[1]
        watch = _pick_next_watch(rows, best)
        self.assertIn("TCS", watch)
        self.assertIn("RELIANCE", watch)

    def test_market_gate_includes_regime(self):
        snapshot = MagicMock(
            market_regime="Bull trend",
            risk_mode="NEUTRAL",
            market_phase="regular",
            volatility_state="normal",
            market_breadth="mixed",
            liquidity_state="normal",
            trading_restrictions=(),
        )
        gate = _market_gate(snapshot)
        self.assertIn("Bull trend", gate)

    def test_risk_warnings_include_loss_streak(self):
        mis = MagicMock(
            flags=(),
            loss_streak_days=3,
            mtf_summary="",
            flow_summary="",
            synthesis_summary="",
        )
        snapshot = MagicMock(trading_restrictions=())
        lines = _risk_warning_lines(mis, snapshot, broker=_connected_broker())
        self.assertTrue(any("losing days" in line for line in lines))

    def test_command_center_trade_recommendation_names_symbol(self):
        state = VerdictCanvasState("trade", "Trade", "See the plan", "plan")
        snapshot = MagicMock(
            market_regime="",
            risk_mode="NEUTRAL",
            market_phase="regular",
            market_breadth="",
            volatility_state="",
            liquidity_state="",
            trading_restrictions=(),
            sector_strength={},
        )
        mis = MagicMock(
            flags=(),
            loss_streak_days=0,
            mtf_summary="",
            flow_summary="",
            synthesis_summary="",
        )
        os_report = MagicMock(
            starred_symbol="RELIANCE",
            next_step="",
            max_loss_inr=1000,
            module=lambda _k: None,
        )
        prefs = MagicMock(capital=100_000, max_risk_pct=1.0)
        center = build_today_command_center(
            state=state,
            snapshot=snapshot,
            mis=mis,
            os_report=os_report,
            pins=[PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16")],
            pulse=None,
            portfolio=None,
            prefs=prefs,
            broker=_connected_broker(),
        )
        self.assertIn("RELIANCE", center.opportunity_name)
        self.assertIn("RELIANCE", center.ai_recommendation)
        self.assertIn("Buy above", center.entry_direction)

    def test_market_gate_excludes_restrictions(self):
        snapshot = MagicMock(
            market_regime="Bull trend",
            risk_mode="NEUTRAL",
            market_phase="regular",
            volatility_state="normal",
            market_breadth="mixed",
            liquidity_state="normal",
            trading_restrictions=("No new longs until 10:15",),
        )
        gate = _market_gate(snapshot)
        self.assertNotIn("No new longs", gate)

    def test_connect_state_drops_broker_offline_risk(self):
        state = VerdictCanvasState("connect", "Connect", "Connect Zerodha", "connect")
        snapshot = MagicMock(
            market_regime="",
            risk_mode="NEUTRAL",
            market_phase="regular",
            market_breadth="",
            volatility_state="",
            liquidity_state="",
            trading_restrictions=(),
            sector_strength={},
        )
        mis = MagicMock(
            flags=(),
            loss_streak_days=0,
            mtf_summary="",
            flow_summary="",
            synthesis_summary="",
        )
        os_report = MagicMock(starred_symbol="", next_step="", max_loss_inr=0, module=lambda _k: None)
        prefs = MagicMock(capital=0, max_risk_pct=0)
        center = build_today_command_center(
            state=state,
            snapshot=snapshot,
            mis=mis,
            os_report=os_report,
            pins=[],
            pulse=None,
            portfolio=None,
            prefs=prefs,
            broker=BrokerSnapshot(state="disconnected"),
        )
        self.assertIn("not linked", center.portfolio_lines[0].lower())
        self.assertFalse(center.risk_warnings)

    def test_risk_warnings_exclude_decision_reason(self):
        mis = MagicMock(
            flags=(),
            loss_streak_days=0,
            mtf_summary="",
            flow_summary="",
            synthesis_summary="",
        )
        snapshot = MagicMock(trading_restrictions=())
        lines = _risk_warning_lines(mis, snapshot, broker=_connected_broker())
        self.assertFalse(any("choppy" in line for line in lines))

    def test_market_support_blocks_entries_before_gate(self):
        snapshot = MagicMock(
            market_regime="Neutral trend",
            risk_mode="NEUTRAL",
            market_phase="opening",
            volatility_state="normal",
            trading_restrictions=("Wait until 9:45 IST before new entries",),
            metadata={"allow_new_entries": False},
        )
        os_report = MagicMock(module=lambda _k: None)
        line = _market_support_line(snapshot, os_report)
        self.assertIn("9:45", line)

    def test_selection_reason_starred(self):
        best = _build_opportunity_views(
            [PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16")],
            None,
        )[0]
        strat = MagicMock(headline="Breakout above opening range", detail="Breakout above opening range")
        stock = MagicMock(detail="Best ranked pick in tonight's list (⭐ = your selection).")

        def module(key):
            if key == "strategy":
                return strat
            if key == "stock":
                return stock
            return None

        os_report = MagicMock(starred_symbol="RELIANCE", module=module)
        reason = _selection_reason(best, os_report)
        self.assertIn("starred", reason.lower())

    def test_do_next_uses_os_next_step(self):
        from ui.components.today_intelligence import _ai_recommendation

        state = VerdictCanvasState("wait", "Wait", "You're done for today", "done")
        best = _build_opportunity_views(
            [PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16")],
            None,
        )[0]
        os_report = MagicMock(
            next_step="Wait until 9:45 IST — observe opening range first.",
            max_loss_inr=0,
            module=lambda _k: None,
        )
        mis = MagicMock(summary="", flags=())
        prefs = MagicMock(capital=100_000, max_risk_pct=1.0)
        text = _ai_recommendation(
            state,
            os_report=os_report,
            mis=mis,
            decision=None,
            best=best,
            risk_warnings=(),
            prefs=prefs,
        )
        self.assertIn("9:45", text)

    def test_do_next_uses_os_next_step_even_in_connect_state(self):
        from ui.components.today_intelligence import _ai_recommendation

        state = VerdictCanvasState("connect", "Connect", "Connect Zerodha", "connect")
        os_report = MagicMock(
            next_step="Link Zerodha first, then review tonight's scan.",
            max_loss_inr=0,
            module=lambda _k: None,
        )
        mis = MagicMock(summary="", flags=())
        prefs = MagicMock(capital=100_000, max_risk_pct=1.0)
        text = _ai_recommendation(
            state,
            os_report=os_report,
            mis=mis,
            decision=None,
            best=None,
            risk_warnings=(),
            prefs=prefs,
        )
        self.assertIn("tonight's scan", text)
        self.assertNotIn("One Zerodha link unlocks", text)


if __name__ == "__main__":
    unittest.main()
