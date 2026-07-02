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

PREFS_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "prefs.json"

DEFAULT_CAPITAL_INR = 50_000.0


@dataclass
class IntradayPrefs:
    capital: float = DEFAULT_CAPITAL_INR
    allocation_pct: float = DEFAULT_INTRADAY_ALLOCATION_PCT
    max_risk_pct: float = DEFAULT_MAX_RISK_PCT
    max_trades: int = DEFAULT_MAX_CONCURRENT_TRADES


def _ensure_dir() -> None:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_intraday_prefs() -> IntradayPrefs:
    _ensure_dir()
    if not PREFS_PATH.exists():
        return IntradayPrefs()
    try:
        raw = json.loads(PREFS_PATH.read_text(encoding="utf-8"))
        return IntradayPrefs(
            capital=float(raw.get("capital", DEFAULT_CAPITAL_INR)),
            allocation_pct=float(raw.get("allocation_pct", DEFAULT_INTRADAY_ALLOCATION_PCT)),
            max_risk_pct=float(raw.get("max_risk_pct", DEFAULT_MAX_RISK_PCT)),
            max_trades=int(raw.get("max_trades", DEFAULT_MAX_CONCURRENT_TRADES)),
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
