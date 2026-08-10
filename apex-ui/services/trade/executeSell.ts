import { getMarketOrderBlockReason } from "@/lib/broker/marketSession";
import {
  fetchZerodhaHoldings,
  placeZerodhaOrder,
} from "@/services/brokers/zerodha";
import { listTradeAccessTokens } from "@/services/broker/tradeAccess";
import { normalizeSymbol } from "@/lib/stockPool";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type ExecuteSellInput = {
  stock: string;
  sellPercent: number;
};

export type ExecuteSellResult =
  | {
      status: "OK";
      stock: string;
      sellPercent: number;
      quantity: number;
      price: number;
      orderId: string;
    }
  | { status: "NOT_CONNECTED" }
  | { status: "TOKEN_EXPIRED" }
  | { status: "NO_HOLDING"; stock: string }
  | { status: "INVALID_QUANTITY"; message: string }
  | { status: "ERROR"; message: string };

function resolveSellQuantity(holdingQty: number, sellPercent: number): number {
  if (holdingQty < 1) {
    return 0;
  }

  const pct = Math.min(100, Math.max(1, Math.round(sellPercent)));
  return Math.max(1, Math.floor((holdingQty * pct) / 100));
}

export async function executeSellTrim(
  supabase: Client,
  userId: string,
  input: ExecuteSellInput,
): Promise<ExecuteSellResult> {
  const stock = normalizeSymbol(input.stock);
  const sellPercent = Math.round(input.sellPercent);

  if (!stock) {
    return { status: "ERROR", message: "Stock symbol is required" };
  }

  if (!Number.isFinite(sellPercent) || sellPercent < 1 || sellPercent > 100) {
    return { status: "ERROR", message: "sellPercent must be between 1 and 100" };
  }

  const marketBlock = getMarketOrderBlockReason();
  if (marketBlock) {
    return { status: "ERROR", message: marketBlock };
  }

  const candidates = await listTradeAccessTokens(supabase, userId);
  if (candidates.length === 0) {
    return { status: "NOT_CONNECTED" };
  }

  let sawExpired = false;
  let lastError = "Could not place sell order on Zerodha.";

  for (const candidate of candidates) {
    const holdings = await fetchZerodhaHoldings(candidate.accessToken);

    if (holdings.status === "TOKEN_EXPIRED") {
      sawExpired = true;
      continue;
    }

    if (holdings.status !== "OK") {
      lastError = holdings.message;
      continue;
    }

    const holding = holdings.data.find(
      (item) => normalizeSymbol(item.tradingsymbol) === stock,
    );

    if (!holding || holding.quantity < 1) {
      return { status: "NO_HOLDING", stock };
    }

    const quantity = resolveSellQuantity(holding.quantity, sellPercent);

    if (quantity < 1) {
      return {
        status: "INVALID_QUANTITY",
        message: `Cannot sell ${sellPercent}% — holding quantity too small`,
      };
    }

    const order = await placeZerodhaOrder(candidate.accessToken, {
      tradingsymbol: stock,
      transaction_type: "SELL",
      quantity,
      order_type: "MARKET",
      product: "CNC",
    });

    if (order.status === "TOKEN_EXPIRED") {
      sawExpired = true;
      continue;
    }

    if (order.status !== "OK") {
      lastError = order.message;
      continue;
    }

    return {
      status: "OK",
      stock,
      sellPercent,
      quantity,
      price: holding.last_price,
      orderId: order.orderId,
    };
  }

  if (sawExpired) {
    return { status: "TOKEN_EXPIRED" };
  }

  return { status: "ERROR", message: lastError };
}
