"""Learn options premium stop/target ratios from CE/PE outcomes."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.suggestion_journal import journal_db_path
from analyzer.watchlist_learning import LOSS_OUTCOMES, WIN_OUTCOMES

IST = ZoneInfo("Asia/Kolkata")

DEFAULT_OPTIONS_STRATEGY = {
    "stop_mult": 0.65,
    "target_mult": 1.5,
    "prefer_recommended_only": True,
}

BOUNDS = {
    "stop_mult": (0.55, 0.75),
    "target_mult": (1.35, 1.75),
}

MIN_SAMPLES = 6
LOW_WIN_RATE = 45.0
HIGH_WIN_RATE = 65.0


@dataclass
class OptionsLearningChange:
    field: str
    old_value: float
    new_value: float
    reason: str


@dataclass
class OptionsLearningReport:
    samples: int
    wins: int
    losses: int
    win_rate_pct: float | None
    insights: list[str] = field(default_factory=list)
    changes: list[OptionsLearningChange] = field(default_factory=list)
    strategy: dict = field(default_factory=dict)


def strategy_path() -> Path:
    d = Path(__file__).resolve().parent.parent / "data" / "intraday"
    d.mkdir(parents=True, exist_ok=True)
    return d / "options_strategy.json"


def _default_state() -> dict:
    return {
        "strategy": dict(DEFAULT_OPTIONS_STRATEGY),
        "defaults": dict(DEFAULT_OPTIONS_STRATEGY),
        "history": [],
        "insights": [],
        "updated_at": None,
    }


def load_options_strategy_state() -> dict:
    path = strategy_path()
    if not path.exists():
        return _default_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        strat = {**DEFAULT_OPTIONS_STRATEGY, **data.get("strategy", {})}
        data["strategy"] = strat
        data.setdefault("defaults", dict(DEFAULT_OPTIONS_STRATEGY))
        data.setdefault("history", [])
        data.setdefault("insights", [])
        return data
    except Exception:
        return _default_state()


def save_options_strategy_state(state: dict) -> None:
    state["updated_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    strategy_path().write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_options_premium_strategy() -> dict:
    return dict(load_options_strategy_state()["strategy"])


def reset_options_strategy() -> dict:
    state = _default_state()
    save_options_strategy_state(state)
    return dict(state["strategy"])


def _clamp(key: str, value: float) -> float:
    lo, hi = BOUNDS[key]
    return round(max(lo, min(hi, value)), 2)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(journal_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def fetch_recommended_options_outcomes(*, days: int = 14) -> list[dict]:
    """Outcomes for ★ signal-aligned CE/PE picks."""
    from analyzer.options_watchlist_history import init_options_watchlist_history

    init_options_watchlist_history()
    cutoff = (datetime.now(IST).date() - timedelta(days=days)).isoformat()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT o.outcome, o.entry, o.stop_loss, o.target, s.recommended
            FROM options_watchlist_outcomes o
            JOIN options_watchlist_snapshots s
              ON s.trade_date = o.trade_date
             AND s.fno_symbol = o.fno_symbol
             AND s.option_type = o.option_type
             AND ABS(s.strike - o.strike) < 0.01
            WHERE o.trade_date >= ?
              AND o.outcome NOT IN ('no_data', 'pending')
              AND s.recommended = 1
            ORDER BY o.trade_date DESC
            """,
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def build_options_learning_report(*, days: int = 14) -> OptionsLearningReport:
    rows = fetch_recommended_options_outcomes(days=days)
    wins = [r for r in rows if r["outcome"] in WIN_OUTCOMES]
    losses = [r for r in rows if r["outcome"] in LOSS_OUTCOMES]
    decided = len(wins) + len(losses)
    wr = (100.0 * len(wins) / decided) if decided else None

    insights: list[str] = []
    if decided:
        insights.append(
            f"Options ★ side win rate: **{wr:.0f}%** over **{decided}** scored contracts "
            f"({len(wins)} wins · {len(losses)} losses)."
        )
    else:
        insights.append(
            "Need more scored **★** options picks — load CE/PE nightly and score after close."
        )

    return OptionsLearningReport(
        samples=decided,
        wins=len(wins),
        losses=len(losses),
        win_rate_pct=wr,
        insights=insights,
        strategy=get_options_premium_strategy(),
    )


def apply_options_strategy_tuning(report: OptionsLearningReport) -> OptionsLearningReport:
    if report.samples < MIN_SAMPLES or report.win_rate_pct is None:
        state = load_options_strategy_state()
        state["insights"] = report.insights
        save_options_strategy_state(state)
        return report

    state = load_options_strategy_state()
    strat = dict(state["strategy"])
    changes: list[OptionsLearningChange] = []
    wr = report.win_rate_pct

    def _set(field: str, new_val: float, reason: str) -> None:
        old = float(strat[field])
        new_val = _clamp(field, new_val)
        if new_val != old:
            changes.append(OptionsLearningChange(field, old, new_val, reason))
            strat[field] = new_val

    if wr < LOW_WIN_RATE:
        _set(
            "stop_mult",
            float(strat["stop_mult"]) - 0.03,
            f"Win rate {wr:.0f}% — tighter premium stop",
        )
        _set(
            "target_mult",
            float(strat["target_mult"]) - 0.05,
            f"Win rate {wr:.0f}% — take profits earlier",
        )
    elif wr >= HIGH_WIN_RATE and report.losses >= 2:
        _set(
            "stop_mult",
            float(strat["stop_mult"]) + 0.02,
            f"Win rate {wr:.0f}% — slightly wider stop",
        )
        _set(
            "target_mult",
            float(strat["target_mult"]) + 0.05,
            f"Win rate {wr:.0f}% — stretch target",
        )

    if changes:
        state["strategy"] = strat
        state["history"].append({
            "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
            "win_rate_pct": wr,
            "samples": report.samples,
            "changes": [
                {"field": c.field, "old": c.old_value, "new": c.new_value, "reason": c.reason}
                for c in changes
            ],
        })
        state["history"] = state["history"][-30:]
        state["insights"] = report.insights + [c.reason for c in changes]
        save_options_strategy_state(state)
        report.changes = changes
        report.strategy = strat
    else:
        state["insights"] = report.insights
        save_options_strategy_state(state)

    return report


def run_options_learning_cycle() -> OptionsLearningReport:
    report = build_options_learning_report()
    return apply_options_strategy_tuning(report)
