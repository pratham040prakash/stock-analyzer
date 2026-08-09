import {
  fetchZerodhaHoldings,
  placeZerodhaOrder,
} from "@/services/brokers/zerodha";
import { getActiveBrokerConnection } from "@/services/broker/connections";
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

  const connection = await getActiveBrokerConnection(supabase, userId);

  if (!connection?.accessToken || connection.status !== "active") {
    return { status: "NOT_CONNECTED" };
  }

  const holdings = await fetchZerodhaHoldings(connection.accessToken);

  if (holdings.status === "TOKEN_EXPIRED") {
    return { status: "TOKEN_EXPIRED" };
  }

  if (holdings.status !== "OK") {
    return { status: "ERROR", message: holdings.message };
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

  const order = await placeZerodhaOrder(connection.accessToken, {
    tradingsymbol: stock,
    transaction_type: "SELL",
    quantity,
    order_type: "MARKET",
    product: "CNC",
  });

  if (order.status === "TOKEN_EXPIRED") {
    return { status: "TOKEN_EXPIRED" };
  }

  if (order.status !== "OK") {
    return { status: "ERROR", message: order.message };
  }

  return {
    status: "OK",
    stock,
    sellPercent,
    quantity,
    orderId: order.orderId,
  };
}
