"""Trust Canvas (Phase 5) helper tests."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from analyzer.broker_truth.learning import LearningOutcomeRow, LearningOutcomeSource
from analyzer.context_engine.models import ContextSnapshot
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.suggestion_journal import SuggestionRecord
from analyzer.trade_journal import TradeJournalEntry
from ui.broker.state import BrokerSnapshot
from ui.components.trust_canvas import build_trust_view

IST = ZoneInfo("Asia/Kolkata")


def _mis() -> MisTradeAdvisory:
    return MisTradeAdvisory(
        verdict="TRADE_OK",
        emoji="",
        headline="",
        summary="Balanced session.",
        score=70,
        flags=(),
        loss_streak_days=0,
    )


def _snapshot() -> ContextSnapshot:
    return ContextSnapshot(
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
        confidence=0.7,
    )


def _suggestion(
    *,
    signal_date: str,
    action: str = "WAIT",
    outcome_correct: int = 1,
    outcome_return_1d: float | None = -0.5,
    outcome_note: str = "",
) -> SuggestionRecord:
    return SuggestionRecord(
        id=f"{signal_date}:pulse:short:INFY:{action}",
        signal_date=signal_date,
        symbol="INFY",
        yahoo_symbol="INFY.NS",
        source="market_pulse",
        horizon="short",
        action=action,
        score=0.7,
        price_at_signal=100.0,
        entry_hint="",
        stop_hint="",
        target_hint="",
        reason="Wait for confirmation",
        strategy_version="v1",
        created_at="",
        validated=True,
        outcome_return_1d=outcome_return_1d,
        outcome_correct=outcome_correct,
        outcome_note=outcome_note,
        validated_at="",
    )


class TrustCanvasHelpersTest(unittest.TestCase):
    def test_thin_history_is_honest(self):
        broker = BrokerSnapshot(state="connected")
        with patch("ui.components.trust_canvas._recent_suggestions", return_value=[]):
            view = build_trust_view(
                broker=broker,
                mis=_mis(),
                snapshot=_snapshot(),
                os_report=InvestmentOS(),
                portfolio=None,
                journal=[],
                learning=[],
                pins=[],
                prefs=IntradayPrefs(),
            )
        self.assertEqual(view.trust_word, "Honest")
        self.assertIn("consistency", view.this_week.lower())
        self.assertEqual(view.primary_label, "Back to You")
        self.assertIn("That's how I improve", view.forward_line)

    def test_micro_label_is_warm(self):
        broker = BrokerSnapshot(state="connected")
        with patch("ui.components.trust_canvas._recent_suggestions", return_value=[]):
            view = build_trust_view(
                broker=broker,
                mis=_mis(),
                snapshot=_snapshot(),
                os_report=InvestmentOS(),
                portfolio=None,
                journal=[],
                learning=[],
                pins=[],
                prefs=IntradayPrefs(),
            )
        self.assertEqual(view.micro_label, "I've been reviewing every decision.")
        self.assertNotIn("keeping score", view.micro_label.lower())

    def test_miss_acknowledges_and_learns(self):
        today = datetime.now(IST).date()
        old = (today - timedelta(days=8)).isoformat()
        miss = _suggestion(
            signal_date=old,
            action="WAIT",
            outcome_correct=0,
            outcome_note="tightened my breakout confirmation rule",
        )
        broker = BrokerSnapshot(state="connected")
        with patch("ui.components.trust_canvas._recent_suggestions", return_value=[miss] * 4):
            view = build_trust_view(
                broker=broker,
                mis=_mis(),
                snapshot=_snapshot(),
                os_report=InvestmentOS(),
                portfolio=None,
                journal=[],
                learning=[LearningOutcomeRow(old, "INFY", "flat", LearningOutcomeSource.NONE)] * 3,
                pins=[],
                prefs=IntradayPrefs(),
            )
        self.assertEqual(view.trust_word, "Learning")
        self.assertIn("I missed", view.miss_line)
        self.assertIn("tightened", view.miss_line.lower())
        self.assertNotIn("but", view.miss_line.lower().split("i've")[0])

    def test_forward_line_optimistic(self):
        broker = BrokerSnapshot(state="connected")
        with patch("ui.components.trust_canvas._recent_suggestions", return_value=[]):
            view = build_trust_view(
                broker=broker,
                mis=_mis(),
                snapshot=_snapshot(),
                os_report=InvestmentOS(),
                portfolio=None,
                journal=[],
                learning=[],
                pins=[],
                prefs=IntradayPrefs(),
            )
        self.assertIn("continue checking", view.forward_line.lower())

    def test_journal_miss_uses_fix(self):
        broker = BrokerSnapshot(state="connected")
        journal = [
            TradeJournalEntry(
                trade_date="2026-07-10",
                symbol="INFY",
                leg="",
                entry=None,
                exit=None,
                pnl_inr=-200.0,
                mistake="Chased breakout",
                fix="tightened my breakout confirmation rule",
                saved_at="",
            )
        ]
        with patch("ui.components.trust_canvas._recent_suggestions", return_value=[]):
            view = build_trust_view(
                broker=broker,
                mis=_mis(),
                snapshot=_snapshot(),
                os_report=InvestmentOS(),
                portfolio=None,
                journal=journal,
                learning=[],
                pins=[],
                prefs=IntradayPrefs(),
            )
        self.assertIn("tightened", view.miss_line.lower())

    def test_no_performance_words_in_trust_word(self):
        broker = BrokerSnapshot(state="connected")
        with patch("ui.components.trust_canvas._recent_suggestions", return_value=[]):
            view = build_trust_view(
                broker=broker,
                mis=_mis(),
                snapshot=_snapshot(),
                os_report=InvestmentOS(),
                portfolio=None,
                journal=[],
                learning=[],
                pins=[],
                prefs=IntradayPrefs(),
            )
        self.assertIn(view.trust_word, ("Honest", "Learning", "Earned"))


if __name__ == "__main__":
    unittest.main()
