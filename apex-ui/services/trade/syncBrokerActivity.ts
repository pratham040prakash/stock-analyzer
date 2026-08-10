import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { normalizeSymbol } from "@/lib/stockPool";
import { listTradeAccessTokens } from "@/services/broker/tradeAccess";
import {
  fetchZerodhaOrders,
  fetchZerodhaTrades,
  type KiteOrder,
  type KiteTrade,
} from "@/services/brokers/zerodha";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";
import {
  getLoggedBrokerOrderIdsToday,
  logTradeFillSafe,
  type TradeFillInput,
} from "@/services/trade/logTradeFill";

type Client = SupabaseClient<Database>;

export type BrokerActivitySyncResult =
  | {
      status: "OK";
      imported: number;
      skipped: number;
      symbols: string[];
      tradesSeen: number;
      ordersSeen: number;
      openOrders: number;
    }
  | { status: "NOT_CONNECTED" }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

function tradeFillDateKey(fillTimestamp: string): string | null {
  const trimmed = fillTimestamp.trim();
  if (trimmed.length < 10) {
    return null;
  }

  return trimmed.slice(0, 10);
}

function aggregateTrades(trades: KiteTrade[]): {
  orderId: string;
  quantity: number;
  price: number;
  side: "buy" | "sell";
} | null {
  if (trades.length === 0) {
    return null;
  }

  const side =
    trades[0].transaction_type === "SELL"
      ? "sell"
      : trades[0].transaction_type === "BUY"
        ? "buy"
        : null;

  if (!side) {
    return null;
  }

  let totalQty = 0;
  let totalValue = 0;

  for (const trade of trades) {
    if (
      trade.transaction_type !== trades[0].transaction_type ||
      !Number.isFinite(trade.quantity) ||
      trade.quantity <= 0 ||
      !Number.isFinite(trade.average_price) ||
      trade.average_price <= 0
    ) {
      continue;
    }

    totalQty += trade.quantity;
    totalValue += trade.quantity * trade.average_price;
  }

  if (totalQty <= 0) {
    return null;
  }

  return {
    orderId: String(trades[0].order_id),
    quantity: totalQty,
    price: totalValue / totalQty,
    side,
  };
}

/** All executed Kite trades for the session, grouped by order id. */
export function listTodayTradeFills(
  trades: KiteTrade[],
  dateKey: string,
): TradeFillInput[] {
  const todays = trades.filter((trade) => {
    const fillDate = tradeFillDateKey(trade.fill_timestamp);
    return fillDate === dateKey;
  });

  const byOrder = new Map<string, KiteTrade[]>();

  for (const trade of todays) {
    const orderId = String(trade.order_id);
    const bucket = byOrder.get(orderId) ?? [];
    bucket.push(trade);
    byOrder.set(orderId, bucket);
  }

  const fills: TradeFillInput[] = [];

  for (const orderTrades of byOrder.values()) {
    const aggregated = aggregateTrades(orderTrades);
    const symbol = normalizeSymbol(orderTrades[0]?.tradingsymbol ?? "");

    if (!aggregated || !symbol) {
      continue;
    }

    fills.push({
      stock: symbol,
      side: aggregated.side,
      price: aggregated.price,
      quantity: aggregated.quantity,
      amount: Math.round(aggregated.price * aggregated.quantity),
      orderId: aggregated.orderId,
    });
  }

  return fills.sort((left, right) => left.orderId.localeCompare(right.orderId));
}

function countOpenOrders(orders: KiteOrder[]): number {
  const openStatuses = new Set([
    "OPEN",
    "TRIGGER PENDING",
    "AMO REQ RECEIVED",
    "VALIDATION PENDING",
    "PUT ORDER REQ RECEIVED",
  ]);

  return orders.filter((order) => openStatuses.has(order.status)).length;
}

export async function syncBrokerActivityFromKite(
  supabase: Client,
  userId: string,
  dateKey = tradingDateKey(),
): Promise<BrokerActivitySyncResult> {
  const candidates = await listTradeAccessTokens(supabase, userId);
  if (candidates.length === 0) {
    return { status: "NOT_CONNECTED" };
  }

  const loggedOrderIds = await getLoggedBrokerOrderIdsToday(
    supabase,
    userId,
    dateKey,
  );

  for (const candidate of candidates) {
    const [tradesResult, ordersResult] = await Promise.all([
      fetchZerodhaTrades(candidate.accessToken),
      fetchZerodhaOrders(candidate.accessToken),
    ]);

    if (
      tradesResult.status === "TOKEN_EXPIRED" ||
      ordersResult.status === "TOKEN_EXPIRED"
    ) {
      continue;
    }

    if (tradesResult.status !== "OK") {
      return { status: "ERROR", message: tradesResult.message };
    }

    if (ordersResult.status !== "OK") {
      return { status: "ERROR", message: ordersResult.message };
    }

    const fills = listTodayTradeFills(tradesResult.data, dateKey);
    const symbols = new Set<string>();
    let imported = 0;
    let skipped = 0;

    for (const fill of fills) {
      if (loggedOrderIds.has(fill.orderId)) {
        skipped += 1;
        continue;
      }

      const loggedId = await logTradeFillSafe(supabase, userId, fill);
      if (!loggedId) {
        continue;
      }

      loggedOrderIds.add(fill.orderId);
      symbols.add(fill.stock);
      imported += 1;
    }

    return {
      status: "OK",
      imported,
      skipped,
      symbols: [...symbols].sort(),
      tradesSeen: fills.length,
      ordersSeen: ordersResult.data.length,
      openOrders: countOpenOrders(ordersResult.data),
    };
  }

  return { status: "TOKEN_EXPIRED" };
}

export function runSyncBrokerActivitySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Sync broker activity self-check failed: ${message}`);
    }
  };

  const dateKey = "2026-08-10";
  const fills = listTodayTradeFills(
    [
      {
        trade_id: "1",
        order_id: "111",
        tradingsymbol: "JIOFIN",
        transaction_type: "SELL",
        quantity: 3,
        average_price: 300,
        fill_timestamp: "2026-08-10 09:30:00",
      },
      {
        trade_id: "2",
        order_id: "111",
        tradingsymbol: "JIOFIN",
        transaction_type: "SELL",
        quantity: 2,
        average_price: 310,
        fill_timestamp: "2026-08-10 09:30:01",
      },
      {
        trade_id: "3",
        order_id: "222",
        tradingsymbol: "RELIANCE",
        transaction_type: "BUY",
        quantity: 1,
        average_price: 2500,
        fill_timestamp: "2026-08-10 10:00:00",
      },
    ],
    dateKey,
  );

  assert(fills.length === 2, "Must emit one fill per order id");
  assert(
    fills.find((fill) => fill.stock === "JIOFIN")?.quantity === 5,
    "Must aggregate partial fills on one order",
  );
  assert(
    fills.some((fill) => fill.stock === "RELIANCE" && fill.side === "buy"),
    "Must include all symbols traded today",
  );
  assert(
    listTodayTradeFills(
      [
        {
          trade_id: "4",
          order_id: "333",
          tradingsymbol: "JIOFIN",
          transaction_type: "SELL",
          quantity: 1,
          average_price: 300,
          fill_timestamp: "2026-08-09 15:00:00",
        },
      ],
      dateKey,
    ).length === 0,
    "Must ignore trades from other sessions",
  );
  assert(
    countOpenOrders([
      {
        order_id: "1",
        tradingsymbol: "JIOFIN",
        transaction_type: "SELL",
        status: "OPEN",
        quantity: 1,
        filled_quantity: 0,
        average_price: 0,
        order_timestamp: "2026-08-10 09:00:00",
      },
      {
        order_id: "2",
        tradingsymbol: "JIOFIN",
        transaction_type: "SELL",
        status: "COMPLETE",
        quantity: 1,
        filled_quantity: 1,
        average_price: 300,
        order_timestamp: "2026-08-10 09:30:00",
      },
    ]) === 1,
    "Must count only open Kite orders",
  );
}
