"""Home — Investment Operating System dashboard."""

from __future__ import annotations

from ui.components.home_dashboard import render_home_dashboard


def render_unified_hub(market: str, *, period: str = "1y", max_trades: int = 1) -> None:
    render_home_dashboard(market, period=period, max_trades=max_trades)
