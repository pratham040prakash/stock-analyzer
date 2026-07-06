"""Learn watchlist screening rules from target/stop outcomes (daily EOD tuning)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo

from analyzer.suggestion_journal import journal_db_path
from analyzer.watchlist_history import (
    can_score_trade_date,
    init_watchlist_history,
    score_daily_watchlist,
)

IST = ZoneInfo("Asia/Kolkata")

DEFAULT_STRATEGY = {
    "min_atr_pct": 1.5,
    "min_volume_ratio": 1.0,
    "rsi_bull_min": 55.0,
    "rsi_bull_max": 65.0,
    "min_checklist_passed": 3,
    "min_prep_score": 36.0,
    "require_rsi_macd": False,
    "require_sector_tailwind": False,
    "max_watchlist": 5,
    "feature_weights": None,
    "baseline_hit_rate": 0.52,
    "research_version": 0,
    "research_samples": 0,
    "research_at": None,
}

BOUNDS = {
    "min_atr_pct": (1.2, 3.5),
    "min_volume_ratio": (1.0, 2.5),
    "rsi_bull_min": (50.0, 60.0),
    "rsi_bull_max": (62.0, 72.0),
    "min_checklist_passed": (3, 5),
    "min_prep_score": (30.0, 80.0),
    "max_watchlist": (3, 5),
}

MIN_SAMPLES = 8
LOW_WIN_RATE = 50.0
VERY_LOW_WIN_RATE = 40.0
HIGH_WIN_RATE = 70.0

WIN_OUTCOMES = frozenset({"target_hit", "flat_positive"})
LOSS_OUTCOMES = frozenset({"stop_hit", "mixed"})


def strategy_path() -> Path:
    d = Path(__file__).resolve().parent.parent / "data" / "intraday"
    d.mkdir(parents=True, exist_ok=True)
    return d / "watchlist_strategy.json"


@dataclass
class PickFeatureRow:
    trade_date: str
    symbol: str
    outcome: str
    prep_score: float
    checklist_passed: int
    atr_pct: float | None
    rsi: float | None
    volume_ratio: float | None
    sector_tailwind: bool
    macd_bullish: bool


@dataclass
class StrategyChange:
    field: str
    old_value: float | int | bool
    new_value: float | int | bool
    reason: str


@dataclass
class WatchlistLearningReport:
    samples: int
    wins: int
    losses: int
    win_rate_pct: float | None
    insights: list[str] = field(default_factory=list)
    changes: list[StrategyChange] = field(default_factory=list)
    strategy: dict = field(default_factory=dict)


def _default_state() -> dict:
    return {
        "strategy": dict(DEFAULT_STRATEGY),
        "defaults": dict(DEFAULT_STRATEGY),
        "history": [],
        "insights": [],
        "updated_at": None,
    }


def load_strategy_state() -> dict:
    path = strategy_path()
    if not path.exists():
        return _default_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        strat = {**DEFAULT_STRATEGY, **data.get("strategy", {})}
        data["strategy"] = strat
        data.setdefault("defaults", dict(DEFAULT_STRATEGY))
        data.setdefault("history", [])
        data.setdefault("insights", [])
        return data
    except Exception:
        return _default_state()


def save_strategy_state(state: dict) -> None:
    state["updated_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    strategy_path().write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_watchlist_strategy() -> dict:
    """Effective screening gates for pre-market watchlist builder."""
    strat = dict(load_strategy_state()["strategy"])
    strat["max_watchlist"] = _clamp_int(
        "max_watchlist", int(strat.get("max_watchlist", DEFAULT_STRATEGY["max_watchlist"]))
    )
    if not strat.get("feature_weights"):
        from analyzer.suggestion_features import DEFAULT_FEATURE_WEIGHTS

        strat["feature_weights"] = dict(DEFAULT_FEATURE_WEIGHTS)
    return strat


def reset_watchlist_strategy() -> dict:
    state = _default_state()
    save_strategy_state(state)
    return dict(state["strategy"])


def recent_strategy_history(limit: int = 8) -> list[dict]:
    return list(reversed(load_strategy_state().get("history", [])[-limit:]))


def _clamp_num(key: str, value: float) -> float:
    lo, hi = BOUNDS[key]
    return max(lo, min(hi, value))


def _clamp_int(key: str, value: int) -> int:
    lo, hi = BOUNDS[key]
    return max(lo, min(hi, value))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(journal_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_watchlist_features() -> None:
    init_watchlist_history()


def fetch_pick_features(*, days: int = 14) -> list[PickFeatureRow]:
    """Join scored outcomes with snapshot features for learning."""
    init_watchlist_history()
    cutoff = (datetime.now(IST).date() - timedelta(days=days)).isoformat()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT
                o.trade_date, o.symbol, o.outcome,
                COALESCE(s.prep_score, 0) AS prep_score,
                COALESCE(s.checklist_passed, 0) AS checklist_passed,
                s.atr_pct, s.rsi, s.volume_ratio,
                COALESCE(s.sector_tailwind, 0) AS sector_tailwind,
                COALESCE(s.macd_bullish, 0) AS macd_bullish
            FROM watchlist_outcomes o
            LEFT JOIN watchlist_daily_snapshots s
              ON s.trade_date = o.trade_date AND s.symbol = o.symbol
            WHERE o.trade_date >= ?
              AND o.outcome NOT IN ('no_data', 'pending')
            ORDER BY o.trade_date DESC
            """,
            (cutoff,),
        ).fetchall()
    return [
        PickFeatureRow(
            trade_date=r["trade_date"],
            symbol=r["symbol"],
            outcome=r["outcome"],
            prep_score=float(r["prep_score"] or 0),
            checklist_passed=int(r["checklist_passed"] or 0),
            atr_pct=float(r["atr_pct"]) if r["atr_pct"] is not None else None,
            rsi=float(r["rsi"]) if r["rsi"] is not None else None,
            volume_ratio=float(r["volume_ratio"]) if r["volume_ratio"] is not None else None,
            sector_tailwind=bool(r["sector_tailwind"]),
            macd_bullish=bool(r["macd_bullish"]),
        )
        for r in rows
    ]


def _avg(rows: list[PickFeatureRow], attr: str) -> float | None:
    vals = [getattr(r, attr) for r in rows if getattr(r, attr) is not None]
    return mean(vals) if vals else None


def build_watchlist_learning_report(*, days: int = 14) -> WatchlistLearningReport:
    rows = fetch_pick_features(days=days)
    wins = [r for r in rows if r.outcome in WIN_OUTCOMES]
    losses = [r for r in rows if r.outcome in LOSS_OUTCOMES]
    decided = wins + losses
    wr = (100.0 * len(wins) / len(decided)) if decided else None

    insights: list[str] = []
    if len(decided) < MIN_SAMPLES:
        insights.append(
            f"**{len(decided)}/{MIN_SAMPLES}** scored picks — need more days before auto-tuning."
        )
    elif wr is not None:
        insights.append(
            f"Watchlist win rate (target / flat+ vs stop): **{wr:.0f}%** "
            f"over **{len(decided)}** decisive picks ({len(wins)} wins · {len(losses)} losses)."
        )
        win_atr = _avg(wins, "atr_pct")
        loss_atr = _avg(losses, "atr_pct")
        if win_atr and loss_atr and win_atr > loss_atr + 0.15:
            insights.append(
                f"Winners averaged **{win_atr:.1f}%** ATR vs **{loss_atr:.1f}%** for stops — "
                "favouring higher volatility names."
            )
        win_tail = sum(1 for r in wins if r.sector_tailwind) / max(len(wins), 1)
        loss_tail = sum(1 for r in losses if r.sector_tailwind) / max(len(losses), 1)
        if win_tail - loss_tail >= 0.2:
            insights.append("Leading-sector tailwind correlates with target hits.")

    return WatchlistLearningReport(
        samples=len(rows),
        wins=len(wins),
        losses=len(losses),
        win_rate_pct=wr,
        insights=insights,
        strategy=get_watchlist_strategy(),
    )


def apply_watchlist_strategy_tuning(
    report: WatchlistLearningReport | None = None,
) -> WatchlistLearningReport:
    """Tighten/relax watchlist gates from target-hit history."""
    report = report or build_watchlist_learning_report()
    decided = report.wins + report.losses
    if decided < MIN_SAMPLES or report.win_rate_pct is None:
        return report

    state = load_strategy_state()
    strat = dict(state["strategy"])
    changes: list[StrategyChange] = []
    wr = report.win_rate_pct
    rows = fetch_pick_features()
    wins = [r for r in rows if r.outcome in WIN_OUTCOMES]

    def _set(key: str, new_val: float | int | bool, reason: str) -> None:
        old = strat[key]
        if old != new_val:
            changes.append(StrategyChange(key, old, new_val, reason))
            strat[key] = new_val

    if wr < VERY_LOW_WIN_RATE:
        _set(
            "min_checklist_passed",
            _clamp_int("min_checklist_passed", int(strat["min_checklist_passed"]) + 1),
            f"Win rate {wr:.0f}% — require more checklist points",
        )
        _set(
            "min_atr_pct",
            round(_clamp_num("min_atr_pct", float(strat["min_atr_pct"]) + 0.25), 2),
            f"Win rate {wr:.0f}% — raise min ATR%",
        )
        _set("require_rsi_macd", True, f"Win rate {wr:.0f}% — require RSI+MACD alignment")
        _set(
            "max_watchlist",
            _clamp_int("max_watchlist", int(strat["max_watchlist"]) - 2),
            f"Win rate {wr:.0f}% — fewer names, higher quality",
        )
    elif wr < LOW_WIN_RATE:
        _set(
            "min_atr_pct",
            round(_clamp_num("min_atr_pct", float(strat["min_atr_pct"]) + 0.1), 2),
            f"Win rate {wr:.0f}% — slight ATR tighten",
        )
        _set(
            "min_checklist_passed",
            _clamp_int("min_checklist_passed", max(int(strat["min_checklist_passed"]), 4)),
            f"Win rate {wr:.0f}% — at least 4/5 checklist",
        )
        _set(
            "max_watchlist",
            _clamp_int("max_watchlist", int(strat["max_watchlist"]) - 1),
            f"Win rate {wr:.0f}% — trim watchlist size",
        )
    elif wr >= HIGH_WIN_RATE and report.losses >= 2:
        _set(
            "min_atr_pct",
            round(_clamp_num("min_atr_pct", float(strat["min_atr_pct"]) - 0.05), 2),
            f"Win rate {wr:.0f}% — slight ATR relax",
        )
        if int(strat["max_watchlist"]) < BOUNDS["max_watchlist"][1]:
            _set(
                "max_watchlist",
                _clamp_int("max_watchlist", int(strat["max_watchlist"]) + 1),
                f"Win rate {wr:.0f}% — allow one more pick",
            )

    if wins:
        win_scores = sorted(r.prep_score for r in wins if r.prep_score > 0)
        if win_scores:
            p25 = win_scores[max(0, len(win_scores) // 4)]
            floor_score = round(_clamp_num("min_prep_score", max(float(strat["min_prep_score"]), p25)), 1)
            if floor_score > float(strat["min_prep_score"]):
                _set(
                    "min_prep_score",
                    floor_score,
                    "Raised min prep score toward winning pick profile",
                )

        win_tail_rate = sum(1 for r in wins if r.sector_tailwind) / len(wins)
        if win_tail_rate >= 0.6 and wr < HIGH_WIN_RATE:
            _set("require_sector_tailwind", True, "Sector leaders hitting targets more often")

    if changes:
        state["strategy"] = strat
        state["history"].append({
            "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
            "win_rate_pct": wr,
            "samples": decided,
            "changes": [
                {"field": c.field, "old": c.old_value, "new": c.new_value, "reason": c.reason}
                for c in changes
            ],
        })
        state["history"] = state["history"][-40:]
        state["insights"] = report.insights + [c.reason for c in changes]
        save_strategy_state(state)
        report.changes = changes
        report.strategy = strat
    else:
        state["insights"] = report.insights
        save_strategy_state(state)

    return report


def score_pending_watchlist_sessions(*, market: str = "india") -> int:
    """Score every past session that has snapshots but incomplete outcomes."""
    init_watchlist_features()
    cutoff = (datetime.now(IST).date() - timedelta(days=14)).isoformat()
    with _connect() as conn:
        dates = [
            r[0]
            for r in conn.execute(
                """
                SELECT DISTINCT trade_date FROM watchlist_daily_snapshots
                WHERE trade_date >= ? ORDER BY trade_date DESC
                """,
                (cutoff,),
            ).fetchall()
        ]
    total = 0
    for td in dates:
        if can_score_trade_date(td):
            total += len(score_daily_watchlist(trade_date=td, market=market))
    return total


def run_watchlist_learning_cycle(*, market: str = "india") -> WatchlistLearningReport:
    """Post-close: score outcomes → analyze winners → tune screening gates."""
    score_pending_watchlist_sessions(market=market)
    try:
        from analyzer.options_watchlist_history import score_pending_options_sessions

        score_pending_options_sessions()
    except Exception:
        pass
    try:
        from analyzer.options_watchlist_learning import run_options_learning_cycle

        run_options_learning_cycle()
    except Exception:
        pass
    report = build_watchlist_learning_report()
    return apply_watchlist_strategy_tuning(report)
