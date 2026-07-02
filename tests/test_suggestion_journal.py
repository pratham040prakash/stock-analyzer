"""Tests for suggestion journal, validation, and learning."""

import tempfile
import unittest
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from analyzer.suggestion_journal import (
    _connect,
    count_pending_validation,
    fetch_suggestions,
    init_journal,
    record_suggestion,
    record_from_daily_briefing,
    record_from_market_pulse,
)
from analyzer.suggestion_learning import build_learning_report
from analyzer.suggestion_validator import validate_pending_suggestions


@dataclass
class _Pick:
    symbol: str
    action: str
    score: float
    price: float
    reason: str = ""


@dataclass
class _Briefing:
    date: str
    short_term_picks: list = field(default_factory=list)
    long_term_picks: list = field(default_factory=list)
    holdings: list = field(default_factory=list)


@dataclass
class _ChartPick:
    nse_symbol: str
    symbol: str
    action: str
    score: float
    price: float
    entry_hint: str = ""
    stop_hint: str = ""
    target_hint: str = ""
    summary: str = ""


@dataclass
class _PulseReport:
    intraday_picks: list
    short_term_picks: list
    long_term_picks: list
    from_cache: bool = False


class TestSuggestionJournal(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "journal.db"
        self.patcher = patch(
            "analyzer.suggestion_journal.journal_db_path",
            return_value=self.db_path,
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.tmp.cleanup()

    def test_record_and_fetch(self) -> None:
        rid = record_suggestion(
            signal_date="2026-03-01",
            symbol="RELIANCE.NS",
            source="test",
            horizon="1d",
            action="BUY",
            score=75.0,
            price_at_signal=2500.0,
            reason="test pick",
        )
        self.assertIsNotNone(rid)
        rows = fetch_suggestions(limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].symbol, "RELIANCE")
        self.assertFalse(rows[0].validated)

    def test_dedup_same_day(self) -> None:
        record_suggestion(
            signal_date="2026-03-01",
            symbol="TCS.NS",
            source="daily_advisor",
            horizon="1d",
            action="BUY",
        )
        record_suggestion(
            signal_date="2026-03-01",
            symbol="TCS.NS",
            source="daily_advisor",
            horizon="1d",
            action="BUY",
        )
        self.assertEqual(len(fetch_suggestions()), 1)

    def test_record_from_daily_briefing(self) -> None:
        briefing = _Briefing(
            date="2026-03-01",
            short_term_picks=[_Pick("INFY.NS", "BUY", 80, 1500, "momentum")],
        )
        n = record_from_daily_briefing(briefing)
        self.assertGreaterEqual(n, 1)
        symbols = {r.symbol for r in fetch_suggestions()}
        self.assertIn("INFY", symbols)

    def test_record_from_market_pulse(self) -> None:
        report = _PulseReport(
            intraday_picks=[],
            short_term_picks=[
                _ChartPick("HDFCBANK", "HDFCBANK.NS", "BUY", 70, 1600, summary="breakout"),
            ],
            long_term_picks=[],
        )
        n = record_from_market_pulse(report)
        self.assertGreaterEqual(n, 1)

    def test_skip_cached_pulse(self) -> None:
        report = _PulseReport(
            intraday_picks=[_ChartPick("TCS", "TCS.NS", "BUY", 50, 100)],
            short_term_picks=[],
            long_term_picks=[],
            from_cache=True,
        )
        self.assertEqual(record_from_market_pulse(report), 0)


class TestSuggestionValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "journal.db"
        self.patcher = patch(
            "analyzer.suggestion_journal.journal_db_path",
            return_value=self.db_path,
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.tmp.cleanup()

    @patch("analyzer.suggestion_validator._forward_returns")
    def test_validate_buy_hit(self, mock_returns) -> None:
        past = (date.today() - timedelta(days=5)).isoformat()
        record_suggestion(
            signal_date=past,
            symbol="RELIANCE.NS",
            source="test",
            horizon="short",
            action="BUY",
            price_at_signal=100.0,
        )
        mock_returns.return_value = (2.5, 3.0, None, 2.0)
        result = validate_pending_suggestions()
        self.assertEqual(result["validated"], 1)
        rows = fetch_suggestions(validated_only=True)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].outcome_correct, 1)

    @patch("analyzer.suggestion_validator._forward_returns")
    def test_validate_sell_miss(self, mock_returns) -> None:
        past = (date.today() - timedelta(days=5)).isoformat()
        record_suggestion(
            signal_date=past,
            symbol="TCS.NS",
            source="test",
            horizon="short",
            action="SELL",
            price_at_signal=100.0,
        )
        mock_returns.return_value = (3.0, 3.0, None, 2.5)
        validate_pending_suggestions()
        rows = fetch_suggestions(validated_only=True)
        self.assertEqual(rows[0].outcome_correct, 0)


class TestSuggestionLearning(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "journal.db"
        self.patcher = patch(
            "analyzer.suggestion_journal.journal_db_path",
            return_value=self.db_path,
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.tmp.cleanup()

    def test_learning_report_empty(self) -> None:
        report = build_learning_report()
        self.assertEqual(report.total_suggestions, 0)
        self.assertTrue(any("Collecting data" in i or "10+" in i for i in report.insights))

    def test_learning_report_with_data(self) -> None:
        rid = record_suggestion(
            signal_date="2026-02-01",
            symbol="INFY.NS",
            source="daily_advisor",
            horizon="short",
            action="BUY",
        )
        self.assertIsNotNone(rid)
        init_journal()
        with _connect() as conn:
            conn.execute(
                """
                UPDATE suggestions SET
                    validated = 1, outcome_correct = 1,
                    outcome_return_1d = 1.5, outcome_nifty_alpha_1d = 0.8
                WHERE id = ?
                """,
                (rid,),
            )
        report = build_learning_report()
        self.assertEqual(report.validated_count, 1)
        self.assertEqual(report.overall_win_rate_pct, 100.0)


if __name__ == "__main__":
    unittest.main()
