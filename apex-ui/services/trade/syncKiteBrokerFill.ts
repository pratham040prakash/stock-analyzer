import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { normalizeSymbol } from "@/lib/stockPool";
import { listTradeAccessTokens } from "@/services/broker/tradeAccess";
import {
  fetchZerodhaTrades,
  type KiteTrade,
} from "@/services/brokers/zerodha";
import { syncUserPortfolio } from "@/services/portfolio/sync";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";
import {
  getBrokerFillToday,
  logTradeFillSafe,
  type BrokerFillToday,
  type TradeFillInput,
} from "@/services/trade/logTradeFill";

type Client = SupabaseClient<Database>;

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

function pickLatestTradeFill(
  trades: KiteTrade[],
  stock: string,
  dateKey: string,
): TradeFillInput | null {
  const normalized = normalizeSymbol(stock);
  if (!normalized) {
    return null;
  }

  const todays = trades.filter((trade) => {
    if (normalizeSymbol(trade.tradingsymbol) !== normalized) {
      return false;
    }

    const fillDate = tradeFillDateKey(trade.fill_timestamp);
    return fillDate === dateKey;
  });

  if (todays.length === 0) {
    return null;
  }

  const byOrder = new Map<string, KiteTrade[]>();

  for (const trade of todays) {
    const orderId = String(trade.order_id);
    const bucket = byOrder.get(orderId) ?? [];
    bucket.push(trade);
    byOrder.set(orderId, bucket);
  }

  let latest: ReturnType<typeof aggregateTrades> = null;
  let latestTimestamp = "";

  for (const orderTrades of byOrder.values()) {
    const aggregated = aggregateTrades(orderTrades);
    if (!aggregated) {
      continue;
    }

    const timestamp = orderTrades
      .map((trade) => trade.fill_timestamp)
      .sort()
      .at(-1);

    if (!timestamp || timestamp < latestTimestamp) {
      continue;
    }

    latestTimestamp = timestamp;
    latest = aggregated;
  }

  if (!latest) {
    return null;
  }

  return {
    stock: normalized,
    side: latest.side,
    price: latest.price,
    quantity: latest.quantity,
    amount: Math.round(latest.price * latest.quantity),
    orderId: latest.orderId,
  };
}

export async function syncBrokerFillFromKiteTrades(
  supabase: Client,
  userId: string,
  stock: string,
  dateKey = tradingDateKey(),
): Promise<BrokerFillToday> {
  const existing = await getBrokerFillToday(supabase, userId, stock, dateKey);
  if (existing.filled) {
    return existing;
  }

  const candidates = await listTradeAccessTokens(supabase, userId);
  if (candidates.length === 0) {
    return { filled: false };
  }

  for (const candidate of candidates) {
    const tradesResult = await fetchZerodhaTrades(candidate.accessToken);

    if (tradesResult.status === "TOKEN_EXPIRED") {
      continue;
    }

    if (tradesResult.status !== "OK") {
      continue;
    }

    const fillInput = pickLatestTradeFill(tradesResult.data, stock, dateKey);
    if (!fillInput) {
      continue;
    }

    await logTradeFillSafe(supabase, userId, fillInput);

    try {
      await syncUserPortfolio(supabase, userId);
    } catch (error) {
      console.error("Portfolio sync after Kite fill import failed:", error);
    }

    return {
      filled: true,
      orderId: fillInput.orderId,
      quantity: fillInput.quantity,
      side: fillInput.side,
      price: fillInput.price,
    };
  }

  return { filled: false };
}

export function runSyncKiteBrokerFillSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Sync Kite broker fill self-check failed: ${message}`);
    }
  };

  const dateKey = "2026-08-10";
  const fill = pickLatestTradeFill(
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
    ],
    "JIOFIN",
    dateKey,
  );

  assert(fill !== null, "Must detect today's Kite sell trades");
  assert(fill?.quantity === 5, "Must aggregate partial fills on one order");
  assert(fill?.side === "sell", "Must preserve sell side");
  assert(
    pickLatestTradeFill(
      [
        {
          trade_id: "3",
          order_id: "222",
          tradingsymbol: "JIOFIN",
          transaction_type: "SELL",
          quantity: 1,
          average_price: 300,
          fill_timestamp: "2026-08-09 15:00:00",
        },
      ],
      "JIOFIN",
      dateKey,
    ) === null,
    "Must ignore trades from other sessions",
  );
}
