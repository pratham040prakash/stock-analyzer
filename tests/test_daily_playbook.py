"""Tests for daily playbook."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.daily_playbook import build_daily_playbook, format_playbook_text
from analyzer.intraday_prefs import IntradayPrefs

IST = ZoneInfo("Asia/Kolkata")


def test_build_daily_playbook_beginner():
    prefs = IntradayPrefs(
        capital=9000,
        min_daily_profit_pct=2.0,
        beginner_mode=True,
        equity_only=True,
        max_trades=1,
    )
    pb = build_daily_playbook(
        now=datetime(2026, 7, 15, 10, 0, tzinfo=IST),
        prefs=prefs,
    )
    assert pb.daily_profit_target_inr == 180.0
    assert pb.equity_only is True
    assert pb.beginner_mode is True
    assert len(pb.steps) >= 8
    assert pb.next_step
    text = format_playbook_text(pb)
    assert "Daily playbook" in text
    assert "180" in text


def test_options_step_blocked_in_equity_only():
    prefs = IntradayPrefs(equity_only=True)
    pb = build_daily_playbook(prefs=prefs)
    opt_steps = [s for s in pb.steps if s.id == "options_gate"]
    assert len(opt_steps) == 1
    assert opt_steps[0].status == "blocked"
