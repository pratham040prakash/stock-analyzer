"""Compare planned trades vs broker-executed trades."""

from __future__ import annotations

import logging

from analyzer.broker_truth.models import PlannedTrade, ReconciliationResult, TradeRecord
from analyzer.broker_truth.planned import load_planned_trades
from analyzer.broker_truth.store import fetch_reconciliation_for_date, fetch_trade_records, save_reconciliation_results
from analyzer.broker_truth.service import BrokerTruthService
from analyzer.broker_truth.symbols import normalize_equity_symbol
from analyzer.structured_log import log_event
from analyzer.watchlist_pins import infer_trade_side

logger = logging.getLogger(__name__)


class ReconciliationService:
    """Planned vs executed — slippage, adherence, missed entries."""

    def __init__(self, broker: BrokerTruthService | None = None):
        self._broker = broker or BrokerTruthService()

    def reconcile_one(
        self,
        planned: PlannedTrade,
        executed: TradeRecord | None,
    ) -> ReconciliationResult:
        if executed is None:
            return ReconciliationResult(
                planned_id=planned.planned_id,
                trade_id=None,
                symbol=planned.symbol,
                trade_date=planned.trade_date,
                matched=False,
                slippage_entry=None,
                slippage_exit=None,
                execution_quality="missed",
                missed_entry=True,
                partial_fill=False,
                stop_adherence="not_applicable",
                planned_entry=planned.planned_entry,
                actual_entry=None,
                planned_stop=planned.planned_stop,
                actual_exit=None,
                planned_target=planned.planned_target,
                realized_pnl=None,
                notes="No broker execution matched this plan.",
            )

        side = infer_trade_side(planned.planned_entry, planned.planned_stop, explicit=planned.side)
        entry_slip = executed.entry_price - planned.planned_entry
        if side == "SHORT":
            entry_slip = planned.planned_entry - executed.entry_price

        exit_slip = None
        if executed.exit_price:
            exit_slip = executed.exit_price - planned.planned_target
            if side == "SHORT":
                exit_slip = planned.planned_target - executed.exit_price

        stop_adherence = _stop_adherence(
            side=side,
            planned_stop=planned.planned_stop,
            actual_exit=executed.exit_price,
            realized_pnl=executed.realized_pnl,
        )
        partial = executed.execution_status == "PARTIAL"
        quality = _execution_quality(entry_slip, stop_adherence, executed.realized_pnl)

        return ReconciliationResult(
            planned_id=planned.planned_id,
            trade_id=executed.trade_id,
            symbol=planned.symbol,
            trade_date=planned.trade_date,
            matched=True,
            slippage_entry=round(entry_slip, 4),
            slippage_exit=round(exit_slip, 4) if exit_slip is not None else None,
            execution_quality=quality,
            missed_entry=False,
            partial_fill=partial,
            stop_adherence=stop_adherence,
            planned_entry=planned.planned_entry,
            actual_entry=executed.entry_price,
            planned_stop=planned.planned_stop,
            actual_exit=executed.exit_price,
            planned_target=planned.planned_target,
            realized_pnl=executed.realized_pnl,
            notes="",
        )

    def reconcile_session(self, trade_date: str) -> list[ReconciliationResult]:
        planned_list = load_planned_trades(trade_date)
        executed_list = fetch_trade_records(trade_date=trade_date)
        results: list[ReconciliationResult] = []
        used_trades: set[str] = set()

        for planned in planned_list:
            match = _best_match(planned, executed_list, used_trades)
            if match:
                used_trades.add(match.trade_id)
            results.append(self.reconcile_one(planned, match))

        save_reconciliation_results(results)
        matched = sum(1 for r in results if r.matched)
        log_event(
            "broker_truth_reconcile",
            trade_date=trade_date,
            planned=len(planned_list),
            executed=len(executed_list),
            matched=matched,
        )
        return results

    def run_full_reconciliation(self, trade_date: str) -> list[ReconciliationResult]:
        self._broker.sync_session(trade_date)
        return self.reconcile_session(trade_date)

    def get_saved_reconciliation(self, trade_date: str) -> list[ReconciliationResult]:
        return fetch_reconciliation_for_date(trade_date)


def _best_match(
    planned: PlannedTrade,
    executed: list[TradeRecord],
    used: set[str],
) -> TradeRecord | None:
    sym = normalize_equity_symbol(planned.symbol)
    candidates = [
        t for t in executed
        if normalize_equity_symbol(t.symbol) == sym and t.trade_id not in used
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda t: abs(t.entry_price - planned.planned_entry))


def _stop_adherence(
    *,
    side: str,
    planned_stop: float,
    actual_exit: float,
    realized_pnl: float,
) -> str:
    if side == "LONG":
        if actual_exit <= planned_stop and realized_pnl < 0:
            return "stop_hit"
        if actual_exit > planned_stop and realized_pnl < 0:
            return "worse_than_stop"
        if realized_pnl >= 0:
            return "held_or_profit"
        return "unknown"
    if actual_exit >= planned_stop and realized_pnl < 0:
        return "stop_hit"
    if actual_exit < planned_stop and realized_pnl < 0:
        return "worse_than_stop"
    if realized_pnl >= 0:
        return "held_or_profit"
    return "unknown"


def _execution_quality(entry_slip: float, stop_adherence: str, pnl: float) -> str:
    if abs(entry_slip) > 2.0:
        return "poor_entry_slippage"
    if stop_adherence == "worse_than_stop":
        return "poor_stop_discipline"
    if pnl > 0:
        return "good"
    if pnl == 0:
        return "flat"
    return "loss_controlled" if stop_adherence == "stop_hit" else "loss"
