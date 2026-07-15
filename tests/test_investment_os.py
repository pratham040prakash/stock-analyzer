"""Tests for Investment Operating System orchestrator."""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from analyzer.investment_os import (
    InvestmentOS,
    MODULE_KEYS,
    _infer_strategy,
    _pick_starred,
    _rank_pins,
    _risk_reward,
    build_investment_os,
)
from analyzer.watchlist_pins import PinnedPlan

IST = ZoneInfo("Asia/Kolkata")


def _mock_context(*, is_open: bool, allow_entries: bool = True):
    from analyzer.context_engine.models import ContextSnapshot

    return ContextSnapshot.create(
        timestamp="2026-07-16 10:00 IST",
        market_regime="Trending Bullish",
        market_phase="mid_session" if is_open else "after_hours",
        market_breadth="unknown",
        volatility_state="normal",
        liquidity_state="normal",
        market_session={
            "is_open": is_open,
            "status": "Market open" if is_open else "Closed",
            "phase": "open" if is_open else "after_hours",
            "date": "2026-07-16",
        },
        sector_strength={"leader": "IT", "laggard": "FMCG", "ranked": []},
        industry_strength={},
        macro_state={},
        global_market_state={"bias": "Bullish"},
        risk_mode="RISK-ON" if is_open else "CLOSED",
        trading_restrictions=[] if allow_entries else ["Wait for gate"],
        confidence=75.0,
        metadata={
            "allow_new_entries": allow_entries,
            "regime_detail": {
                "adx": 28.0,
                "allow_aggressive_intraday": True,
                "allow_aggressive_swing": True,
                "banner": "Bull",
                "message": "Trend",
            },
        },
    )


def _pin(
    symbol: str = "RELIANCE",
    entry: float = 100.0,
    stop: float = 98.0,
    target: float = 104.0,
    sector: str = "Energy",
    side: str = "LONG",
) -> PinnedPlan:
    return PinnedPlan(
        symbol=symbol,
        entry=entry,
        stop_loss=stop,
        target=target,
        prep_date="2026-07-16",
        sector=sector,
        side=side,
    )


class TestInvestmentOSHelpers(unittest.TestCase):
    def test_risk_reward(self):
        self.assertEqual(_risk_reward(100, 98, 104), 2.0)
        self.assertIsNone(_risk_reward(100, 100, 104))

    def test_rank_pins_by_rr(self):
        low = _pin("LOW", 100, 99, 101)
        high = _pin("HIGH", 100, 95, 110)
        ranked = _rank_pins([low, high])
        self.assertEqual(ranked[0][0].symbol, "HIGH")

    def test_pick_starred_prefers_selection(self):
        pins = [_pin("A"), _pin("B")]
        ranked = _rank_pins(pins)
        with patch("analyzer.investment_os.load_selected_symbols", return_value=["B"]):
            star = _pick_starred(pins, ranked)
        self.assertEqual(star.symbol, "B")

    def test_infer_strategy_timing_block(self):
        head, detail, status = _infer_strategy(
            _pin(),
            market_bias="BULLISH",
            regime=None,
            timing_blocked=True,
        )
        self.assertIn("Wait", head)
        self.assertEqual(status, "wait")

    def test_infer_strategy_short_bearish(self):
        head, _, status = _infer_strategy(
            _pin(side="SHORT"),
            market_bias="BEARISH",
            regime=MagicMock(regime="Trending Bearish"),
            timing_blocked=False,
        )
        self.assertIn("breakdown", head.lower())
        self.assertEqual(status, "ok")


class TestBuildInvestmentOS(unittest.TestCase):
    def test_builds_seven_modules(self):
        pins = [_pin()]
        session = {
            "is_open": True,
            "status": "Market open",
            "phase": "regular",
            "date": "2026-07-16",
        }
        timing = MagicMock(allow_new_entries=True, headline="Entries allowed")

        with (
            patch("analyzer.investment_os.load_pinned_plans", return_value=pins),
            patch("analyzer.investment_os.load_selected_symbols", return_value=["RELIANCE"]),
            patch("analyzer.context_engine.build_context_snapshot", return_value=_mock_context(is_open=True)),
            patch("analyzer.investment_os._load_pulse", return_value=None),
            patch("analyzer.investment_os.load_intraday_prefs") as mock_prefs,
            patch("analyzer.decision_engine.verdict_bridge.attach_decision_to_investment_os"),
            patch("analyzer.investment_os.load_journal_entries", return_value=[]),
            patch(
                "analyzer.investment_os.build_watchlist_learning_report",
                return_value=MagicMock(insights=[]),
            ),
        ):
            mock_prefs.return_value.capital = 9000
            mock_prefs.return_value.min_daily_profit_pct = 2.0
            mock_prefs.return_value.max_risk_pct = 1.0
            report = build_investment_os(
                "india",
                deep=False,
                now=datetime(2026, 7, 16, 10, 0, tzinfo=IST),
            )

        self.assertIsInstance(report, InvestmentOS)
        self.assertEqual(len(report.modules), 7)
        keys = [m.key for m in report.modules]
        self.assertEqual(keys, list(MODULE_KEYS))
        self.assertEqual(report.starred_symbol, "RELIANCE")
        self.assertIn(report.verdict, ("TRADE OK", "WAIT", "NO TRADE", "PREP", "CLOSED"))

    def test_no_pins_yields_prep_verdict(self):
        session = {"is_open": False, "status": "Closed", "phase": "after_hours", "date": "2026-07-16"}
        timing = MagicMock(allow_new_entries=False, headline="After hours")

        with (
            patch("analyzer.investment_os.load_pinned_plans", return_value=[]),
            patch("analyzer.context_engine.build_context_snapshot", return_value=_mock_context(is_open=False, allow_entries=False)),
            patch("analyzer.investment_os._load_pulse", return_value=None),
            patch("analyzer.investment_os.load_intraday_prefs") as mock_prefs,
            patch("analyzer.investment_os.load_journal_entries", return_value=[]),
            patch(
                "analyzer.investment_os.build_watchlist_learning_report",
                return_value=MagicMock(insights=[]),
            ),
        ):
            mock_prefs.return_value.capital = 9000
            mock_prefs.return_value.min_daily_profit_pct = 2.0
            mock_prefs.return_value.max_risk_pct = 1.0
            report = build_investment_os("india", deep=False)

        self.assertEqual(report.verdict, "PREP")
        stock = report.module("stock")
        self.assertIsNotNone(stock)
        self.assertEqual(stock.headline, "No picks saved")


if __name__ == "__main__":
    unittest.main()
