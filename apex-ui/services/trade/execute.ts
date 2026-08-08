import { fetchStockData } from "@/services/market/stockData";
import {
  fetchZerodhaMargins,
  fetchZerodhaQuote,
  placeZerodhaOrder,
} from "@/services/brokers/zerodha";
import { getActiveBrokerConnection } from "@/services/broker/connections";
import { normalizeSymbol } from "@/lib/stockPool";
import { evaluateEntryTimingSafe } from "@/services/execution/entryTiming";
import { runRiskChecksSafe } from "@/services/risk/riskControl";
import type { MarketTrend } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type ExecuteTradeInput = {
  stock: string;
  amount: number;
  portfolioValue?: number;
  marketTrend?: MarketTrend;
};

export type ExecuteTradeResult =
  | {
      status: "OK";
      stock: string;
      amount: number;
      price: number;
      quantity: number;
      orderId: string;
    }
  | { status: "INSUFFICIENT_FUNDS"; availableCash: number; requested: number }
  | { status: "NOT_CONNECTED" }
  | { status: "TOKEN_EXPIRED" }
  | { status: "RISK_BLOCKED"; reason: string }
  | { status: "ENTRY_BLOCKED"; reason: string }
  | { status: "ERROR"; message: string };

async function resolveLatestPrice(
  accessToken: string,
  stock: string,
): Promise<number | null> {
  const quote = await fetchZerodhaQuote(accessToken, stock);
  if (quote.status === "OK") {
    return quote.lastPrice;
  }

  const data = await fetchStockData(stock);
  if (!data.prices.length) {
    return null;
  }

  return data.prices[data.prices.length - 1] ?? null;
}

export async function executeTrade(
  supabase: Client,
  userId: string,
  input: ExecuteTradeInput,
): Promise<ExecuteTradeResult> {
  const stock = normalizeSymbol(input.stock);
  const amount = Math.round(input.amount);

  if (!stock) {
    return { status: "ERROR", message: "Stock symbol is required" };
  }

  if (amount <= 0) {
    return { status: "ERROR", message: "Amount must be greater than zero" };
  }

  const risk = await runRiskChecksSafe(supabase, {
    userId,
    amount,
    portfolioValue: input.portfolioValue ?? 0,
    marketTrend: input.marketTrend,
  });

  if (!risk.allowed) {
    return {
      status: "RISK_BLOCKED",
      reason: risk.reason ?? "Trade blocked by risk controls",
    };
  }

  const connection = await getActiveBrokerConnection(supabase, userId);

  if (!connection?.accessToken || connection.status !== "active") {
    return { status: "NOT_CONNECTED" };
  }

  const margins = await fetchZerodhaMargins(connection.accessToken);

  if (margins.status === "TOKEN_EXPIRED") {
    return { status: "TOKEN_EXPIRED" };
  }

  if (margins.status !== "OK") {
    return { status: "ERROR", message: margins.message };
  }

  if (amount > margins.availableCash) {
    return {
      status: "INSUFFICIENT_FUNDS",
      availableCash: margins.availableCash,
      requested: amount,
    };
  }

  const price = await resolveLatestPrice(connection.accessToken, stock);

  if (!price || price <= 0) {
    return { status: "ERROR", message: "Unable to fetch latest price" };
  }

  const entryTiming = await evaluateEntryTimingSafe(stock, price);

  if (!entryTiming.enter) {
    return {
      status: "ENTRY_BLOCKED",
      reason: entryTiming.reason,
    };
  }

  const quantity = Math.floor(amount / price);

  if (quantity < 1) {
    return {
      status: "ERROR",
      message: `Amount too small for 1 share at ${price.toFixed(2)}`,
    };
  }

  const order = await placeZerodhaOrder(connection.accessToken, {
    tradingsymbol: stock,
    transaction_type: "BUY",
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
    amount: quantity * price,
    price,
    quantity,
    orderId: order.orderId,
  };
}

export async function executeTradeSafe(
  supabase: Client,
  userId: string,
  input: ExecuteTradeInput,
): Promise<ExecuteTradeResult | null> {
  try {
    return await executeTrade(supabase, userId, input);
  } catch (error) {
    console.error("Trade execution failed:", error);
    return null;
  }
}
