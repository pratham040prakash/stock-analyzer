"""Tests for high-impact MIS enhancements."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.intraday_beginner_tips import build_capital_budget
from analyzer.prep_morning_nag import format_prep_morning_nag, needs_prep_nag
from analyzer.prep_status import is_nightly_prep_complete, prep_status_for, sync_selection_prep_step
from analyzer.trade_selection import (
    auto_select_top_by_rank,
    effective_trade_plans,
    toggle_selected,
)
from analyzer.trade_selection_scheduler import run_auto_trade_selection
from analyzer.watchlist_pins import PinnedPlan
from analyzer.watchlist_position_size import equity_position_hint
from analyzer.watchlist_live_alerts import check_watchlist_live_alerts


class TestPerTradeSizing(unittest.TestCase):
    def test_per_trade_caps_shares(self):
        budget = build_capital_budget(
            50_000,
            allocation_pct=50,
            max_risk_pct=1.0,
            max_concurrent_trades=2,
        )
        hint_full = equity_position_hint(
            "RELIANCE",
            entry=2500.0,
            stop_loss=2480.0,
            target=2550.0,
            allocated_inr=budget.allocated_inr,
            max_risk_pct=1.0,
            max_concurrent_trades=2,
            per_trade_budget_inr=budget.per_trade_budget_inr,
        )
        hint_no_cap = equity_position_hint(
            "RELIANCE",
            entry=2500.0,
            stop_loss=2480.0,
            target=2550.0,
            allocated_inr=budget.allocated_inr,
            max_risk_pct=1.0,
            max_concurrent_trades=1,
            per_trade_budget_inr=budget.allocated_inr,
        )
        self.assertLessEqual(hint_full.suggested_shares or 0, hint_no_cap.suggested_shares or 0)


class TestSectorCapSelection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.sel_path = Path(self.tmp.name) / "sel.json"
        self.p1 = patch("analyzer.trade_selection.SELECT_PATH", self.sel_path)
        self.p2 = patch("analyzer.trade_selection.session_target_date", return_value="2026-07-07")
        self.p3 = patch(
            "analyzer.trade_selection.sector_for_symbol",
            side_effect=lambda s: {"A": "Banking", "B": "Banking", "C": "IT"}.get(s, ""),
        )
        self.p1.start()
        self.p2.start()
        self.p3.start()

    def tearDown(self):
        self.p3.stop()
        self.p2.stop()
        self.p1.stop()
        self.tmp.cleanup()

    def test_blocks_second_same_sector_when_cap_one(self):
        ok, _ = toggle_selected("A", sector="Banking", max_selected=2, max_same_sector=1)
        self.assertTrue(ok)
        ok, msg = toggle_selected("B", sector="Banking", max_selected=2, max_same_sector=1)
        self.assertFalse(ok)
        self.assertIn("Banking", msg)


class TestAutoSelect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.sel_path = Path(self.tmp.name) / "sel.json"
        self.state_path = Path(self.tmp.name) / "state.json"
        self.p1 = patch("analyzer.trade_selection.SELECT_PATH", self.sel_path)
        self.p2 = patch("analyzer.trade_selection_scheduler.STATE_PATH", self.state_path)
        self.p3 = patch("analyzer.trade_selection.session_target_date", return_value="2026-07-07")
        self.p4 = patch("analyzer.trade_selection_scheduler.session_target_date", return_value="2026-07-07")
        self.p1.start()
        self.p2.start()
        self.p3.start()
        self.p4.start()

    def tearDown(self):
        self.p4.stop()
        self.p3.stop()
        self.p2.stop()
        self.p1.stop()
        self.tmp.cleanup()

    @patch("analyzer.trade_selection.load_pinned_plans")
    def test_auto_top_two(self, load_pins):
        load_pins.return_value = [
            PinnedPlan("RELIANCE", 1, 1, 2, "x"),
            PinnedPlan("TCS", 1, 1, 2, "x"),
            PinnedPlan("INFY", 1, 1, 2, "x"),
        ]
        ok, msg = auto_select_top_by_rank(trade_date="2026-07-07")
        self.assertTrue(ok)
        self.assertIn("RELIANCE", msg)
        plans = effective_trade_plans("2026-07-07")
        self.assertEqual(len(plans), 2)

    @patch("analyzer.trade_selection.load_pinned_plans")
    def test_scheduler_force(self, load_pins):
        load_pins.return_value = [
            PinnedPlan("RELIANCE", 1, 1, 2, "x"),
            PinnedPlan("TCS", 1, 1, 2, "x"),
        ]
        count, status = run_auto_trade_selection(force=True)
        self.assertEqual(count, 1)
        self.assertIn("Auto-picked", status)


class TestPrepMorningNag(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "prep.json"
        self.p = patch("analyzer.prep_status.STATUS_PATH", self.path)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()

    @patch("analyzer.prep_status.session_target_date", return_value="2026-07-07")
    @patch("analyzer.prep_morning_nag.session_target_date", return_value="2026-07-07")
    def test_needs_nag_when_incomplete(self, _d1, _d2):
        self.assertTrue(needs_prep_nag("2026-07-07"))
        msg = format_prep_morning_nag()
        self.assertIn("incomplete", msg.lower())

    @patch("analyzer.prep_status.session_target_date", return_value="2026-07-07")
    @patch("analyzer.prep_morning_nag.session_target_date", return_value="2026-07-07")
    @patch("analyzer.prep_status.is_selection_complete", return_value=True)
    def test_complete_no_nag(self, _sel, _d1, _d2):
        from analyzer.prep_status import mark_prep_step

        mark_prep_step("equity", trade_date="2026-07-07")
        mark_prep_step("options", trade_date="2026-07-07")
        mark_prep_step("telegram", trade_date="2026-07-07")
        mark_prep_step("selection", trade_date="2026-07-07")
        self.assertFalse(needs_prep_nag("2026-07-07"))


class TestLiveAlerts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "alerts.json"
        self.sel = Path(self.tmp.name) / "sel.json"
        self.p1 = patch("analyzer.watchlist_live_alerts.STATE_PATH", self.state)
        self.p2 = patch("analyzer.trade_selection.SELECT_PATH", self.sel)
        self.p3 = patch("analyzer.trade_selection.session_target_date", return_value="2026-07-07")
        self.p4 = patch("analyzer.watchlist_live_alerts.session_target_date", return_value="2026-07-07")
        self.p1.start()
        self.p2.start()
        self.p3.start()
        self.p4.start()
        from analyzer.trade_selection import set_selected_symbols

        set_selected_symbols(["RELIANCE"], trade_date="2026-07-07")

    def tearDown(self):
        self.p4.stop()
        self.p3.stop()
        self.p2.stop()
        self.p1.stop()
        self.tmp.cleanup()

    @patch("analyzer.watchlist_live_alerts.get_live_ltp", return_value=(2475.0, "kite"))
    @patch("analyzer.trade_selection.load_pinned_plans")
    def test_entry_near_alert_once(self, load_pins, _ltp):
        load_pins.return_value = [
            PinnedPlan("RELIANCE", 2500.0, 2480.0, 2550.0, "x"),
        ]
        msgs = check_watchlist_live_alerts(trade_date="2026-07-07")
        self.assertTrue(any("RELIANCE" in m for m in msgs))
        again = check_watchlist_live_alerts(trade_date="2026-07-07")
        self.assertEqual(again, [])


if __name__ == "__main__":
    unittest.main()
