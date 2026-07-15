"""Persist intraday capital / risk settings across sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from analyzer.intraday_beginner_tips import (
    DEFAULT_INTRADAY_ALLOCATION_PCT,
    DEFAULT_MAX_CONCURRENT_TRADES,
)
from analyzer.intraday_trade_plan import DEFAULT_MAX_RISK_PCT
from analyzer.profit_targets import PROFIT_MODES

PREFS_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "prefs.json"

DEFAULT_CAPITAL_INR = 50_000.0
DEFAULT_PROFIT_MODE = "aggressive"
DEFAULT_MIN_DAILY_PROFIT_PCT = 20.0
DEFAULT_TARGET_DAILY_PROFIT_PCT = 25.0
DEFAULT_STRETCH_DAILY_PROFIT_PCT = 35.0
DEFAULT_WEALTH_GOAL_INR = 10_00_00_000.0
DEFAULT_MONTHLY_SIP_INR = 5_000.0


@dataclass
class IntradayPrefs:
    capital: float = DEFAULT_CAPITAL_INR
    allocation_pct: float = DEFAULT_INTRADAY_ALLOCATION_PCT
    max_risk_pct: float = DEFAULT_MAX_RISK_PCT
    max_trades: int = DEFAULT_MAX_CONCURRENT_TRADES
    profit_mode: str = DEFAULT_PROFIT_MODE
    min_daily_profit_pct: float = DEFAULT_MIN_DAILY_PROFIT_PCT
    target_daily_profit_pct: float = DEFAULT_TARGET_DAILY_PROFIT_PCT
    stretch_daily_profit_pct: float = DEFAULT_STRETCH_DAILY_PROFIT_PCT
    beginner_mode: bool = False
    equity_only: bool = False
    wealth_goal_inr: float = DEFAULT_WEALTH_GOAL_INR
    monthly_sip_inr: float = DEFAULT_MONTHLY_SIP_INR


def _ensure_dir() -> None:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_intraday_prefs() -> IntradayPrefs:
    _ensure_dir()
    if not PREFS_PATH.exists():
        return IntradayPrefs()
    try:
        raw = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        mode = str(raw.get("profit_mode", DEFAULT_PROFIT_MODE)).lower()
        if mode not in PROFIT_MODES:
            mode = DEFAULT_PROFIT_MODE
        return IntradayPrefs(
            capital=float(raw.get("capital", DEFAULT_CAPITAL_INR)),
            allocation_pct=float(raw.get("allocation_pct", DEFAULT_INTRADAY_ALLOCATION_PCT)),
            max_risk_pct=float(raw.get("max_risk_pct", DEFAULT_MAX_RISK_PCT)),
            max_trades=int(raw.get("max_trades", DEFAULT_MAX_CONCURRENT_TRADES)),
            profit_mode=mode,
            min_daily_profit_pct=float(raw.get("min_daily_profit_pct", DEFAULT_MIN_DAILY_PROFIT_PCT)),
            target_daily_profit_pct=float(
                raw.get("target_daily_profit_pct", DEFAULT_TARGET_DAILY_PROFIT_PCT)
            ),
            stretch_daily_profit_pct=float(
                raw.get("stretch_daily_profit_pct", DEFAULT_STRETCH_DAILY_PROFIT_PCT)
            ),
            beginner_mode=bool(raw.get("beginner_mode", False)),
            equity_only=bool(raw.get("equity_only", False)),
            wealth_goal_inr=float(raw.get("wealth_goal_inr", DEFAULT_WEALTH_GOAL_INR)),
            monthly_sip_inr=float(raw.get("monthly_sip_inr", DEFAULT_MONTHLY_SIP_INR)),
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return IntradayPrefs()


def save_intraday_prefs(prefs: IntradayPrefs) -> None:
    _ensure_dir()
    PREFS_PATH.write_text(
        json.dumps(
            {
                "capital": prefs.capital,
                "allocation_pct": prefs.allocation_pct,
                "max_risk_pct": prefs.max_risk_pct,
                "max_trades": prefs.max_trades,
                "profit_mode": prefs.profit_mode,
                "min_daily_profit_pct": prefs.min_daily_profit_pct,
                "target_daily_profit_pct": prefs.target_daily_profit_pct,
                "stretch_daily_profit_pct": prefs.stretch_daily_profit_pct,
                "beginner_mode": prefs.beginner_mode,
                "equity_only": prefs.equity_only,
                "wealth_goal_inr": prefs.wealth_goal_inr,
                "monthly_sip_inr": prefs.monthly_sip_inr,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def prefs_to_session_keys(prefs: IntradayPrefs) -> dict[str, float | int]:
    return {
        "intraday_capital": int(prefs.capital),
        "intraday_allocation_pct": int(prefs.allocation_pct),
        "intraday_max_risk_pct": float(prefs.max_risk_pct),
        "intraday_max_trades": int(prefs.max_trades),
    }


def session_to_prefs(
    capital: float,
    allocation_pct: float,
    max_risk_pct: float,
    max_trades: int,
) -> IntradayPrefs:
    return IntradayPrefs(
        capital=float(capital),
        allocation_pct=float(allocation_pct),
        max_risk_pct=float(max_risk_pct),
        max_trades=int(max_trades),
    )
