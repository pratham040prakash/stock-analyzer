"""Persist saved SIP goals and reminder preferences."""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.sip_planner import SipPlan, SipPlannerInput, build_sip_plan, sip_input_from_dict, sip_input_to_dict

IST = ZoneInfo("Asia/Kolkata")
GOALS_PATH = Path(__file__).resolve().parent.parent / "data" / "sip" / "goals.json"


@dataclass
class SavedSipGoal:
    goal_id: str
    created_at: str
    updated_at: str
    planner_input: dict
    monthly_sip: float
    projected_corpus: float
    target_amount: float
    reminder_day: int = 1
    reminders_enabled: bool = False
    currency: str = "₹"
    notes: str = ""


def _ensure_dir() -> None:
    GOALS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict:
    _ensure_dir()
    if not GOALS_PATH.exists():
        return {"version": 1, "goals": []}
    try:
        return json.loads(GOALS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "goals": []}


def _save_raw(data: dict) -> None:
    _ensure_dir()
    GOALS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _row_to_goal(d: dict) -> SavedSipGoal:
    return SavedSipGoal(
        goal_id=d["goal_id"],
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
        planner_input=d.get("planner_input", {}),
        monthly_sip=float(d.get("monthly_sip", 0)),
        projected_corpus=float(d.get("projected_corpus", 0)),
        target_amount=float(d.get("target_amount", 0)),
        reminder_day=int(d.get("reminder_day", 1)),
        reminders_enabled=bool(d.get("reminders_enabled", False)),
        currency=d.get("currency", "₹"),
        notes=d.get("notes", ""),
    )


def list_saved_goals() -> list[SavedSipGoal]:
    data = _load_raw()
    goals = [_row_to_goal(g) for g in data.get("goals", [])]
    goals.sort(key=lambda g: g.updated_at, reverse=True)
    return goals


def list_reminder_goals() -> list[SavedSipGoal]:
    return [g for g in list_saved_goals() if g.reminders_enabled]


def save_goal(
    inp: SipPlannerInput,
    plan: SipPlan,
    *,
    currency: str = "₹",
    reminder_day: int = 1,
    reminders_enabled: bool = False,
    notes: str = "",
    goal_id: str | None = None,
) -> SavedSipGoal:
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    data = _load_raw()
    goals: list[dict] = data.get("goals", [])
    gid = goal_id or f"sg_{secrets.token_hex(6)}"

    row = {
        "goal_id": gid,
        "created_at": now,
        "updated_at": now,
        "planner_input": sip_input_to_dict(inp),
        "monthly_sip": plan.monthly_sip,
        "projected_corpus": plan.projected_corpus,
        "target_amount": plan.target_amount,
        "reminder_day": max(1, min(28, reminder_day)),
        "reminders_enabled": reminders_enabled,
        "currency": currency,
        "notes": notes,
    }

    replaced = False
    for i, g in enumerate(goals):
        if g.get("goal_id") == gid:
            row["created_at"] = g.get("created_at", now)
            goals[i] = row
            replaced = True
            break
    if not replaced:
        goals.append(row)

    data["goals"] = goals
    _save_raw(data)
    return _row_to_goal(row)


def delete_goal(goal_id: str) -> bool:
    data = _load_raw()
    before = len(data.get("goals", []))
    data["goals"] = [g for g in data.get("goals", []) if g.get("goal_id") != goal_id]
    if len(data["goals"]) == before:
        return False
    _save_raw(data)
    return True


def update_reminder(goal_id: str, *, reminder_day: int | None = None, enabled: bool | None = None) -> bool:
    data = _load_raw()
    found = False
    for g in data.get("goals", []):
        if g.get("goal_id") != goal_id:
            continue
        if reminder_day is not None:
            g["reminder_day"] = max(1, min(28, reminder_day))
        if enabled is not None:
            g["reminders_enabled"] = enabled
        g["updated_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
        found = True
        break
    if found:
        _save_raw(data)
    return found


def rebuild_plan_from_saved(goal: SavedSipGoal) -> SipPlan:
    return build_sip_plan(sip_input_from_dict(goal.planner_input))


def mark_reminder_sent(goal_id: str) -> None:
    """Record last reminder timestamp to avoid duplicate sends same day."""
    state_path = GOALS_PATH.parent / "reminder_state.json"
    state: dict = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    today = datetime.now(IST).strftime("%Y-%m-%d")
    state[goal_id] = {"last_sent": today, "ts": time.time()}
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def was_reminder_sent_today(goal_id: str) -> bool:
    state_path = GOALS_PATH.parent / "reminder_state.json"
    if not state_path.exists():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        return state.get(goal_id, {}).get("last_sent") == datetime.now(IST).strftime("%Y-%m-%d")
    except Exception:
        return False
