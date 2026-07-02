"""Monthly SIP reminder scheduling and Telegram formatting."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.sip_export import plan_to_markdown
from analyzer.sip_planner import SipPlan
from analyzer.sip_storage import (
    SavedSipGoal,
    list_reminder_goals,
    mark_reminder_sent,
    rebuild_plan_from_saved,
    was_reminder_sent_today,
)

IST = ZoneInfo("Asia/Kolkata")


def is_sip_reminder_day(day: int | None = None) -> bool:
    """True on reminder day of month (default: today)."""
    d = day if day is not None else datetime.now(IST).day
    return 1 <= d <= 28


def goals_due_today(goals: list[SavedSipGoal] | None = None) -> list[SavedSipGoal]:
    today = datetime.now(IST).day
    pool = goals if goals is not None else list_reminder_goals()
    return [
        g for g in pool
        if g.reminders_enabled and g.reminder_day == today and not was_reminder_sent_today(g.goal_id)
    ]


def format_sip_plan_telegram(plan: SipPlan, *, currency: str = "₹") -> str:
    lines = [
        f"*SIP Plan — {plan.goal_name}*",
        f"Monthly: *{currency}{plan.monthly_sip:,.0f}*",
        f"Target: {currency}{plan.target_amount:,.0f} in {plan.years:.0f}y",
        f"Projected: *{currency}{plan.projected_corpus:,.0f}* @ {plan.annual_return_pct:.0f}%",
        "",
        "*Allocation:*",
    ]
    for line in plan.allocation[:6]:
        ticker = line.ticker.replace(".NS", "")
        lines.append(
            f"• {ticker} — {currency}{line.monthly_amount:,.0f} ({line.weight_pct:.0f}%)"
        )
    lines.append("_Not financial advice._")
    return "\n".join(lines)


def format_sip_reminder_telegram(goal: SavedSipGoal) -> str:
    inp_name = goal.planner_input.get("goal_name", "SIP goal")
    lines = [
        f"*SIP reminder — {inp_name}*",
        f"Invest *{goal.currency}{goal.monthly_sip:,.0f}* today (day {goal.reminder_day} of month).",
        f"Target: {goal.currency}{goal.target_amount:,.0f} · "
        f"On track for {goal.currency}{goal.projected_corpus:,.0f}",
    ]
    plan = rebuild_plan_from_saved(goal)
    top = plan.allocation[:4]
    if top:
        lines.append("")
        lines.append("*Split:*")
        for line in top:
            ticker = line.ticker.replace(".NS", "")
            lines.append(f"• {ticker} {goal.currency}{line.monthly_amount:,.0f}")
    if goal.notes:
        lines.append(f"_{goal.notes[:120]}_")
    lines.append("_Not financial advice._")
    return "\n".join(lines)


def format_combined_reminder_message(goals: list[SavedSipGoal]) -> str:
    if len(goals) == 1:
        return format_sip_reminder_telegram(goals[0])
    lines = [f"*SIP reminders — {len(goals)} goals*"]
    for g in goals:
        name = g.planner_input.get("goal_name", "Goal")
        lines.append(f"• *{name}*: {g.currency}{g.monthly_sip:,.0f}")
    lines.append("_Not financial advice._")
    return "\n".join(lines)


def run_sip_reminders(*, force: bool = False) -> tuple[int, str]:
    """
    Send Telegram SIP reminders for goals due today.
    Returns (count_sent, status_message).
    """
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    if not telegram_configured():
        return 0, "Telegram not configured"

    due = goals_due_today()
    if not due and not force:
        if not is_sip_reminder_day():
            return 0, "Not a reminder day (1–28)"
        return 0, "No goals due today"

    if force and not due:
        due = list_reminder_goals()[:3]
        if not due:
            return 0, "No saved goals with reminders enabled"

    msg = format_combined_reminder_message(due)
    ok, err = send_telegram_broadcast(msg, alert_type="sip")
    if ok:
        for g in due:
            mark_reminder_sent(g.goal_id)
        return len(due), f"Sent reminders for {len(due)} goal(s)"
    return 0, err


def export_plan_text(plan: SipPlan, *, currency: str = "₹", fmt: str = "markdown") -> str:
    if fmt == "csv":
        from analyzer.sip_export import plan_to_csv
        return plan_to_csv(plan, currency=currency)
    return plan_to_markdown(plan, currency=currency)
