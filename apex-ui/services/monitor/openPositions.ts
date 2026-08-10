import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { resolveZerodhaAccessToken } from "@/services/broker/accessToken";
import {
  fetchZerodhaHoldings,
  fetchZerodhaQuotes,
  type ZerodhaLiveQuote,
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

type PendingMonitorRow = {
  id: string;
  stock: string;
  entryPrice: number;
  stopLoss: number;
  quantity: number;
  openedToday: boolean;
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

export function resolveOpenedToday(
  decisionDate: string | null | undefined,
  signals: unknown,
  todayKey: string,
): boolean {
  const sig = signals as Signals | null;

  if (sig?.filled_at && typeof sig.filled_at === "string") {
    return sig.filled_at.slice(0, 10) === todayKey;
  }

  return decisionDate === todayKey;
}

/** Day P&L for one monitored open position using live LTP + prior close. */
export function computeMonitorPositionDayPnl(
  quantity: number,
  entryPrice: number,
  liveLastPrice: number,
  previousClose: number | null,
  holding: HoldingSnapshot | undefined,
  openedToday: boolean,
): number | null {
  if (liveLastPrice <= 0 || quantity <= 0) {
    return null;
  }

  if (openedToday && entryPrice > 0) {
    return (liveLastPrice - entryPrice) * quantity;
  }

  const close =
    previousClose ??
    (holding && holding.closePrice > 0 ? holding.closePrice : null);

  if (close !== null && close > 0) {
    return (liveLastPrice - close) * quantity;
  }

  if (
    holding &&
    holding.dayChange !== null &&
    Number.isFinite(holding.dayChange)
  ) {
    return holding.dayChange * quantity;
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

function roundPnl(value: number): number {
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

  const pending: PendingMonitorRow[] = [];
  const seenStocks = new Set<string>();

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

    seenStocks.add(stock);
    pending.push({
      id: row.id,
      stock,
      entryPrice,
      stopLoss,
      quantity,
      openedToday: resolveOpenedToday(row.decision_date, row.signals, todayKey),
    });
  }

  const liveQuotes: Map<string, ZerodhaLiveQuote> =
    token && pending.length > 0
      ? await fetchZerodhaQuotes(
          token.accessToken,
          pending.map((item) => item.stock),
        )
      : new Map<string, ZerodhaLiveQuote>();

  const monitors: OpenMonitorPosition[] = [];
  let dayPnlTotal = 0;
  let hasDayPnl = false;

  for (const item of pending) {
    const holding = holdingsBySymbol.get(item.stock);
    const quote = liveQuotes.get(item.stock);
    const liveLast =
      quote?.lastPrice ?? holding?.lastPrice ?? item.entryPrice;

    const positionDayPnl = computeMonitorPositionDayPnl(
      item.quantity,
      item.entryPrice,
      liveLast,
      quote?.previousClose ?? null,
      holding,
      item.openedToday,
    );

    if (positionDayPnl !== null) {
      hasDayPnl = true;
      dayPnlTotal += positionDayPnl;
    }

    const unrealizedPnl = (liveLast - item.entryPrice) * item.quantity;
    const pnlPct =
      item.entryPrice > 0
        ? ((liveLast - item.entryPrice) / item.entryPrice) * 100
        : 0;
    const { status, distanceToStopPct } = resolveStopStatus(
      liveLast,
      item.stopLoss,
    );

    monitors.push({
      id: item.id,
      stock: item.stock,
      quantity: item.quantity,
      entryPrice: roundPrice(item.entryPrice),
      currentPrice: roundPrice(liveLast),
      stopLoss: Math.round(item.stopLoss),
      unrealizedPnl: roundPnl(unrealizedPnl),
      pnlPct,
      stopStatus: status,
      distanceToStopPct,
    });
  }

  return {
    positions: monitors,
    dayPnl: hasDayPnl ? roundPnl(dayPnlTotal) : null,
  };
}

export function runOpenMonitorEntrySelfCheck(): void {
  const holding: HoldingSnapshot = {
    quantity: 1,
    lastPrice: 5058.7,
    averagePrice: 5058.7,
    closePrice: 5040,
    dayChange: 0,
  };

  const resolved = resolveMonitorEntryPrice(5067, null, holding);
  if (Math.abs(resolved - 5058.7) > 0.01) {
    throw new Error("resolveMonitorEntryPrice should prefer Zerodha average price");
  }

  const fromFill = resolveMonitorEntryPrice(5067, 5059.2, undefined);
  if (Math.abs(fromFill - 5059.2) > 0.01) {
    throw new Error("resolveMonitorEntryPrice should use fill price when holdings missing");
  }

  const openedTodayPnl = computeMonitorPositionDayPnl(
    1,
    5058.7,
    5067,
    5040,
    holding,
    true,
  );
  if (openedTodayPnl === null || Math.abs(openedTodayPnl - 8.3) > 0.01) {
    throw new Error("computeMonitorPositionDayPnl should use live LTP vs entry for same-day opens");
  }

  const overnightPnl = computeMonitorPositionDayPnl(
    1,
    5058.7,
    5067,
    5040,
    holding,
    false,
  );
  if (overnightPnl === null || Math.abs(overnightPnl - 27) > 0.01) {
    throw new Error("computeMonitorPositionDayPnl should use live LTP vs prior close overnight");
  }
}
