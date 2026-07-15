"""Tests for MIS trade / no-trade advisory."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def _mock_context(*, is_open: bool, regime: str, adx: float = 20.0, allow_entries: bool = True):
    from analyzer.context_engine.models import ContextSnapshot

    return ContextSnapshot.create(
        timestamp="2026-07-10 10:00 IST",
        market_regime=regime,
        market_phase="mid_session" if is_open else "closed",
        market_breadth="unknown",
        volatility_state="normal",
        liquidity_state="normal",
        market_session={"is_open": is_open, "phase": "open" if is_open else "closed"},
        sector_strength={},
        industry_strength={},
        macro_state={},
        global_market_state={},
        risk_mode="NEUTRAL" if is_open else "CLOSED",
        trading_restrictions=[],
        confidence=70.0,
        metadata={
            "allow_new_entries": allow_entries,
            "prefer_exit": False,
            "regime_detail": {"adx": adx},
        },
    )


class TestMisTradeAdvisory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal = Path(self.tmp.name) / "trade_journal.json"
        self.jp = patch("analyzer.trade_journal.STORE_PATH", self.journal)
        self.jp.start()

    def tearDown(self):
        self.jp.stop()
        self.tmp.cleanup()

    @patch("analyzer.mis_trade_advisory._best_actionable_pick", return_value=("", False, "", None))
    @patch("analyzer.context_engine.build_context_snapshot")
    def test_late_session_no_trade(self, mock_ctx_fn, _pick):
        from analyzer.mis_trade_advisory import build_mis_trade_advisory

        mock_ctx_fn.return_value = _mock_context(is_open=True, regime="Range-bound", adx=12.0, allow_entries=True)
        now = datetime(2026, 7, 10, 14, 10, tzinfo=IST)
        adv = build_mis_trade_advisory(now=now)
        self.assertEqual(adv.verdict, "NO_TRADE")
        self.assertTrue(any("2:00 PM" in f for f in adv.flags))

    @patch("analyzer.strategy_synthesis.synthesize_options")
    @patch("analyzer.mis_trade_advisory._best_actionable_pick", return_value=("NIFTY CE 24200", True, "ok", 0.5))
    @patch("analyzer.context_engine.build_context_snapshot")
    def test_morning_gate_ok_trending(self, mock_ctx_fn, _pick, mock_syn):
        from analyzer.mis_trade_advisory import build_mis_trade_advisory
        from analyzer.strategy_synthesis import StrategySynthesis

        mock_syn.return_value = StrategySynthesis(
            target="NIFTY CE 24200",
            asset_class="options",
            side="CE",
            verdict="BUY",
            confidence_pct=72,
            headline="Aligned",
            summary="5 green",
            trade_allowed=True,
            positives=["gate green"],
            negatives=[],
        )

        mock_ctx_fn.return_value = _mock_context(is_open=True, regime="Trending Bullish", adx=28.0, allow_entries=True)
        now = datetime(2026, 7, 10, 10, 0, tzinfo=IST)
        adv = build_mis_trade_advisory(now=now)
        self.assertIn(adv.verdict, ("TRADE_OK", "CAUTION"))
        self.assertTrue(adv.gate_allowed)

    def test_loss_streak(self):
        from analyzer.trade_journal import save_journal_entry
        from analyzer.mis_trade_advisory import recent_loss_streak_days

        save_journal_entry(
            trade_date="2026-07-09",
            symbol="BANKNIFTY",
            leg="PE 55000",
            pnl_inr=-1754,
            mistake="OTM chop",
            fix="1 lot",
        )
        save_journal_entry(
            trade_date="2026-07-10",
            symbol="NIFTY",
            leg="CE 24500",
            pnl_inr=-253,
            mistake="trail",
            fix="book early",
        )
        self.assertEqual(recent_loss_streak_days(), 2)

    @patch("analyzer.mis_trade_advisory._best_actionable_pick", return_value=("", False, "", None))
    @patch("analyzer.context_engine.build_context_snapshot")
    def test_two_loss_days_forces_no_trade(self, mock_ctx_fn, _pick):
        from analyzer.mis_trade_advisory import build_mis_trade_advisory
        from analyzer.trade_journal import save_journal_entry

        save_journal_entry(
            trade_date="2026-07-09", symbol="BNF", pnl_inr=-100,
        )
        save_journal_entry(
            trade_date="2026-07-10", symbol="NIFTY", pnl_inr=-50,
        )
        mock_ctx_fn.return_value = _mock_context(is_open=True, regime="Trending Bullish", adx=25.0, allow_entries=True)
        now = datetime(2026, 7, 10, 10, 0, tzinfo=IST)
        adv = build_mis_trade_advisory(now=now)
        self.assertIn(adv.verdict, ("NO_TRADE", "CAUTION"))
        self.assertEqual(adv.loss_streak_days, 2)


if __name__ == "__main__":
    unittest.main()
