"""APEX-012 Phase 2a — Review Setup navigates via canonical MorningBriefViewModel symbol."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.market_pulse_scan import MarketPulseReport, StockPulseEntry
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_assembly import assemble_morning_brief_view_model
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.canvas_utils import VerdictCanvasState
from ui.components.decision_card import (
    BestOpportunityView,
    DecisionCardViewModel,
    hero_review_setup_symbol,
    project_decision_card,
    resolve_hero_review_nav_symbol,
)
from ui.components.today_intelligence import (
    TodayCommandCenter,
    build_today_command_center,
    render_today_command_center,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _snapshot() -> ContextSnapshot:
    return ContextSnapshot(
        timestamp="2026-08-05T09:00:00+05:30",
        market_regime="Neutral",
        market_phase="regular",
        market_breadth="mixed",
        volatility_state="normal",
        liquidity_state="normal",
        market_session=MappingProxyType({"phase": "regular", "is_open": True}),
        sector_strength=MappingProxyType({}),
        industry_strength=MappingProxyType({}),
        macro_state=MappingProxyType({}),
        global_market_state=MappingProxyType({}),
        risk_mode="NEUTRAL",
        trading_restrictions=(),
        confidence=0.85,
        snapshot_id="ctx1",
        context_hash="",
    )


def _trade_brief(*, starred: str, pins: list[PinnedPlan]):
    art = DecisionArtifact(
        decision_id="d1",
        timestamp="2026-08-05T09:00:00",
        verdict=DecisionVerdict.ACT,
        reason="RELIANCE lines up with structure and timing.",
        evidence_packet_id="ep1",
        confidence=0.85,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        trade_allowed=True,
    )
    packet = MagicMock(
        items=[
            MagicMock(
                label="Regime",
                category=MagicMock(value="Market"),
                type=MagicMock(value="FACT"),
                source=MagicMock(value="internal_model"),
                confidence=MagicMock(value="high"),
                value="Trend",
                explanation="",
            )
        ],
        conflicts=[],
        gaps=[],
    )
    return assemble_morning_brief_view_model(
        market="NSE",
        context=_snapshot(),
        decision=art,
        decision_source="equity",
        broker=BrokerSnapshot(state="connected", holdings_count=2),
        mis=MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
        os_report=InvestmentOS(starred_symbol=starred, next_step="Buy above ₹2,850"),
        pins=pins,
        prefs=IntradayPrefs(capital=100_000, max_risk_pct=1.8),
        built_at="09:12 IST",
        scenario=MorningBriefScenario.NORMAL,
        stale=False,
        stale_reason="",
        context_from_cache=False,
        context_cache_age=None,
        data_error="",
        evidence_packet=packet,
    )


def _minimal_center(*, best_ticker: str) -> TodayCommandCenter:
    return TodayCommandCenter(
        opportunity_name="",
        entry_direction="",
        selection_reason="",
        price_status="",
        market_gate="",
        market_support="",
        portfolio_lines=(),
        risk_warnings=(),
        next_watch="",
        ai_recommendation="",
        best_ticker=best_ticker,
    )


class TestReviewSetupNavSymbol(unittest.TestCase):
    def test_hero_review_setup_symbol_from_card(self):
        brief = _trade_brief(starred="RELIANCE", pins=[PinnedPlan("TCS", 4100, 4050, 4200, "2026-07-16")])
        card = project_decision_card(brief)
        self.assertEqual(hero_review_setup_symbol(card), "RELIANCE")

    def test_canonical_symbol_overrides_legacy_best_ticker(self):
        self.assertEqual(
            resolve_hero_review_nav_symbol(review_symbol="RELIANCE", legacy_best_ticker="TCS"),
            "RELIANCE",
        )

    def test_legacy_used_only_when_review_symbol_not_provided(self):
        self.assertEqual(
            resolve_hero_review_nav_symbol(review_symbol=None, legacy_best_ticker="TCS"),
            "TCS",
        )

    def test_matching_symbols_resolve_same(self):
        self.assertEqual(
            resolve_hero_review_nav_symbol(review_symbol="RELIANCE", legacy_best_ticker="RELIANCE"),
            "RELIANCE",
        )


class TestReviewSetupNavigation(unittest.TestCase):
    def test_render_review_setup_navigates_to_review_symbol(self):
        center = _minimal_center(best_ticker="TCS")
        state = VerdictCanvasState("trade", "Trade", "See the plan", "plan")
        cached = {
            "snapshot": _snapshot(),
            "mis": MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
            "os_report": InvestmentOS(starred_symbol="RELIANCE"),
            "pins": [],
            "prefs": IntradayPrefs(capital=50_000, max_risk_pct=1.0),
        }
        with patch("ui.components.today_intelligence.st") as mock_st, patch(
            "ui.components.today_intelligence._go_symbol"
        ) as mock_go:
            mock_st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
            mock_st.button.return_value = True
            render_today_command_center(
                state=state,
                market="NSE",
                cached=cached,
                broker=BrokerSnapshot(state="connected"),
                sections=(),
                include_actions=True,
                center=center,
                review_symbol="RELIANCE",
            )
            mock_go.assert_called_once_with("RELIANCE")

    def test_legacy_center_best_ticker_not_used_when_review_symbol_set(self):
        center = _minimal_center(best_ticker="TCS")
        nav = resolve_hero_review_nav_symbol(review_symbol="RELIANCE", legacy_best_ticker=center.best_ticker)
        self.assertNotEqual(nav, center.best_ticker)
        self.assertEqual(nav, "RELIANCE")


class TestPhase2aWiring(unittest.TestCase):
    def test_today_brief_uses_review_symbol_from_card(self):
        text = (REPO_ROOT / "ui/components/today_brief_experience.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("hero_review_setup_symbol(card)", text)


class TestCardContract(unittest.TestCase):
    def test_hidden_opportunity_yields_no_review_symbol(self):
        card = DecisionCardViewModel(
            verdict_word="Wait",
            verdict_key="wait",
            reason="Wait",
            confidence_level=50,
            confidence_band="medium",
            last_updated="",
            valid_until="",
            portfolio_ready=True,
            portfolio_status="",
            sync_label="Synced",
            sync_state="ok",
            best_opportunity=None,
            risk_level="low",
            coach_message="",
            cta_label="Done",
            cta_action="done",
            scenario="normal",
            stale=False,
            stale_label="",
            trust_summary="",
            evidence_teaser=(),
            broker_connected=True,
            cash_available_inr=None,
            last_sync="",
            decision_verdict="WAIT",
            failure_message=None,
        )
        self.assertIsNone(hero_review_setup_symbol(card))


if __name__ == "__main__":
    unittest.main()
