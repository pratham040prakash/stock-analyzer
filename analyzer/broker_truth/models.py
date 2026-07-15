"""Canonical broker and planned trade models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ExecutionStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    OPEN = "OPEN"
    CANCELLED = "CANCELLED"
    MISSED = "MISSED"


@dataclass
class PlannedTrade:
    """Pre-trade plan — never overwritten by broker imports."""

    planned_id: str
    symbol: str
    exchange: str
    strategy: str
    trade_date: str
    planned_entry: float
    planned_stop: float
    planned_target: float
    planned_quantity: float | None
    side: str
    source: str
    created_at: str
    prep_score: float | None = None
    confidence_pct: float | None = None
    notes: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class TradeRecord:
    """Canonical completed trade from broker execution."""

    trade_id: str
    symbol: str
    exchange: str
    strategy: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    broker_charges: float
    realized_pnl: float
    holding_period_minutes: float | None
    order_ids: list[str]
    execution_status: str
    tags: list[str]
    notes: str
    product: str
    side: str
    trade_date: str
    planned_id: str | None
    source: str
    synced_at: str


@dataclass
class BrokerOrder:
    order_id: str
    exchange: str
    tradingsymbol: str
    product: str
    transaction_type: str
    quantity: float
    filled_quantity: float
    average_price: float | None
    status: str
    order_timestamp: str
    exchange_timestamp: str
    tag: str
    trade_date: str
    charges: float = 0.0


@dataclass
class BrokerTradeFill:
    trade_id: str
    order_id: str
    exchange: str
    tradingsymbol: str
    product: str
    transaction_type: str
    quantity: float
    average_price: float
    fill_timestamp: str
    trade_date: str


@dataclass
class BrokerPosition:
    tradingsymbol: str
    exchange: str
    product: str
    quantity: float
    average_price: float | None
    last_price: float | None
    pnl: float | None
    realised: float | None
    trade_date: str


@dataclass
class BrokerHolding:
    tradingsymbol: str
    exchange: str
    quantity: float
    average_price: float | None
    last_price: float | None
    pnl: float | None
    trade_date: str


@dataclass
class ReconciliationResult:
    planned_id: str
    trade_id: str | None
    symbol: str
    trade_date: str
    matched: bool
    slippage_entry: float | None
    slippage_exit: float | None
    execution_quality: str
    missed_entry: bool
    partial_fill: bool
    stop_adherence: str
    planned_entry: float
    actual_entry: float | None
    planned_stop: float
    actual_exit: float | None
    planned_target: float
    realized_pnl: float | None
    notes: str = ""
