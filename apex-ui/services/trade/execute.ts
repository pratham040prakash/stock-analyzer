import { getMarketOrderBlockReason } from "@/lib/broker/marketSession";
import { fetchStockData } from "@/services/market/stockData";
import {
  fetchZerodhaMargins,
  fetchZerodhaQuote,
  placeZerodhaOrder,
} from "@/services/brokers/zerodha";
import { listTradeAccessTokens } from "@/services/broker/tradeAccess";
import { normalizeSymbol } from "@/lib/stockPool";
import { logger } from "@/lib/logging/logger";
import { evaluateEntryTimingSafe } from "@/services/execution/entryTiming";
import { computeStopLoss, runRiskChecksSafe } from "@/services/risk/riskControl";
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
      stopLoss?: number;
      stopLossOrderId?: string;
      stopLossNote?: string;
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

  const marketBlock = getMarketOrderBlockReason();
  if (marketBlock) {
    return { status: "ERROR", message: marketBlock };
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

  const connection = await listTradeAccessTokens(supabase, userId);

  if (connection.length === 0) {
    return { status: "NOT_CONNECTED" };
  }

  let sawExpired = false;
  let lastError = "Could not place buy order on Zerodha.";

  for (const candidate of connection) {
    const margins = await fetchZerodhaMargins(candidate.accessToken);

    if (margins.status === "TOKEN_EXPIRED") {
      sawExpired = true;
      continue;
    }

    if (margins.status !== "OK") {
      lastError = margins.message;
      continue;
    }

    if (amount > margins.marginAvailable) {
      return {
        status: "INSUFFICIENT_FUNDS",
        availableCash: margins.marginAvailable,
        requested: amount,
      };
    }

    const price = await resolveLatestPrice(candidate.accessToken, stock);

    if (!price || price <= 0) {
      lastError = "Unable to fetch latest price";
      continue;
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

    const order = await placeZerodhaOrder(candidate.accessToken, {
      tradingsymbol: stock,
      transaction_type: "BUY",
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

    const stopLoss = computeStopLoss(price);
    const triggerPrice = Math.round(stopLoss * 100) / 100;
    const limitPrice = Math.max(0.05, Math.round(triggerPrice * 0.995 * 100) / 100);

    const stopOrder = await placeZerodhaOrder(candidate.accessToken, {
      tradingsymbol: stock,
      transaction_type: "SELL",
      quantity,
      order_type: "SL-M",
      product: "CNC",
      trigger_price: triggerPrice,
      price: limitPrice,
    });

    let stopLossNote: string | undefined;
    let stopLossOrderId: string | undefined;

    if (stopOrder.status === "OK") {
      stopLossOrderId = stopOrder.orderId;
      stopLossNote = `Stop loss order placed at ${triggerPrice.toFixed(2)}.`;
    } else {
      stopLossNote = `Buy filled. Place stop near ${triggerPrice.toFixed(2)} in Zerodha — ${stopOrder.status === "ERROR" ? stopOrder.message : "SL order pending"}.`;
    }

    return {
      status: "OK",
      stock,
      amount: quantity * price,
      price,
      quantity,
      orderId: order.orderId,
      stopLoss: triggerPrice,
      stopLossOrderId,
      stopLossNote,
    };
  }

  if (sawExpired) {
    return { status: "TOKEN_EXPIRED" };
  }

  return { status: "ERROR", message: lastError };
}

export async function executeTradeSafe(
  supabase: Client,
  userId: string,
  input: ExecuteTradeInput,
): Promise<ExecuteTradeResult | null> {
  try {
    return await executeTrade(supabase, userId, input);
  } catch (error) {
    logger.error("trade_execution_failed", {
      route: "executeTradeSafe",
      userId,
      error: error instanceof Error ? error.message : "unknown",
    });
    return null;
  }
}
