"""V3-201 — Research Workspace contracts and render integration."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.watchlist_pins import PinnedPlan
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.research_workspace_experience import (
    render_investment_decision_panel,
    render_investment_view_hero,
    render_research_context_header,
    render_research_handoff_footer,
    render_research_question_navigator,
    render_research_question_panel,
    render_research_workbench_experience,
)
from ui.components.research_workspace_ui import (
    DISPOSITION_LABELS,
    RESEARCH_QUESTIONS,
    research_question_understand_contract,
    research_workspace_from_inputs,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _holding(symbol: str, qty: int, avg: float, ltp: float, pnl: float) -> ZerodhaHolding:
    return ZerodhaHolding(
        kite_symbol=f"NSE:{symbol}-EQ",
        tradingsymbol=symbol,
        exchange="NSE",
        quantity=qty,
        average_price=avg,
        last_price=ltp,
        pnl=pnl,
        yahoo_symbol=f"{symbol}.NS",
    )


def _sample_cached(broker: BrokerSnapshot):
    snap = ContextSnapshot(
        timestamp="2026-08-06T09:00:00+05:30",
        market_regime="Neutral",
        market_phase="regular",
        market_breadth="mixed",
        volatility_state="normal",
        liquidity_state="normal",
        market_session=MappingProxyType({"phase": "regular", "is_open": True, "date": "2026-08-06"}),
        sector_strength=MappingProxyType({}),
        industry_strength=MappingProxyType({}),
        macro_state=MappingProxyType({}),
        global_market_state=MappingProxyType({}),
        risk_mode="NEUTRAL",
        trading_restrictions=(),
        confidence=0.85,
        snapshot_id="ctx-research",
        context_hash="",
    )
    art = DecisionArtifact(
        decision_id="d-research",
        timestamp="2026-08-06T09:00:00",
        verdict=DecisionVerdict.WAIT,
        reason="RELIANCE shows mixed signals — patience advised.",
        evidence_packet_id="pkt-1",
        confidence=0.6,
        uncertainty=UncertaintyVector(),
        capital_recommendation="Wait for better entry",
        execution_recommendation="No action today",
        trade_allowed=False,
        invalidation_conditions=("Margin compression for two quarters",),
    )
    mis = MisTradeAdvisory(
        verdict="TRADE_OK",
        emoji="",
        headline="",
        summary="Balanced setup.",
        score=70,
        flags=(),
    )
    os_report = InvestmentOS(starred_symbol="RELIANCE", next_step="")
    setattr(os_report, "decision_artifact", art)
    packet = MagicMock(items=[], conflicts=[], gaps=[])
    return {
        "_context_bundle_version": "1",
        "snapshot": snap.as_dict(),
        "mis": mis,
        "os_report": os_report,
        "decision": art,
        "decision_source": "equity",
        "pins": [PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-08-06", side="LONG")],
        "prefs": IntradayPrefs(capital=100_000),
        "built_at": "09:12 IST",
        "market": "NSE",
        "broker": broker.to_dict(),
        "_broker_at_build": broker.to_dict(),
        "scenario": "normal",
        "stale": False,
        "stale_reason": "",
        "context_from_cache": False,
        "context_cache_age": None,
        "data_error": "",
    }, packet


class TestResearchWorkspaceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.broker = BrokerSnapshot(state="connected", holdings_count=2, portfolio_value_inr=100_000)
        cls.cached, cls.packet = _sample_cached(cls.broker)
        cls._packet_patcher = patch(
            "analyzer.use_cases.decision_context_bundle.fetch_evidence_packet_safe",
            return_value=cls.packet,
        )
        cls._packet_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls._packet_patcher.stop()

    def test_seven_research_questions_framing(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=self.cached,
            broker=self.broker,
            portfolio=ZerodhaImportResult(
                holdings=[_holding("RELIANCE", 10, 1000, 10000, 0)],
                source="manual",
            ),
            prefs=IntradayPrefs(),
        )
        self.assertEqual(len(contract.questions), 7)
        self.assertEqual(tuple(q.question_text for q in contract.questions), RESEARCH_QUESTIONS)

    def test_investment_view_hero_answer_first(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=self.cached,
            broker=self.broker,
            portfolio=ZerodhaImportResult(
                holdings=[_holding("RELIANCE", 10, 1000, 10000, 0)],
                source="manual",
            ),
            prefs=IntradayPrefs(),
        )
        self.assertTrue(contract.hero.view_label)
        self.assertTrue(contract.hero.summary)
        self.assertIn("research", contract.hero.disclaimer.lower())

    def test_question_two_has_labeled_evidence(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=self.cached,
            broker=self.broker,
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        q2 = contract.questions[1]
        self.assertEqual(q2.question_text, "What evidence supports investing?")
        self.assertTrue(q2.labeled_lines or q2.body_lines)

    def test_investment_decision_dispositions(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=self.cached,
            broker=self.broker,
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        self.assertIn(contract.decision.default_disposition, DISPOSITION_LABELS)
        q7 = contract.questions[6]
        self.assertEqual(q7.question_text, "What investment decision have I reached?")

    def test_portfolio_context_for_held_symbol(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=self.cached,
            broker=self.broker,
            portfolio=ZerodhaImportResult(
                holdings=[_holding("RELIANCE", 10, 1000, 10000, 0)],
                source="manual",
            ),
            prefs=IntradayPrefs(),
        )
        self.assertTrue(contract.context.held)
        self.assertNotEqual(contract.context.weight_label, "—")

    def test_fallback_without_cache(self):
        contract = research_workspace_from_inputs(
            symbol="TCS",
            cached=None,
            broker=self.broker,
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        self.assertEqual(contract.hero.view_label, "Insufficient data")
        self.assertEqual(len(contract.questions), 7)

    def test_question_understand_reuses_framework(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=self.cached,
            broker=self.broker,
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        understand = research_question_understand_contract(
            contract.questions[1],
            understand=contract.understand,
        )
        self.assertTrue(understand.sections)


class TestResearchWorkspaceRender(unittest.TestCase):
    def test_render_markers(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=None,
            broker=BrokerSnapshot(state="connected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []
        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.columns.side_effect = lambda spec: [MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.button.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.session_state = {}

        with patch("ui.components.research_workspace_experience.st", mock_st):
            render_research_context_header(contract=contract)
            render_investment_view_hero(contract=contract)
            render_research_question_navigator(contract=contract, active=1)
            render_research_question_panel(question=contract.questions[0], contract=contract)
            render_research_handoff_footer(contract=contract)

        joined = "".join(chunks)
        self.assertIn("apex-research-hero", joined)
        self.assertIn("apex-research-question-panel", joined)
        self.assertIn("Broker Console", joined)

    def test_experience_composes_main_landmark(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=None,
            broker=BrokerSnapshot(state="connected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []
        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.button.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.text_area.return_value = ""
        mock_st.radio.return_value = "Watch"
        mock_st.session_state = {}

        with patch("ui.components.research_workspace_experience.st", mock_st):
            render_research_workbench_experience(contract=contract)

        joined = "".join(chunks)
        self.assertIn("apex-research-workbench", joined)

    def test_investment_decision_panel_markers(self):
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=None,
            broker=BrokerSnapshot(state="connected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []
        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.button.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.text_area.return_value = ""
        mock_st.radio.return_value = "Watch"
        mock_st.session_state = {}

        with patch("ui.components.research_workspace_experience.st", mock_st):
            render_investment_decision_panel(contract=contract)

        joined = "".join(chunks)
        self.assertIn("apex-research-decision", joined)
        self.assertIn("what investment decision have i reached", joined.lower())

    def test_module_files_exist(self):
        for rel in (
            "ui/components/research_workspace_experience.py",
            "ui/components/research_workspace_ui.py",
        ):
            self.assertTrue((REPO_ROOT / rel).is_file())


if __name__ == "__main__":
    unittest.main()
