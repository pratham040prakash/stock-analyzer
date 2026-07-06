"""Tests for intraday entry/exit trade plans."""

import unittest

from analyzer.intraday_trade_plan import (
    MIN_RISK_REWARD,
    build_intraday_trade_plan,
)


class TestIntradayTradePlan(unittest.TestCase):
    def test_long_plan_with_partial_exit_rules(self):
        plan = build_intraday_trade_plan(
            "BUY", entry=1000.0, stop_loss=990.0, target=1015.0,
            account_inr=50_000, max_risk_pct=1.0,
            entry_reasons=["VWAP breakout"],
        )
        self.assertEqual(plan.side, "LONG")
        self.assertTrue(plan.can_enter)
        self.assertEqual(plan.risk_reward_ratio, 1.5)
        self.assertEqual(plan.suggested_shares, 50)
        self.assertTrue(any("T1" in r for r in plan.exit_rules))
        self.assertTrue(any("breakeven" in r.lower() or "40%" in r for r in plan.exit_rules))

    def test_skip_when_rr_too_low(self):
        plan = build_intraday_trade_plan(
            "BUY", entry=100.0, stop_loss=95.0, target=102.0,
        )
        self.assertFalse(plan.can_enter)
        self.assertLess(plan.risk_reward_ratio or 0, MIN_RISK_REWARD)

    def test_skip_when_stop_too_wide_for_account(self):
        plan = build_intraday_trade_plan(
            "BUY", entry=1000.0, stop_loss=950.0, target=1075.0,
            account_inr=1_000, max_risk_pct=1.0,
        )
        self.assertFalse(plan.can_enter)
        self.assertIn("risk budget", (plan.skip_reason or "").lower())

    def test_wait_is_flat(self):
        plan = build_intraday_trade_plan("WAIT", None, None, None)
        self.assertEqual(plan.side, "FLAT")
        self.assertFalse(plan.can_enter)

    def test_short_side(self):
        plan = build_intraday_trade_plan(
            "SELL", entry=500.0, stop_loss=510.0, target=485.0,
        )
        self.assertEqual(plan.side, "SHORT")
        self.assertGreaterEqual(plan.risk_reward_ratio or 0, MIN_RISK_REWARD)


if __name__ == "__main__":
    unittest.main()
