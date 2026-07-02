"""Auto-calibrate Market Pulse score gates from validated suggestion outcomes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.suggestion_learning import LearningReport, PerformanceSlice

IST = ZoneInfo("Asia/Kolkata")

DEFAULT_THRESHOLDS = {
    "intraday": 35,
    "short": 22,
    "long": 28,
}

BOUNDS = {
    "intraday": (25, 50),
    "short": (15, 35),
    "long": (20, 40),
}

MIN_SAMPLES = 8
LOW_WIN_RATE = 45.0
VERY_LOW_WIN_RATE = 40.0
HIGH_WIN_RATE = 62.0
STEP_UP_SMALL = 3
STEP_UP_LARGE = 5
STEP_DOWN = 2

HORIZON_LABELS = {
    "intraday": "Horizon: intraday",
    "short": "Horizon: short",
    "long": "Horizon: long",
}


def thresholds_path() -> Path:
    d = Path(__file__).resolve().parent.parent / "data" / "suggestions"
    d.mkdir(parents=True, exist_ok=True)
    return d / "thresholds.json"


@dataclass
class ThresholdChange:
    horizon: str
    old_value: int
    new_value: int
    win_rate_pct: float
    scored: int
    reason: str


@dataclass
class TuningResult:
    thresholds: dict[str, int]
    changes: list[ThresholdChange] = field(default_factory=list)
    applied: bool = False


def _default_payload() -> dict:
    return {
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "defaults": dict(DEFAULT_THRESHOLDS),
        "history": [],
        "updated_at": None,
    }


def load_threshold_state() -> dict:
    path = thresholds_path()
    if not path.exists():
        return _default_payload()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in DEFAULT_THRESHOLDS:
            data.setdefault("thresholds", {})[key] = int(
                data.get("thresholds", {}).get(key, DEFAULT_THRESHOLDS[key])
            )
        data.setdefault("defaults", dict(DEFAULT_THRESHOLDS))
        data.setdefault("history", [])
        return data
    except Exception:
        return _default_payload()


def save_threshold_state(state: dict) -> None:
    state["updated_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    thresholds_path().write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_pulse_thresholds() -> dict[str, int]:
    """Effective min-score gates for Market Pulse pick filters."""
    return dict(load_threshold_state()["thresholds"])


def _clamp(horizon: str, value: int) -> int:
    lo, hi = BOUNDS[horizon]
    return max(lo, min(hi, value))


def _propose_change(
    horizon: str,
    current: int,
    slice_: PerformanceSlice | None,
) -> ThresholdChange | None:
    if slice_ is None or slice_.scored < MIN_SAMPLES:
        return None

    wr = slice_.win_rate_pct
    if wr < VERY_LOW_WIN_RATE:
        new_val = _clamp(horizon, current + STEP_UP_LARGE)
        reason = f"Win rate {wr:.0f}% — tightened gate (+{STEP_UP_LARGE})"
    elif wr < LOW_WIN_RATE:
        new_val = _clamp(horizon, current + STEP_UP_SMALL)
        reason = f"Win rate {wr:.0f}% — tightened gate (+{STEP_UP_SMALL})"
    elif wr >= HIGH_WIN_RATE and slice_.losses >= 2:
        new_val = _clamp(horizon, current - STEP_DOWN)
        reason = f"Win rate {wr:.0f}% — relaxed gate (-{STEP_DOWN})"
    else:
        return None

    if new_val == current:
        return None

    return ThresholdChange(
        horizon=horizon,
        old_value=current,
        new_value=new_val,
        win_rate_pct=wr,
        scored=slice_.scored,
        reason=reason,
    )


def apply_threshold_tuning(report: LearningReport) -> TuningResult:
    """
    Adjust intraday / short / long min scores from journal win rates.
    Requires MIN_SAMPLES scored picks per horizon before changing.
    """
    state = load_threshold_state()
    current = dict(state["thresholds"])
    by_label = {s.label: s for s in report.slices}
    changes: list[ThresholdChange] = []

    for horizon, label in HORIZON_LABELS.items():
        change = _propose_change(horizon, current[horizon], by_label.get(label))
        if change:
            current[horizon] = change.new_value
            changes.append(change)
            state["history"].append({
                "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
                "horizon": horizon,
                "old": change.old_value,
                "new": change.new_value,
                "win_rate_pct": change.win_rate_pct,
                "scored": change.scored,
                "reason": change.reason,
            })

    if changes:
        state["thresholds"] = current
        state["history"] = state["history"][-50:]
        save_threshold_state(state)

    return TuningResult(thresholds=current, changes=changes, applied=bool(changes))


def reset_thresholds() -> dict[str, int]:
    """Restore defaults (e.g. after strategy version bump)."""
    state = _default_payload()
    save_threshold_state(state)
    return dict(state["thresholds"])


def recent_tuning_history(limit: int = 10) -> list[dict]:
    return list(reversed(load_threshold_state().get("history", [])[-limit:]))
