"""Import executed trades from Zerodha Kite — broker truth source."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.broker_truth.models import (
    BrokerHolding,
    BrokerOrder,
    BrokerPosition,
    BrokerTradeFill,
    ExecutionStatus,
    TradeRecord,
)
from analyzer.broker_truth.store import (
    fetch_fills_for_date,
    fetch_order_charges_for_date,
    fetch_trade_records,
    log_sync_run,
    replace_trade_records_for_date,
    upsert_fills,
    upsert_holdings,
    upsert_orders,
    upsert_positions,
)
from analyzer.broker_truth.symbols import normalize_equity_symbol
from analyzer.structured_log import log_event
from analyzer.zerodha import kite_to_yahoo

IST = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)


def _parse_trade_date(ts: str, fallback: str) -> str:
    if not ts:
        return fallback
    try:
        if "T" in ts:
            return ts.split("T")[0]
        return ts.split(" ")[0]
    except Exception:
        return fallback


def _parse_dt(ts: str) -> datetime | None:
    if not ts:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            return datetime.strptime(ts.replace("+0530", "+05:30"), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


@dataclass
class BrokerSyncResult:
    trade_date: str
    orders_imported: int = 0
    fills_imported: int = 0
    positions_imported: int = 0
    holdings_imported: int = 0
    records_built: int = 0
    errors: list[str] = field(default_factory=list)
    connected: bool = False


class BrokerTruthService:
    """Single source of truth for completed broker executions."""

    def __init__(self, kite=None):
        self._kite = kite

    def _client(self):
        if self._kite is not None:
            return self._kite
        from analyzer.zerodha import get_kite_client

        return get_kite_client()

    def sync_session(self, trade_date: str | None = None) -> BrokerSyncResult:
        """Import orders, fills, positions, holdings; build TradeRecords."""
        trade_date = trade_date or datetime.now(IST).strftime("%Y-%m-%d")
        result = BrokerSyncResult(trade_date=trade_date)
        kite = self._client()
        if kite is None:
            msg = "Kite not connected — broker truth sync skipped"
            result.errors.append(msg)
            logger.info(msg)
            log_event("broker_truth_sync_skipped", trade_date=trade_date, reason="not_connected")
            log_sync_run(
                trade_date=trade_date,
                orders_count=0,
                fills_count=0,
                records_count=0,
                status="skipped",
                error="not_connected",
            )
            return result

        result.connected = True
        for step_name, step_fn in (
            ("orders", lambda: self._import_orders(kite, trade_date)),
            ("trades", lambda: self._import_trades(kite, trade_date)),
            ("positions", lambda: self._import_positions(kite, trade_date)),
            ("holdings", lambda: self._import_holdings(kite, trade_date)),
        ):
            try:
                count = step_fn()
                if step_name == "orders":
                    result.orders_imported = count
                elif step_name == "trades":
                    result.fills_imported = count
                elif step_name == "positions":
                    result.positions_imported = count
                else:
                    result.holdings_imported = count
            except Exception as exc:
                err = f"{step_name}: {exc}"
                result.errors.append(err)
                logger.warning("broker_truth import failed: %s", err)

        try:
            records = self.build_trade_records(trade_date)
            result.records_built = replace_trade_records_for_date(trade_date, records)
            status = "ok" if not result.errors else "partial"
            log_event(
                "broker_truth_sync",
                trade_date=trade_date,
                status=status,
                orders=result.orders_imported,
                fills=result.fills_imported,
                records=result.records_built,
                errors=len(result.errors),
            )
            log_sync_run(
                trade_date=trade_date,
                orders_count=result.orders_imported,
                fills_count=result.fills_imported,
                records_count=result.records_built,
                status=status,
                error="; ".join(result.errors)[:500],
            )
        except Exception as exc:
            err = str(exc)
            result.errors.append(err)
            logger.exception("broker_truth record build failed for %s", trade_date)
            log_event("broker_truth_sync_error", trade_date=trade_date, error=err)
            log_sync_run(
                trade_date=trade_date,
                orders_count=result.orders_imported,
                fills_count=result.fills_imported,
                records_count=result.records_built,
                status="error",
                error=err,
            )
        return result

    def _import_orders(self, kite, trade_date: str) -> int:
        orders: list[BrokerOrder] = []
        for row in kite.orders() or []:
            order_id = str(row.get("order_id") or "").strip()
            if not order_id:
                continue
            order_ts = str(row.get("order_timestamp") or row.get("exchange_timestamp") or "")
            od = _parse_trade_date(order_ts, trade_date)
            if od != trade_date:
                continue
            orders.append(
                BrokerOrder(
                    order_id=order_id,
                    exchange=str(row.get("exchange") or "NSE"),
                    tradingsymbol=str(row.get("tradingsymbol") or ""),
                    product=str(row.get("product") or ""),
                    transaction_type=str(row.get("transaction_type") or ""),
                    quantity=_safe_float(row.get("quantity")),
                    filled_quantity=_safe_float(row.get("filled_quantity")),
                    average_price=_safe_float(row["average_price"]) if row.get("average_price") else None,
                    status=str(row.get("status") or ""),
                    order_timestamp=order_ts,
                    exchange_timestamp=str(row.get("exchange_timestamp") or ""),
                    tag=str(row.get("tag") or ""),
                    trade_date=od,
                    charges=_safe_float(row.get("charges") or row.get("brokerage")),
                )
            )
        return upsert_orders(orders)

    def _import_trades(self, kite, trade_date: str) -> int:
        fills: list[BrokerTradeFill] = []
        for row in kite.trades() or []:
            trade_id = str(row.get("trade_id") or "").strip()
            if not trade_id:
                continue
            qty = _safe_float(row.get("quantity"))
            if qty <= 0:
                continue
            fill_ts = str(row.get("fill_timestamp") or row.get("order_timestamp") or "")
            fd = _parse_trade_date(fill_ts, trade_date)
            if fd != trade_date:
                continue
            fills.append(
                BrokerTradeFill(
                    trade_id=trade_id,
                    order_id=str(row.get("order_id") or ""),
                    exchange=str(row.get("exchange") or "NSE"),
                    tradingsymbol=str(row.get("tradingsymbol") or ""),
                    product=str(row.get("product") or ""),
                    transaction_type=str(row.get("transaction_type") or "").upper(),
                    quantity=qty,
                    average_price=_safe_float(row.get("average_price")),
                    fill_timestamp=fill_ts,
                    trade_date=fd,
                )
            )
        return upsert_fills(fills)

    def _import_positions(self, kite, trade_date: str) -> int:
        positions: list[BrokerPosition] = []
        raw = kite.positions()
        for bucket in ("net", "day"):
            for row in raw.get(bucket) or []:
                positions.append(
                    BrokerPosition(
                        tradingsymbol=str(row.get("tradingsymbol") or ""),
                        exchange=str(row.get("exchange") or "NSE"),
                        product=str(row.get("product") or ""),
                        quantity=_safe_float(row.get("quantity")),
                        average_price=_safe_float(row["average_price"])
                        if row.get("average_price")
                        else None,
                        last_price=_safe_float(row["last_price"]) if row.get("last_price") else None,
                        pnl=_safe_float(row["pnl"]) if row.get("pnl") is not None else None,
                        realised=_safe_float(row["realised"]) if row.get("realised") is not None else None,
                        trade_date=trade_date,
                    )
                )
        return upsert_positions(positions)

    def _import_holdings(self, kite, trade_date: str) -> int:
        holdings: list[BrokerHolding] = []
        for row in kite.holdings() or []:
            qty = _safe_float(row.get("quantity")) + _safe_float(row.get("t1_quantity"))
            if qty <= 0:
                continue
            holdings.append(
                BrokerHolding(
                    tradingsymbol=str(row.get("tradingsymbol") or ""),
                    exchange=str(row.get("exchange") or "NSE"),
                    quantity=qty,
                    average_price=_safe_float(row["average_price"])
                    if row.get("average_price")
                    else None,
                    last_price=_safe_float(row["last_price"]) if row.get("last_price") else None,
                    pnl=_safe_float(row["pnl"]) if row.get("pnl") is not None else None,
                    trade_date=trade_date,
                )
            )
        return upsert_holdings(holdings)

    def build_trade_records(self, trade_date: str) -> list[TradeRecord]:
        """Pair buy/sell fills into completed TradeRecords (FIFO per symbol+product)."""
        fills = fetch_fills_for_date(trade_date)
        if not fills:
            return []

        charges_map = fetch_order_charges_for_date(trade_date)
        synced_at = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %z")
        records: list[TradeRecord] = []
        groups: dict[tuple[str, str], list[BrokerTradeFill]] = {}
        for f in fills:
            key = (f.tradingsymbol.upper(), f.product.upper())
            groups.setdefault(key, []).append(f)

        for (tsym, product), legs in groups.items():
            legs_sorted = sorted(legs, key=lambda x: x.fill_timestamp)
            long_lots: list[dict] = []
            short_lots: list[dict] = []
            seq = 0

            for leg in legs_sorted:
                txn = leg.transaction_type.upper()
                if txn == "BUY":
                    remaining = leg.quantity
                    while remaining > 0 and short_lots:
                        lot = short_lots[0]
                        matched = min(remaining, lot["qty"])
                        seq += 1
                        records.append(
                            _make_record(
                                trade_date=trade_date,
                                symbol=normalize_equity_symbol(tsym),
                                exchange=leg.exchange,
                                product=product,
                                side="SHORT",
                                entry_price=lot["price"],
                                exit_price=leg.average_price,
                                quantity=matched,
                                entry_time=lot["time"],
                                exit_time=leg.fill_timestamp,
                                order_ids=[lot["order_id"], leg.order_id],
                                seq=seq,
                                synced_at=synced_at,
                                charges_map=charges_map,
                            )
                        )
                        lot["qty"] -= matched
                        remaining -= matched
                        if lot["qty"] <= 0:
                            short_lots.pop(0)
                    if remaining > 0:
                        long_lots.append({
                            "qty": remaining,
                            "price": leg.average_price,
                            "time": leg.fill_timestamp,
                            "order_id": leg.order_id,
                        })
                elif txn == "SELL":
                    remaining = leg.quantity
                    while remaining > 0 and long_lots:
                        lot = long_lots[0]
                        matched = min(remaining, lot["qty"])
                        seq += 1
                        records.append(
                            _make_record(
                                trade_date=trade_date,
                                symbol=normalize_equity_symbol(tsym),
                                exchange=leg.exchange,
                                product=product,
                                side="LONG",
                                entry_price=lot["price"],
                                exit_price=leg.average_price,
                                quantity=matched,
                                entry_time=lot["time"],
                                exit_time=leg.fill_timestamp,
                                order_ids=[lot["order_id"], leg.order_id],
                                seq=seq,
                                synced_at=synced_at,
                                charges_map=charges_map,
                            )
                        )
                        lot["qty"] -= matched
                        remaining -= matched
                        if lot["qty"] <= 0:
                            long_lots.pop(0)
                    if remaining > 0:
                        short_lots.append({
                            "qty": remaining,
                            "price": leg.average_price,
                            "time": leg.fill_timestamp,
                            "order_id": leg.order_id,
                        })

        return records

    def get_completed_trades(
        self,
        *,
        trade_date: str | None = None,
        symbol: str | None = None,
        limit: int = 200,
    ) -> list[TradeRecord]:
        return fetch_trade_records(trade_date=trade_date, symbol=symbol, limit=limit)

    def yahoo_symbol(self, tradingsymbol: str, exchange: str = "NSE") -> str:
        return kite_to_yahoo(f"{exchange}:{tradingsymbol}")


def _make_record(
    *,
    trade_date: str,
    symbol: str,
    exchange: str,
    product: str,
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    entry_time: str,
    exit_time: str,
    order_ids: list[str],
    seq: int,
    synced_at: str,
    charges_map: dict[str, float],
) -> TradeRecord:
    if side == "LONG":
        gross = (exit_price - entry_price) * quantity
    else:
        gross = (entry_price - exit_price) * quantity

    charges = sum(charges_map.get(oid, 0.0) for oid in order_ids if oid)
    net_pnl = gross - charges

    entry_dt = _parse_dt(entry_time)
    exit_dt = _parse_dt(exit_time)
    holding = None
    if entry_dt and exit_dt:
        holding = round((exit_dt - entry_dt).total_seconds() / 60.0, 2)

    trade_id = f"{trade_date}:{symbol}:{product}:{side}:{seq}"
    strategy = "MIS" if product.upper() == "MIS" else product.upper()

    return TradeRecord(
        trade_id=trade_id,
        symbol=symbol,
        exchange=exchange,
        strategy=strategy,
        entry_time=entry_time,
        exit_time=exit_time,
        entry_price=round(entry_price, 4),
        exit_price=round(exit_price, 4),
        quantity=quantity,
        broker_charges=round(charges, 2),
        realized_pnl=round(net_pnl, 2),
        holding_period_minutes=holding,
        order_ids=[oid for oid in order_ids if oid],
        execution_status=ExecutionStatus.COMPLETE.value,
        tags=[product.upper()],
        notes="",
        product=product.upper(),
        side=side,
        trade_date=trade_date,
        planned_id=None,
        source="kite_api",
        synced_at=synced_at,
    )
