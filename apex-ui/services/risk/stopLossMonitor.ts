import { fetchStockData } from "@/services/market/stockData";
import { getSignalsForStock } from "@/services/decision/stockScoring";
import {
  fetchZerodhaHoldings,
  fetchZerodhaQuote,
  placeZerodhaOrder,
} from "@/services/brokers/zerodha";
import { getActiveBrokerConnection } from "@/services/broker/connections";
import { checkStopLoss, type RiskPosition } from "@/services/risk/riskControl";
import {
  checkSignalReversal,
  checkTakeProfit,
  computeTrailingStop,
  shouldUpdateTrailingStop,
  takeProfitSellQuantity,
} from "@/services/risk/profitOptimization";
import {
  getOpenStopLossPositions,
  updateDecisionOutcome,
  updatePositionAfterPartialExit,
  updatePositionSignals,
  updateStopLoss,
} from "@/services/decision/decisionMemory";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

type OpenPosition = {
  id: string;
  user_id: string;
  stock: string;
  entry_price: number | null;
  stop_loss: number | null;
  amount: number | null;
  quantity: number | null;
  take_profit_taken: boolean;
};

export type PositionMonitorResult = {
  checked: number;
  triggered: number;
  failed: number;
  stopLossExits: number;
  takeProfitExits: number;
  signalExits: number;
  trailingUpdates: number;
};

async function resolveCurrentPrice(
  accessToken: string | null,
  stock: string,
): Promise<number | null> {
  if (accessToken) {
    const quote = await fetchZerodhaQuote(accessToken, stock);
    if (quote.status === "OK") {
      return quote.lastPrice;
    }
  }

  const data = await fetchStockData(stock);
  if (!data.prices.length) {
    return null;
  }

  return data.prices[data.prices.length - 1] ?? null;
}

function resolvePositionQuantity(record: OpenPosition): number {
  if (record.quantity && record.quantity > 0) {
    return Math.floor(Number(record.quantity));
  }

  if (record.amount && record.entry_price && record.entry_price > 0) {
    return Math.floor(Number(record.amount) / Number(record.entry_price));
  }

  return 0;
}

async function resolveSellQuantity(
  accessToken: string,
  record: OpenPosition,
  requestedQuantity: number,
): Promise<number> {
  let quantity = requestedQuantity;

  if (quantity < 1) {
    quantity = resolvePositionQuantity(record);
  }

  if (quantity < 1) {
    const holdings = await fetchZerodhaHoldings(accessToken);
    if (holdings.status === "OK") {
      const holding = holdings.data.find(
        (item) => item.tradingsymbol === record.stock,
      );
      quantity = holding?.quantity ?? 0;
    }
  }

  return quantity;
}

async function executeSellOrder(
  supabase: Client,
  record: OpenPosition,
  currentPrice: number,
  quantity: number,
  reason: string,
): Promise<boolean> {
  const connection = await getActiveBrokerConnection(supabase, record.user_id);

  if (!connection?.accessToken || connection.status !== "active") {
    return false;
  }

  const sellQuantity = await resolveSellQuantity(
    connection.accessToken,
    record,
    quantity,
  );

  if (sellQuantity < 1) {
    return false;
  }

  const order = await placeZerodhaOrder(connection.accessToken, {
    tradingsymbol: record.stock,
    transaction_type: "SELL",
    quantity: sellQuantity,
    order_type: "MARKET",
    product: "CNC",
  });

  if (order.status !== "OK") {
    console.warn(`${reason} sell failed:`, record.stock, order);
    return false;
  }

  console.log(`${reason} executed:`, {
    stock: record.stock,
    price: currentPrice,
    quantity: sellQuantity,
    orderId: order.orderId,
  });

  return true;
}

async function executeFullExit(
  supabase: Client,
  record: OpenPosition,
  currentPrice: number,
  reason: string,
): Promise<boolean> {
  const sold = await executeSellOrder(
    supabase,
    record,
    currentPrice,
    resolvePositionQuantity(record),
    reason,
  );

  if (!sold) {
    return false;
  }

  await updateDecisionOutcome(supabase, record.id, currentPrice);
  return true;
}

async function executePartialTakeProfit(
  supabase: Client,
  record: OpenPosition,
  currentPrice: number,
): Promise<boolean> {
  const totalQuantity = resolvePositionQuantity(record);
  const sellQuantity = takeProfitSellQuantity(totalQuantity);

  if (sellQuantity < 1) {
    return false;
  }

  const sold = await executeSellOrder(
    supabase,
    record,
    currentPrice,
    sellQuantity,
    "Take-profit",
  );

  if (!sold) {
    return false;
  }

  const remainingQuantity = totalQuantity - sellQuantity;
  return updatePositionAfterPartialExit(
    supabase,
    record.id,
    remainingQuantity,
    currentPrice,
  );
}

async function applyTrailingStop(
  supabase: Client,
  record: OpenPosition,
  currentPrice: number,
): Promise<number | null> {
  const currentStopLoss = Number(record.stop_loss);

  if (!shouldUpdateTrailingStop(currentStopLoss, currentPrice)) {
    return currentStopLoss;
  }

  const nextStopLoss = computeTrailingStop(currentStopLoss, currentPrice);
  const updated = await updateStopLoss(supabase, record.id, nextStopLoss);

  return updated ? nextStopLoss : currentStopLoss;
}

export async function monitorStopLosses(
  supabase: Client,
): Promise<PositionMonitorResult> {
  const positions = await getOpenStopLossPositions(supabase);
  const priceCache = new Map<string, number>();
  const tokenCache = new Map<string, string | null>();

  let triggered = 0;
  let failed = 0;
  let stopLossExits = 0;
  let takeProfitExits = 0;
  let signalExits = 0;
  let trailingUpdates = 0;

  for (const record of positions) {
    if (!record.stock || !record.stop_loss || !record.entry_price) {
      failed += 1;
      continue;
    }

    let token = tokenCache.get(record.user_id);
    if (token === undefined) {
      const connection = await getActiveBrokerConnection(
        supabase,
        record.user_id,
      );
      token = connection?.accessToken ?? null;
      tokenCache.set(record.user_id, token);
    }

    let currentPrice = priceCache.get(record.stock);
    if (!currentPrice) {
      const resolved = await resolveCurrentPrice(token, record.stock);
      if (resolved && resolved > 0) {
        currentPrice = resolved;
        priceCache.set(record.stock, currentPrice);
      }
    }

    if (!currentPrice) {
      failed += 1;
      continue;
    }

    const entryPrice = Number(record.entry_price);
    let activeStopLoss = Number(record.stop_loss);

    const previousStopLoss = activeStopLoss;
    const trailingStop = await applyTrailingStop(
      supabase,
      record,
      currentPrice,
    );

    if (trailingStop !== null) {
      activeStopLoss = trailingStop;
      if (trailingStop > previousStopLoss) {
        trailingUpdates += 1;
      }
    }

    const signals = await getSignalsForStock(record.stock);
    await updatePositionSignals(supabase, record.id, signals);

    if (checkSignalReversal(signals)) {
      const sold = await executeFullExit(
        supabase,
        record,
        currentPrice,
        "Signal-reversal",
      );

      if (sold) {
        triggered += 1;
        signalExits += 1;
      } else {
        failed += 1;
      }
      continue;
    }

    const position: RiskPosition = { stopLoss: activeStopLoss };

    if (checkStopLoss(position, currentPrice)) {
      const sold = await executeFullExit(
        supabase,
        record,
        currentPrice,
        "Stop-loss",
      );

      if (sold) {
        triggered += 1;
        stopLossExits += 1;
      } else {
        failed += 1;
      }
      continue;
    }

    if (!record.take_profit_taken && checkTakeProfit(entryPrice, currentPrice)) {
      const sold = await executePartialTakeProfit(
        supabase,
        record,
        currentPrice,
      );

      if (sold) {
        triggered += 1;
        takeProfitExits += 1;
      } else {
        failed += 1;
      }
    }
  }

  return {
    checked: positions.length,
    triggered,
    failed,
    stopLossExits,
    takeProfitExits,
    signalExits,
    trailingUpdates,
  };
}
