import { getMarketOrderBlockReason } from "@/lib/broker/marketSession";
import { resolveSellTrim } from "@/lib/sellTrim";
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
  | { status: "PARTIAL_NOT_POSSIBLE"; stock: string; message: string }
  | { status: "INVALID_QUANTITY"; message: string }
  | { status: "ERROR"; message: string };

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

    const resolution = resolveSellTrim(holding.quantity, sellPercent);

    if (!resolution) {
      return {
        status: "INVALID_QUANTITY",
        message: "Could not resolve sell quantity for this holding",
      };
    }

    if (resolution.mode === "full_exit" && sellPercent < 100) {
      const shareLabel =
        holding.quantity === 1 ? "1 share" : `${holding.quantity} shares`;
      return {
        status: "PARTIAL_NOT_POSSIBLE",
        stock,
        message: `Cannot trim ${sellPercent}% with ${shareLabel}. Confirm a full-position sell (100%) or hold.`,
      };
    }

    const quantity = resolution.quantity;

    if (quantity < 1 || quantity > holding.quantity) {
      return {
        status: "INVALID_QUANTITY",
        message: "Could not resolve sell quantity for this holding",
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
      sellPercent: resolution.effectivePercent,
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
