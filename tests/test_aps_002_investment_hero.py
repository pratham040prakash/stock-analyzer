"""APS-002 Investment Hero — recommendation projection and freshness tests."""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime
from types import MappingProxyType
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief_assembly import assemble_morning_brief_view_model
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.decision_card import project_decision_card
from ui.components.investment_hero_experience import (
    investment_display_name,
    investment_review_time_label,
    investment_review_why_line,
    render_investment_hero_experience,
)
from ui.components.morning_brief_ui import (
    RecommendationContract,
    answer_key_from_brief,
    human_review_freshness_label,
    recommendation_contract_from_brief,
)

IST = ZoneInfo("Asia/Kolkata")


def _snapshot(**overrides) -> ContextSnapshot:
    base = dict(
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
        confidence=0.72,
        snapshot_id="ctx1",
        context_hash="",
    )
    base.update(overrides)
    return ContextSnapshot(**base)


def _build_brief(**overrides):
    decision = overrides.get("decision")
    if decision is None and overrides.get("with_decision"):
        decision = DecisionArtifact(
            decision_id="d1",
            timestamp="2026-08-05T09:00:00",
            verdict=DecisionVerdict.ACT,
            reason="RELIANCE lines up with structure and timing.",
            evidence_packet_id="ep1",
            confidence=0.85,
            uncertainty=UncertaintyVector(),
            capital_recommendation="Size within risk budget.",
            execution_recommendation="Buy above trigger only.",
            trade_allowed=True,
        )
    return assemble_morning_brief_view_model(
        market="NSE",
        context=overrides.get("snapshot", _snapshot()),
        decision=decision,
        decision_source=overrides.get("decision_source", "equity"),
        broker=overrides.get("broker", BrokerSnapshot(state="connected", holdings_count=2)),
        mis=overrides.get(
            "mis",
            MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
        ),
        os_report=overrides.get("os_report", InvestmentOS(starred_symbol="RELIANCE")),
        pins=[],
        prefs=MagicMock(capital=50000),
        built_at="09:12 IST",
        scenario=overrides.get("scenario", MorningBriefScenario.NORMAL),
        stale=overrides.get("stale", False),
        stale_reason=overrides.get("stale_reason", ""),
        context_from_cache=False,
        context_cache_age=None,
        data_error=overrides.get("data_error", ""),
        evidence_packet=overrides.get("evidence_packet"),
    )


def _trade_brief(**overrides):
    art = overrides.get(
        "decision",
        DecisionArtifact(
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
        ),
    )
    packet = overrides.get(
        "evidence_packet",
        MagicMock(
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
        ),
    )
    return assemble_morning_brief_view_model(
        market="NSE",
        context=overrides.get("snapshot", _snapshot()),
        decision=art,
        decision_source=overrides.get("decision_source", "equity"),
        broker=overrides.get("broker", BrokerSnapshot(state="connected", holdings_count=2)),
        mis=overrides.get(
            "mis",
            MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
        ),
        os_report=overrides.get("os_report", InvestmentOS(starred_symbol="RELIANCE")),
        pins=overrides.get("pins", [PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16")]),
        prefs=MagicMock(capital=50000),
        built_at="09:12 IST",
        scenario=overrides.get("scenario", MorningBriefScenario.NORMAL),
        stale=overrides.get("stale", False),
        stale_reason=overrides.get("stale_reason", ""),
        context_from_cache=False,
        context_cache_age=None,
        data_error=overrides.get("data_error", ""),
        evidence_packet=packet,
    )


class APS002HeroProjectionTest(unittest.TestCase):
    def test_investment_name_from_review_symbol(self):
        brief = _trade_brief()
        card = project_decision_card(brief)
        name = investment_display_name(
            card=card,
            plan_symbol=None,
            os_report=InvestmentOS(starred_symbol="TCS"),
        )
        self.assertEqual(name, "RELIANCE")

    def test_recommendation_badge_from_brief_not_ui_logic(self):
        brief = _trade_brief()
        key, label = answer_key_from_brief(brief)
        self.assertEqual(key, "buy")
        self.assertEqual(label, "Buy")

    def test_review_why_hidden_when_unavailable(self):
        brief = _build_brief(
            decision=DecisionArtifact(
                decision_id="d1",
                timestamp="2026-08-05T09:00:00",
                verdict=DecisionVerdict.WAIT,
                reason="",
                evidence_packet_id="",
                confidence=0.5,
                uncertainty=UncertaintyVector(),
                capital_recommendation="",
                execution_recommendation="",
            ),
            os_report=InvestmentOS(),
        )
        brief = replace(brief, trust=replace(brief.trust, why_this_is_recommended=""))
        card = project_decision_card(brief)
        card = replace(card, reason="")
        contract = RecommendationContract(
            why=(),
            evidence=(),
            trade_offs=(),
            risks=(),
            what_could_change=(),
            suggested_next_step=(),
            help_simple=(),
            help_business=(),
            help_professional=(),
        )
        self.assertEqual(
            investment_review_why_line(card=card, contract=contract, brief=brief),
            "",
        )

    def test_review_time_fallback_quick_review(self):
        card = project_decision_card(_build_brief(with_decision=True))
        with patch(
            "ui.components.investment_hero_experience._review_time_minutes",
            return_value="",
        ):
            self.assertEqual(investment_review_time_label(card), "Quick Review")

    def test_human_freshness_refreshing(self):
        self.assertEqual(
            human_review_freshness_label(
                built_at="09:12 IST",
                last_updated="2026-08-05T09:00:00",
                stale=False,
                stale_label="",
                refreshing=True,
            ),
            "Reviewed just now · updating",
        )

    def test_human_freshness_minutes_ago(self):
        fixed_now = datetime(2026, 8, 5, 9, 30, tzinfo=IST)
        with patch("ui.components.morning_brief_ui.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            label = human_review_freshness_label(
                built_at="09:12 IST",
                last_updated="2026-08-05T09:15:00",
                stale=False,
                stale_label="",
                refreshing=False,
            )
        self.assertEqual(label, "Reviewed 15 minutes ago")

    def test_human_freshness_offline(self):
        self.assertIn(
            "offline",
            human_review_freshness_label(
                built_at="09:12 IST",
                last_updated="",
                stale=False,
                stale_label="",
                refreshing=False,
                offline=True,
            ).lower(),
        )


class APS002HeroRenderTest(unittest.TestCase):
    def test_render_includes_required_hero_sections(self):
        brief = _trade_brief()
        card = project_decision_card(brief)
        cached = {"built_at": "09:12 IST", "prefs": MagicMock(capital=50000)}
        html_chunks: list[str] = []

        def capture(markdown, **kwargs):
            html_chunks.append(str(markdown))

        with patch("ui.components.investment_hero_experience.st") as mock_st:
            mock_st.markdown.side_effect = capture
            mock_st.columns.return_value = (MagicMock(), MagicMock())
            mock_st.button.return_value = False
            mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
            mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
            render_investment_hero_experience(
                cached=cached,
                brief=brief,
                card=card,
                broker=BrokerSnapshot(state="connected"),
                snapshot=_snapshot(),
                mis=MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
                domain_decision=None,
                pins=[],
                os_report=InvestmentOS(starred_symbol="RELIANCE"),
                prefs=MagicMock(capital=50000),
                pulse=None,
                portfolio=None,
                journal_today_pnl=None,
                plan_symbol="RELIANCE",
            )

        joined = "\n".join(html_chunks)
        self.assertIn("apex-inv-name", joined)
        self.assertIn("apex-inv-badge", joined)
        self.assertIn("Today", joined)
        self.assertIn("status", joined)
        self.assertIn("Recommendation", joined)
        self.assertIn("Decision confidence", joined)
        self.assertIn("Review time", joined)
        self.assertIn("apex-inv-fresh", joined)

    def test_render_surfaces_failure_message(self):
        brief = _build_brief(with_decision=True, data_error="Market data unavailable")
        card = project_decision_card(brief)
        html_chunks: list[str] = []

        with patch("ui.components.investment_hero_experience.st") as mock_st:
            mock_st.markdown.side_effect = lambda md, **kw: html_chunks.append(str(md))
            mock_st.columns.return_value = (MagicMock(), MagicMock())
            mock_st.button.return_value = False
            mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
            mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
            render_investment_hero_experience(
                cached={"built_at": "09:12 IST"},
                brief=brief,
                card=card,
                broker=BrokerSnapshot(state="connected"),
                snapshot=_snapshot(),
                mis=MisTradeAdvisory(verdict="NO_TRADE", emoji="", headline="", summary="", score=40),
                domain_decision=None,
                pins=[],
                os_report=InvestmentOS(),
                prefs=MagicMock(),
                pulse=None,
                portfolio=None,
                journal_today_pnl=None,
            )

        joined = "\n".join(html_chunks)
        if card.failure_message:
            self.assertIn("apex-failure", joined)


class APS002PlanCanvasWiringTest(unittest.TestCase):
    def test_plan_canvas_uses_decision_context_bundle(self):
        from pathlib import Path

        text = (Path(__file__).resolve().parent.parent / "ui/components/plan_canvas.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("DecisionContextBundle.from_cache_dict", text)
        self.assertIn("render_investment_hero_experience", text)
        self.assertNotIn("_broker_snapshot()", text)


if __name__ == "__main__":
    unittest.main()
