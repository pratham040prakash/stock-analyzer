"""Tests for SIP export, storage, and reminders."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.sip_planner import SipAllocationLine, SipPlannerInput, SipPlan, build_sip_plan
from analyzer.sip_export import plan_to_csv, plan_to_markdown
from analyzer.sip_reminders import format_sip_plan_telegram, format_sip_reminder_telegram, goals_due_today
from analyzer.sip_storage import SavedSipGoal, delete_goal, list_saved_goals, save_goal


def _sample_plan() -> SipPlan:
    inp = SipPlannerInput(
        goal_name="Wealth building",
        target_amount=10_00_000,
        years=10,
        market="india",
    )
    return build_sip_plan(inp)


class TestSipExport(unittest.TestCase):
    def test_markdown_contains_summary(self):
        plan = _sample_plan()
        md = plan_to_markdown(plan)
        self.assertIn("Wealth building", md)
        self.assertIn("Monthly SIP", md)

    def test_csv_has_allocation_header(self):
        plan = _sample_plan()
        csv_text = plan_to_csv(plan)
        self.assertIn("Instrument", csv_text)
        self.assertIn("NIFTYBEES", csv_text.upper() + csv_text)


class TestSipStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.goals = Path(self.tmp.name) / "goals.json"
        self.state = Path(self.tmp.name) / "reminder_state.json"
        self.p_goals = patch("analyzer.sip_storage.GOALS_PATH", self.goals)
        self.p_state = patch("analyzer.sip_storage.GOALS_PATH", self.goals)
        self.p_goals.start()

    def tearDown(self):
        self.p_goals.stop()
        self.tmp.cleanup()

    def test_save_and_list(self):
        inp = SipPlannerInput(goal_name="Retirement", target_amount=50_00_000, years=15)
        plan = build_sip_plan(inp)
        saved = save_goal(inp, plan, reminders_enabled=True, reminder_day=5)
        self.assertEqual(len(list_saved_goals()), 1)
        self.assertEqual(saved.reminder_day, 5)
        self.assertTrue(delete_goal(saved.goal_id))


class TestSipReminders(unittest.TestCase):
    def test_telegram_format(self):
        plan = _sample_plan()
        msg = format_sip_plan_telegram(plan)
        self.assertIn("SIP Plan", msg)
        self.assertIn("Allocation", msg)

    def test_reminder_for_goal(self):
        goal = SavedSipGoal(
            goal_id="x",
            created_at="",
            updated_at="",
            planner_input={"goal_name": "House"},
            monthly_sip=20_000,
            projected_corpus=30_00_000,
            target_amount=30_00_000,
            reminder_day=1,
            reminders_enabled=True,
        )
        msg = format_sip_reminder_telegram(goal)
        self.assertIn("House", msg)
        self.assertIn("20,000", msg)

    def test_goals_due_filters_day(self):
        g1 = SavedSipGoal(
            goal_id="a", created_at="", updated_at="",
            planner_input={}, monthly_sip=1000, projected_corpus=10000,
            target_amount=10000, reminder_day=99, reminders_enabled=True,
        )
        self.assertEqual(goals_due_today([g1]), [])


if __name__ == "__main__":
    unittest.main()
