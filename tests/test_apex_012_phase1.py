"""APEX-012 Phase 1 — Hero Opportunity intel migrates to MorningBriefViewModel."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock

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
    compose_hero_intel_html,
    project_decision_card,
    project_opportunity_intel_html,
)
from ui.components.today_intelligence import build_today_command_center

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


class TestHeroOpportunityFromBrief(unittest.TestCase):
    """Invariant: hero Opportunity block uses MBVM symbol, not today_intelligence ranking."""

    def test_project_opportunity_intel_uses_brief_symbol(self):
        brief = _trade_brief(starred="RELIANCE", pins=[PinnedPlan("TCS", 4100, 4050, 4200, "2026-07-16")])
        card = project_decision_card(brief)
        html = project_opportunity_intel_html(card)
        self.assertIn("RELIANCE", html)
        self.assertNotIn("TCS", html)
        self.assertIn("Opportunity", html)

    def test_hero_opportunity_differs_from_command_center_ranking(self):
        """Starred symbol not in pins: brief=RELIANCE, legacy center picks TCS."""
        pins = [PinnedPlan("TCS", 4100, 4050, 4200, "2026-07-16")]
        brief = _trade_brief(starred="RELIANCE", pins=pins)
        card = project_decision_card(brief)
        state = VerdictCanvasState(
            card.verdict_key, card.verdict_word, card.cta_label, card.cta_action
        )
        pulse = MarketPulseReport(
            indices=[],
            market_verdict="Neutral",
            index_options=[],
            top_stocks=[],
            stock_map={
                "TCS": StockPulseEntry(
                    symbol="TCS.NS",
                    nse_symbol="TCS",
                    name="TCS",
                    price=4110.0,
                    combined_rec="BUY",
                    combined_score=92.0,
                    what_to_do="Breakout watch",
                    ltp_source="live",
                )
            },
        )
        center = build_today_command_center(
            state=state,
            snapshot=_snapshot(),
            mis=MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
            os_report=InvestmentOS(starred_symbol="RELIANCE", next_step=""),
            pins=pins,
            pulse=pulse,
            portfolio=None,
            prefs=IntradayPrefs(capital=100_000, max_risk_pct=1.8),
            broker=BrokerSnapshot(state="connected", holdings_count=2),
        )
        self.assertEqual(center.best_ticker, "TCS")
        self.assertIn("TCS", center.opportunity_name)
        opp_html = project_opportunity_intel_html(card)
        self.assertIn("RELIANCE", opp_html)
        self.assertNotIn("TCS", opp_html)

    def test_compose_hero_intel_prefers_brief_for_opportunity_section(self):
        brief = _trade_brief(starred="RELIANCE", pins=[PinnedPlan("TCS", 4100, 4050, 4200, "2026-07-16")])
        card = project_decision_card(brief)
        legacy = '<div class="vc-intel-stack vc-intel-stack-hero"><section>Risk legacy</section></div>'
        html = compose_hero_intel_html(
            card=card,
            legacy_intel_html=legacy,
            sections=("opportunity", "risk"),
        )
        self.assertIn("RELIANCE", html)
        self.assertNotIn("TCS", html)
        self.assertIn("Risk legacy", html)


class TestPhase1Wiring(unittest.TestCase):
    """Invariant: home_dashboard delegates Today surface to V2 brief experience."""

    def test_home_dashboard_delegates_to_today_brief_experience(self):
        text = (REPO_ROOT / "ui/components/home_dashboard.py").read_text(encoding="utf-8")
        self.assertIn("render_today_brief_experience", text)
        self.assertNotIn("compose_hero_intel_html", text)


if __name__ == "__main__":
    unittest.main()
