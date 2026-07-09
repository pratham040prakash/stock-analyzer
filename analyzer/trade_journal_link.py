"""Queue a Track Record lesson from a logged intraday trade."""

from __future__ import annotations

from typing import Any

from analyzer.intraday_journal import IntradayTradeLog


def build_lesson_prefill(trade: IntradayTradeLog) -> dict[str, Any]:
    return {
        "symbol": f"{trade.symbol} {trade.action}",
        "leg": "equity",
        "entry": trade.entry,
        "exit": trade.price_at_log,
        "pnl_inr": None,
        "mistake": trade.notes or "",
        "fix": "",
    }
