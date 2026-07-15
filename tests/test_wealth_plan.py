"""Tests for wealth plan."""

from __future__ import annotations

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.wealth_plan import build_wealth_plan, format_wealth_plan_text


def test_build_wealth_plan_10cr():
    prefs = IntradayPrefs(
        capital=9000,
        wealth_goal_inr=10_00_00_000,
        monthly_sip_inr=5000,
        equity_only=True,
        min_daily_profit_pct=2.0,
        max_risk_pct=1.0,
    )
    plan = build_wealth_plan(prefs=prefs, monthly_sip_inr=5000, horizon_years=20)
    assert plan.goal_inr == 10_00_00_000
    assert plan.trading_capital_inr == 9000
    assert plan.monthly_sip_inr == 5000
    assert len(plan.phases) == 4
    assert plan.required_sip_inr > 0
    assert plan.projected_corpus_inr > plan.trading_capital_inr
    text = format_wealth_plan_text(plan)
    assert "10 Cr" in text
    assert "SIP" in text


def test_wealth_plan_income_save_rate():
    prefs = IntradayPrefs(capital=20_000, wealth_goal_inr=1_00_00_000)
    plan = build_wealth_plan(
        prefs=prefs,
        monthly_sip_inr=10_000,
        monthly_income_inr=50_000,
        horizon_years=15,
    )
    assert any("Save rate" in w for w in plan.this_week)
