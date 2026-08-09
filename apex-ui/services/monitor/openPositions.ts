import { resolveZerodhaAccessToken } from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaQuote,
} from "@/services/brokers/zerodha";
import { checkStopLoss } from "@/services/risk/riskControl";
import { normalizeSymbol } from "@/lib/stockPool";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type MonitorStopStatus = "safe" | "near" | "breached";

export type OpenMonitorPosition = {
  id: string;
  stock: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  stopLoss: number;
  unrealizedPnl: number;
  pnlPct: number;
  stopStatus: MonitorStopStatus;
  distanceToStopPct: number;
};

function resolveStopStatus(
  currentPrice: number,
  stopLoss: number,
): { status: MonitorStopStatus; distanceToStopPct: number } {
  if (stopLoss <= 0) {
    return { status: "safe", distanceToStopPct: 0 };
  }

  if (checkStopLoss({ stopLoss }, currentPrice)) {
    return { status: "breached", distanceToStopPct: 0 };
  }

  const distanceToStopPct = ((currentPrice - stopLoss) / stopLoss) * 100;

  if (distanceToStopPct <= 2) {
    return { status: "near", distanceToStopPct };
  }

  return { status: "safe", distanceToStopPct };
}

export async function getOpenMonitorPositions(
  supabase: Client,
  userId: string,
): Promise<OpenMonitorPosition[]> {
  const { data: rows, error } = await supabase
    .from("decision_memory")
    .select(
      "id, stock, entry_price, stop_loss, quantity, amount",
    )
    .eq("user_id", userId)
    .eq("action", "buy")
    .is("exit_price", null)
    .not("stop_loss", "is", null)
    .not("stock", "is", null)
    .order("created_at", { ascending: false })
    .limit(10);

  if (error || !rows?.length) {
    return [];
  }

  const token = await resolveZerodhaAccessToken(supabase, userId);
  const holdingsBySymbol = new Map<
    string,
    { quantity: number; lastPrice: number }
  >();

  if (token) {
    const holdingsResult = await fetchZerodhaHoldings(token.accessToken);
    if (holdingsResult.status === "OK") {
      for (const holding of holdingsResult.data) {
        const symbol = normalizeSymbol(holding.tradingsymbol);
        holdingsBySymbol.set(symbol, {
          quantity: holding.quantity,
          lastPrice: holding.last_price,
        });
      }
    }
  }

  const monitors: OpenMonitorPosition[] = [];

  for (const row of rows) {
    const stock = normalizeSymbol(row.stock ?? "");
    if (!stock) {
      continue;
    }

    const entryPrice = Number(row.entry_price ?? 0);
    const stopLoss = Number(row.stop_loss ?? 0);

    if (entryPrice <= 0 || stopLoss <= 0) {
      continue;
    }

    const holding = holdingsBySymbol.get(stock);
    let quantity = Math.max(0, Math.round(Number(row.quantity ?? 0)));

    if (holding) {
      if (holding.quantity < 1) {
        continue;
      }
      quantity = quantity > 0 ? Math.min(quantity, holding.quantity) : holding.quantity;
    } else if (quantity < 1) {
      quantity = Math.max(
        1,
        Math.floor(Number(row.amount ?? 0) / entryPrice),
      );
    }

    let currentPrice = holding?.lastPrice ?? 0;

    if (currentPrice <= 0 && token) {
      const quote = await fetchZerodhaQuote(token.accessToken, stock);
      if (quote.status === "OK") {
        currentPrice = quote.lastPrice;
      }
    }

    if (currentPrice <= 0) {
      currentPrice = entryPrice;
    }

    const unrealizedPnl = (currentPrice - entryPrice) * quantity;
    const pnlPct =
      entryPrice > 0 ? ((currentPrice - entryPrice) / entryPrice) * 100 : 0;
    const { status, distanceToStopPct } = resolveStopStatus(
      currentPrice,
      stopLoss,
    );

    monitors.push({
      id: row.id,
      stock,
      quantity,
      entryPrice: Math.round(entryPrice),
      currentPrice: Math.round(currentPrice),
      stopLoss: Math.round(stopLoss),
      unrealizedPnl: Math.round(unrealizedPnl),
      pnlPct,
      stopStatus: status,
      distanceToStopPct,
    });
  }

  return monitors;
}
