"""V3-202 — Research Journal contracts and render integration."""

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
from ui.components.research_journal_experience import (
    confirm_journal_draft,
    create_journal_draft_from_research,
    discard_journal_draft,
    get_journal_draft,
    get_journal_entry,
    list_journal_entries,
    render_editable_narrative_block,
    render_evolution_chain,
    render_frozen_system_summary_block,
    render_journal_confirm_draft,
    render_journal_drafts_inbox,
    render_journal_entry_detail,
    render_journal_timeline,
    render_outcome_review_placeholder,
    render_portfolio_linkage_block,
    render_research_completion_strip,
    render_research_journal_experience,
)
from ui.components.research_journal_ui import (
    ENTRY_TYPE_RESEARCH,
    draft_to_confirmed_entry,
    prior_confirmed_entry_id,
    research_journal_draft_from_workspace,
    symbol_entry_chain,
)
from ui.components.research_workspace_ui import DISPOSITION_LABELS, research_workspace_from_inputs

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
        snapshot_id="ctx-journal",
        context_hash="",
    )
    art = DecisionArtifact(
        decision_id="d-journal",
        timestamp="2026-08-06T09:00:00",
        verdict=DecisionVerdict.WAIT,
        reason="WIPRO shows mixed signals — patience advised.",
        evidence_packet_id="pkt-journal",
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
    os_report = InvestmentOS(starred_symbol="WIPRO", next_step="")
    setattr(os_report, "decision_artifact", art)
    packet = MagicMock(items=[], conflicts=[], gaps=[])
    return {
        "_context_bundle_version": "1",
        "snapshot": snap.as_dict(),
        "mis": mis,
        "os_report": os_report,
        "decision": art,
        "decision_source": "equity",
        "pins": [PinnedPlan("WIPRO", 2850, 2815, 2930, "2026-08-06", side="LONG")],
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


class TestResearchJournalContracts(unittest.TestCase):
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

    def test_draft_projection_from_workspace(self):
        session = {
            "research_investment_decision_text_WIPRO": "Hold current position until health stabilizes.",
            "research_disposition_WIPRO": "hold",
            "research_reviewed_question_keys": {"WIPRO:1", "WIPRO:2", "WIPRO:3"},
        }
        contract = research_workspace_from_inputs(
            symbol="WIPRO",
            cached=self.cached,
            broker=self.broker,
            portfolio=ZerodhaImportResult(
                holdings=[_holding("WIPRO", 10, 1000, 10000, 0)],
                source="manual",
            ),
            prefs=IntradayPrefs(),
        )
        draft = research_journal_draft_from_workspace(
            contract=contract,
            session=session,
            cached=self.cached,
        )
        self.assertEqual(draft.entry_type, ENTRY_TYPE_RESEARCH)
        self.assertEqual(draft.symbol, "WIPRO")
        self.assertEqual(draft.disposition, "hold")
        self.assertEqual(draft.disposition_label, DISPOSITION_LABELS["hold"])
        self.assertTrue(draft.portfolio_held)
        self.assertEqual(draft.decision_id, "d-journal")
        self.assertEqual(draft.evidence_packet_id, "pkt-journal")
        self.assertEqual(draft.bundle_built_at, "09:12 IST")
        self.assertEqual(sum(draft.questions_reviewed), 3)

    def test_confirm_produces_immutable_entry(self):
        session = {
            "research_investment_decision_text_TCS": "Watch for pullback.",
            "research_disposition_TCS": "watch",
        }
        contract = research_workspace_from_inputs(
            symbol="TCS",
            cached=self.cached,
            broker=self.broker,
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        draft = research_journal_draft_from_workspace(
            contract=contract,
            session=session,
            cached=self.cached,
        )
        entry = draft_to_confirmed_entry(draft)
        self.assertEqual(entry.entry_id, draft.entry_id)
        self.assertEqual(entry.user_narrative, draft.user_narrative)
        self.assertEqual(entry.source_label, "Research")

    def test_evolution_chain_same_symbol(self):
        session_a = {
            "research_investment_decision_text_WIPRO": "Watch.",
            "research_disposition_WIPRO": "watch",
        }
        session_b = {
            "research_investment_decision_text_WIPRO": "Hold.",
            "research_disposition_WIPRO": "hold",
        }
        contract = research_workspace_from_inputs(
            symbol="WIPRO",
            cached=self.cached,
            broker=self.broker,
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        draft_a = research_journal_draft_from_workspace(contract=contract, session=session_a, cached=self.cached)
        draft_b = research_journal_draft_from_workspace(
            contract=contract,
            session=session_b,
            cached=self.cached,
            prior_entry_id=draft_a.entry_id,
        )
        entry_a = draft_to_confirmed_entry(draft_a)
        entry_b = draft_to_confirmed_entry(draft_b, supersedes_entry_id=entry_a.entry_id)
        chain = symbol_entry_chain(symbol="WIPRO", entries=(entry_a, entry_b))
        self.assertEqual(len(chain), 2)
        self.assertEqual(prior_confirmed_entry_id(symbol="WIPRO", entries=(entry_a,)), entry_a.entry_id)


class TestResearchJournalSessionFlow(unittest.TestCase):
    def test_draft_confirm_discard_session_flow(self):
        mock_st = MagicMock()
        mock_st.session_state = {
            "research_investment_decision_text_RELIANCE": "Accumulate on dips.",
            "research_disposition_RELIANCE": "accumulate_later",
        }
        contract = research_workspace_from_inputs(
            symbol="RELIANCE",
            cached=None,
            broker=BrokerSnapshot(state="connected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        with patch("ui.components.research_journal_experience.st", mock_st):
            draft_id = create_journal_draft_from_research(contract=contract)
            draft = get_journal_draft(draft_id)
            self.assertIsNotNone(draft)
            self.assertEqual(draft.user_narrative, "Accumulate on dips.")

            entry = confirm_journal_draft(draft_id)
            self.assertIsNotNone(entry)
            self.assertIsNone(get_journal_draft(draft_id))
            self.assertEqual(len(list_journal_entries()), 1)
            self.assertEqual(get_journal_entry(entry.entry_id).disposition, "accumulate_later")

            draft_id_2 = create_journal_draft_from_research(contract=contract)
            discard_journal_draft(draft_id_2)
            self.assertIsNone(get_journal_draft(draft_id_2))


class TestResearchJournalRender(unittest.TestCase):
    def _mock_st(self) -> MagicMock:
        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.button.return_value = False
        mock_st.text_area.return_value = ""
        mock_st.radio.return_value = "Hold"
        mock_st.checkbox.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.columns.side_effect = lambda spec: [MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.warning = MagicMock()
        mock_st.error = MagicMock()
        mock_st.caption = MagicMock()
        mock_st.session_state = {}
        return mock_st

    def test_timeline_markers(self):
        global chunks
        chunks = []
        contract = research_workspace_from_inputs(
            symbol="WIPRO",
            cached=None,
            broker=BrokerSnapshot(state="connected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        entry = draft_to_confirmed_entry(
            research_journal_draft_from_workspace(
                contract=contract,
                session={
                    "research_investment_decision_text_WIPRO": "Hold.",
                    "research_disposition_WIPRO": "hold",
                },
            )
        )
        mock_st = self._mock_st()
        with patch("ui.components.research_journal_experience.st", mock_st):
            render_journal_timeline(entries=(entry,))
        joined = "".join(chunks)
        self.assertIn("apex-journal-timeline", joined)
        self.assertIn("Research Decision", joined)

    def test_confirm_draft_markers(self):
        global chunks
        chunks = []
        contract = research_workspace_from_inputs(
            symbol="WIPRO",
            cached=None,
            broker=BrokerSnapshot(state="connected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        draft = research_journal_draft_from_workspace(
            contract=contract,
            session={
                "research_investment_decision_text_WIPRO": "Hold.",
                "research_disposition_WIPRO": "hold",
            },
        )
        mock_st = self._mock_st()
        with patch("ui.components.research_journal_experience.st", mock_st):
            render_journal_confirm_draft(draft=draft)
        joined = "".join(chunks)
        self.assertIn("apex-journal-confirm", joined)
        self.assertIn("cannot be edited", joined.lower())

    def test_entry_detail_outcome_placeholder_disabled(self):
        global chunks
        chunks = []
        contract = research_workspace_from_inputs(
            symbol="WIPRO",
            cached=None,
            broker=BrokerSnapshot(state="connected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        entry = draft_to_confirmed_entry(
            research_journal_draft_from_workspace(
                contract=contract,
                session={
                    "research_investment_decision_text_WIPRO": "Hold.",
                    "research_disposition_WIPRO": "hold",
                },
            )
        )
        mock_st = self._mock_st()
        with patch("ui.components.research_journal_experience.st", mock_st):
            render_journal_entry_detail(entry=entry, entries=(entry,))
        joined = "".join(chunks)
        self.assertIn("apex-journal-outcome-placeholder", joined)
        self.assertIn("future", joined.lower())
        mock_st.button.assert_any_call(
            "Start Outcome Review",
            key=f"journal_outcome_review_{entry.entry_id}",
            disabled=True,
            use_container_width=True,
        )

    def test_component_blocks_render(self):
        global chunks
        chunks = []
        contract = research_workspace_from_inputs(
            symbol="WIPRO",
            cached=None,
            broker=BrokerSnapshot(state="connected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        draft = research_journal_draft_from_workspace(
            contract=contract,
            session={
                "research_investment_decision_text_WIPRO": "Hold.",
                "research_disposition_WIPRO": "hold",
            },
        )
        entry = draft_to_confirmed_entry(draft)
        mock_st = self._mock_st()
        with patch("ui.components.research_journal_experience.st", mock_st):
            render_editable_narrative_block(draft=draft, text_key="journal_text")
            render_frozen_system_summary_block(entry=draft)
            render_research_completion_strip(entry=draft)
            render_portfolio_linkage_block(entry=draft)
            render_evolution_chain(entry=entry, entries=(entry,))
            render_outcome_review_placeholder(entry=entry)
            render_journal_drafts_inbox(drafts=(draft,))
        joined = "".join(chunks)
        self.assertIn("apex-journal-editable-narrative", joined)
        self.assertIn("apex-journal-frozen-summary", joined)
        self.assertIn("apex-journal-drafts-inbox", joined)

    def test_experience_main_landmark(self):
        global chunks
        chunks = []
        mock_st = self._mock_st()
        mock_st.session_state = {"journal_view": "timeline"}
        with patch("ui.components.research_journal_experience.st", mock_st):
            render_research_journal_experience()
        joined = "".join(chunks)
        self.assertIn("apex-research-journal", joined)

    def test_module_files_exist(self):
        for rel in (
            "ui/components/research_journal_experience.py",
            "ui/components/research_journal_ui.py",
            "ui/pages/research_journal.py",
        ):
            self.assertTrue((REPO_ROOT / rel).is_file())


chunks: list[str] = []


if __name__ == "__main__":
    unittest.main()
