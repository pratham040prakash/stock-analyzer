"""Shared types for market data providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

DataSourceName = Literal["Kite", "Yahoo Finance", "NSE India"]


@dataclass
class IntradayMeta:
    symbol: str
    interval: str
    session_date: str
    bars: int
    source: DataSourceName
    market: dict = field(default_factory=dict)
    lag_note: str = ""
