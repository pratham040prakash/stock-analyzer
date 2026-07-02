"""Tests for SIP / goals planner."""

import unittest

from analyzer.sip_planner import (
    allocation_template,
    build_allocation_lines,
    build_sip_plan,
    future_value_sip,
    required_monthly_sip,
    SipPlannerInput,
    total_invested,
)


class TestSipPlanner(unittest.TestCase):
    def test_future_value_positive(self):
        fv = future_value_sip(10_000, 12.0, 12, lump_sum=0)
        self.assertGreater(fv, 120_000)

    def test_required_monthly_reaches_target(self):
        target = 10_00_000
        months = 120
        monthly = required_monthly_sip(target, 12.0, months)
        fv = future_value_sip(monthly, 12.0, months)
        self.assertGreaterEqual(fv, target * 0.99)

    def test_lump_sum_reduces_required_sip(self):
        m1 = required_monthly_sip(20_00_000, 12.0, 120)
        m2 = required_monthly_sip(20_00_000, 12.0, 120, lump_sum=5_00_000)
        self.assertLess(m2, m1)

    def test_allocation_weights_sum(self):
        lines = build_allocation_lines(10_000, "balanced", "some", "india")
        weights = sum(l.weight_pct for l in lines)
        self.assertAlmostEqual(weights, 100.0, places=1)
        amounts = sum(l.monthly_amount for l in lines)
        self.assertAlmostEqual(amounts, 10_000, delta=2)

    def test_new_investor_more_index(self):
        new_lines = build_allocation_lines(10_000, "balanced", "new", "india")
        some_lines = build_allocation_lines(10_000, "balanced", "some", "india")
        new_index = sum(l.weight_pct for l in new_lines if l.sleeve == "index")
        some_index = sum(l.weight_pct for l in some_lines if l.sleeve == "index")
        self.assertGreater(new_index, some_index)

    def test_build_plan_with_budget(self):
        inp = SipPlannerInput(
            goal_name="Wealth building",
            target_amount=50_00_000,
            years=10,
            monthly_budget=20_000,
            annual_return_pct=12.0,
            market="india",
        )
        plan = build_sip_plan(inp)
        self.assertEqual(plan.monthly_sip, 20_000)
        self.assertGreater(plan.projected_corpus, 0)

    def test_total_invested_step_up(self):
        flat = total_invested(10_000, 24)
        stepped = total_invested(10_000, 24, step_up_annual_pct=10)
        self.assertGreater(stepped, flat)

    def test_us_template_exists(self):
        rows = allocation_template("balanced", "some", "us")
        self.assertTrue(any("VOO" in r[0] for r in rows))


if __name__ == "__main__":
    unittest.main()
