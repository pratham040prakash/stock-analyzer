import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { resolveZerodhaAccessToken } from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaQuote,
} from "@/services/brokers/zerodha";
import { checkStopLoss } from "@/services/risk/riskControl";
import { normalizeSymbol } from "@/lib/stockPool";
import type { Signals } from "@/types/decision";
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

export type OpenMonitorResult = {
  positions: OpenMonitorPosition[];
  dayPnl: number | null;
};

type HoldingSnapshot = {
  quantity: number;
  lastPrice: number;
  averagePrice: number;
  closePrice: number;
  dayChange: number | null;
};

/** Prefer broker truth (avg / fill) over planned decision entry for P&L display. */
export function resolveMonitorEntryPrice(
  plannedEntry: number,
  fillPrice: number | null,
  holding: HoldingSnapshot | undefined,
): number {
  if (holding && holding.averagePrice > 0) {
    return holding.averagePrice;
  }

  if (fillPrice !== null && fillPrice > 0) {
    return fillPrice;
  }

  return plannedEntry;
}

/** Day P&L for one monitored open position (scoped strip, not whole portfolio). */
export function computeMonitorPositionDayPnl(
  quantity: number,
  entryPrice: number,
  holding: HoldingSnapshot | undefined,
  openedToday: boolean,
): number | null {
  if (!holding || holding.lastPrice <= 0 || quantity <= 0) {
    return null;
  }

  if (openedToday && entryPrice > 0) {
    return (holding.lastPrice - entryPrice) * quantity;
  }

  if (holding.dayChange !== null && Number.isFinite(holding.dayChange)) {
    return holding.dayChange * quantity;
  }

  if (holding.closePrice > 0) {
    return (holding.lastPrice - holding.closePrice) * quantity;
  }

  return null;
}

function parseFillPrice(signals: unknown): number | null {
  if (!signals || typeof signals !== "object") {
    return null;
  }

  const fillPrice = (signals as Signals).fill_price;
  return typeof fillPrice === "number" && fillPrice > 0 ? fillPrice : null;
}

function roundPrice(value: number): number {
  return Math.round(value * 10) / 10;
}

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
): Promise<OpenMonitorResult> {
  const { data: rows, error } = await supabase
    .from("decision_memory")
    .select(
      "id, stock, entry_price, stop_loss, quantity, amount, signals, decision_date",
    )
    .eq("user_id", userId)
    .eq("action", "buy")
    .is("exit_price", null)
    .not("stop_loss", "is", null)
    .not("stock", "is", null)
    .order("created_at", { ascending: false })
    .limit(10);

  if (error || !rows?.length) {
    return { positions: [], dayPnl: null };
  }

  const todayKey = tradingDateKey();
  const token = await resolveZerodhaAccessToken(supabase, userId);
  const holdingsBySymbol = new Map<string, HoldingSnapshot>();

  if (token) {
    const holdingsResult = await fetchZerodhaHoldings(token.accessToken);
    if (holdingsResult.status === "OK") {
      for (const holding of holdingsResult.data) {
        const symbol = normalizeSymbol(holding.tradingsymbol);
        holdingsBySymbol.set(symbol, {
          quantity: holding.quantity,
          lastPrice: holding.last_price,
          averagePrice: holding.average_price,
          closePrice:
            typeof holding.close_price === "number" && holding.close_price > 0
              ? holding.close_price
              : 0,
          dayChange:
            typeof holding.day_change === "number" &&
            Number.isFinite(holding.day_change)
              ? holding.day_change
              : null,
        });
      }
    }
  }

  const monitors: OpenMonitorPosition[] = [];
  const seenStocks = new Set<string>();
  let dayPnlTotal = 0;
  let hasDayPnl = false;

  for (const row of rows) {
    const stock = normalizeSymbol(row.stock ?? "");
    if (!stock || seenStocks.has(stock)) {
      continue;
    }

    const plannedEntry = Number(row.entry_price ?? 0);
    const stopLoss = Number(row.stop_loss ?? 0);

    if (plannedEntry <= 0 || stopLoss <= 0) {
      continue;
    }

    const holding = holdingsBySymbol.get(stock);
    const entryPrice = resolveMonitorEntryPrice(
      plannedEntry,
      parseFillPrice(row.signals),
      holding,
    );

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

    const openedToday = row.decision_date === todayKey;
    const positionDayPnl = computeMonitorPositionDayPnl(
      quantity,
      entryPrice,
      holding,
      openedToday,
    );

    if (positionDayPnl !== null) {
      hasDayPnl = true;
      dayPnlTotal += positionDayPnl;
    }

    const unrealizedPnl = (currentPrice - entryPrice) * quantity;
    const pnlPct =
      entryPrice > 0 ? ((currentPrice - entryPrice) / entryPrice) * 100 : 0;
    const { status, distanceToStopPct } = resolveStopStatus(
      currentPrice,
      stopLoss,
    );

    seenStocks.add(stock);
    monitors.push({
      id: row.id,
      stock,
      quantity,
      entryPrice: roundPrice(entryPrice),
      currentPrice: roundPrice(currentPrice),
      stopLoss: Math.round(stopLoss),
      unrealizedPnl: Math.round(unrealizedPnl),
      pnlPct,
      stopStatus: status,
      distanceToStopPct,
    });
  }

  return {
    positions: monitors,
    dayPnl: hasDayPnl ? Math.round(dayPnlTotal) : null,
  };
}

export function runOpenMonitorEntrySelfCheck(): void {
  const holding: HoldingSnapshot = {
    quantity: 1,
    lastPrice: 5067,
    averagePrice: 5058.7,
    closePrice: 5040,
    dayChange: 27,
  };

  const resolved = resolveMonitorEntryPrice(5067, null, holding);
  if (Math.abs(resolved - 5058.7) > 0.01) {
    throw new Error("resolveMonitorEntryPrice should prefer Zerodha average price");
  }

  const fromFill = resolveMonitorEntryPrice(5067, 5059.2, undefined);
  if (Math.abs(fromFill - 5059.2) > 0.01) {
    throw new Error("resolveMonitorEntryPrice should use fill price when holdings missing");
  }

  const openedTodayPnl = computeMonitorPositionDayPnl(1, 5058.7, holding, true);
  if (openedTodayPnl === null || Math.abs(openedTodayPnl - 8.3) > 0.01) {
    throw new Error("computeMonitorPositionDayPnl should use entry for same-day opens");
  }

  const overnightPnl = computeMonitorPositionDayPnl(1, 5058.7, holding, false);
  if (overnightPnl === null || Math.abs(overnightPnl - 27) > 0.01) {
    throw new Error("computeMonitorPositionDayPnl should use Zerodha day_change when held overnight");
  }
}
