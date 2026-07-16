"""Answer Canvas (Phase 4) helper tests."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from ui.broker.state import BrokerSnapshot
from ui.components.answer_canvas import build_ask_answer, suggestion_chips


def _cached(
    *,
    risk_mode: str = "NEUTRAL",
    starred: str = "RELIANCE",
    verdict: DecisionVerdict = DecisionVerdict.ACT,
) -> dict:
    snap = ContextSnapshot(
        timestamp="t",
        market_regime="n",
        market_phase="regular",
        market_breadth="m",
        volatility_state="n",
        liquidity_state="n",
        market_session={"phase": "regular"},
        sector_strength={"IT": 0.3, "Defence": 0.8},
        industry_strength={},
        macro_state={},
        global_market_state={},
        risk_mode=risk_mode,
        trading_restrictions=(),
        confidence=0.75,
    )
    decision = DecisionArtifact(
        decision_id="d1",
        timestamp="",
        verdict=verdict,
        reason="Momentum confirms after opening range.",
        evidence_packet_id="",
        confidence=0.8,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        trade_allowed=True,
    )
    mis = MisTradeAdvisory(
        verdict="TRADE_OK",
        emoji="",
        headline="",
        summary="Session looks balanced.",
        score=70,
        flags=[],
        loss_streak_days=0,
    )
    os_report = InvestmentOS(
        starred_symbol=starred,
        next_step="Wait for trigger.",
    )
    setattr(os_report, "decision_artifact", decision)
    return {
        "snapshot": snap.as_dict(),
        "mis": mis,
        "os_report": os_report,
        "pins": [],
        "prefs": IntradayPrefs(capital=100_000, max_risk_pct=1.8),
        "portfolio": None,
    }


class AnswerCanvasHelpersTest(unittest.TestCase):
    def test_suggestion_chips_are_two(self):
        chips = suggestion_chips()
        self.assertEqual(len(chips), 2)

    def test_personalized_opener_when_connected(self):
        broker = BrokerSnapshot(state="connected")
        answer = build_ask_answer("Should I buy RELIANCE?", broker=broker, cached=_cached())
        self.assertIn("If I were managing your portfolio today", answer.mentor_line)
        self.assertEqual(answer.context_line, "Based on today's market and your portfolio.")
        self.assertEqual(answer.primary_label, "Back to Today")

    def test_afford_answer_yes(self):
        broker = BrokerSnapshot(state="connected")
        answer = build_ask_answer("Can I afford this trade?", broker=broker, cached=_cached())
        self.assertIn(answer.answer_word, ("Yes", "Tight", "No"))
        self.assertTrue(answer.mentor_line.startswith("If I were"))

    def test_macro_answer_risk_word(self):
        broker = BrokerSnapshot(state="connected")
        answer = build_ask_answer("What if Nifty falls 2%?", broker=broker, cached=_cached())
        self.assertEqual(answer.answer_word, "Risk")
        self.assertIn("Nifty", answer.mentor_line)

    def test_average_down_pass(self):
        broker = BrokerSnapshot(state="connected")
        answer = build_ask_answer("Should I average down?", broker=broker, cached=_cached())
        self.assertEqual(answer.answer_word, "Pass")

    def test_unknown_symbol_pass(self):
        broker = BrokerSnapshot(state="connected")
        answer = build_ask_answer(
            "Should I buy ZZZZZNOTATICKER99?",
            broker=broker,
            cached=_cached(),
        )
        self.assertEqual(answer.answer_word, "Pass")
        self.assertIn("couldn't map", answer.mentor_line.lower())

    def test_ghost_label_is_why_not_done(self):
        broker = BrokerSnapshot(state="connected")
        answer = build_ask_answer("Can I afford this trade?", broker=broker, cached=_cached())
        self.assertEqual(answer.primary_label, "Back to Today")
        self.assertNotEqual(answer.primary_label, "Done")

    def test_connect_on_afford_without_broker(self):
        broker = BrokerSnapshot(state="disconnected")
        answer = build_ask_answer("Can I afford this trade?", broker=broker, cached=_cached())
        self.assertEqual(answer.primary_label, "Connect Zerodha")
        self.assertEqual(answer.primary_action, "connect")


if __name__ == "__main__":
    unittest.main()
