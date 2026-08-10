import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import {
  fetchLiveKitePortfolioCached,
  type LiveKitePortfolioResult,
} from "@/services/broker/kitePortfolio";
import { checkStopLoss } from "@/services/risk/riskControl";
import type { ZerodhaLiveQuote } from "@/services/brokers/zerodha";
import { signalsIndicateBrokerFill } from "@/services/trade/logTradeFill";
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

/** Live price + P&L tick for one open position (5s poll, no card reload). */
export type MonitorLiveTick = {
  id: string;
  currentPrice: number;
  unrealizedPnl: number;
  pnlPct: number;
  positionDayPnl: number | null;
  stopStatus: MonitorStopStatus;
};

export type MonitorLiveSnapshot = {
  dayPnl: number | null;
  ticks: MonitorLiveTick[];
};

type HoldingSnapshot = {
  quantity: number;
  t1Quantity: number;
  lastPrice: number;
  averagePrice: number;
  closePrice: number;
  dayChange: number | null;
  m2m: number | null;
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

/** Monitor strip only tracks executed buys that are still held at the broker. */
export function isExecutedOpenMonitorDecision(
  signals: unknown,
  holding: HoldingSnapshot | undefined,
): boolean {
  if (!signalsIndicateBrokerFill(signals as Signals | null)) {
    return false;
  }

  return Boolean(holding && holding.quantity >= 1);
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

/** Resolve display LTP — quote first, then close+day_change from holdings. */
export function resolveLiveLastPrice(
  quote: ZerodhaLiveQuote | undefined,
  holding: HoldingSnapshot | undefined,
  entryPrice: number,
): number {
  if (quote?.lastPrice && quote.lastPrice > 0) {
    return quote.lastPrice;
  }

  if (holding) {
    if (
      holding.closePrice > 0 &&
      holding.dayChange !== null &&
      holding.dayChange !== 0
    ) {
      const derived = holding.closePrice + holding.dayChange;
      if (derived > 0) {
        return derived;
      }
    }

    if (holding.lastPrice > 0) {
      return holding.lastPrice;
    }
  }

  return entryPrice;
}

/** Day P&L for one monitored position — broker standard vs prior close / day_change. */
export function computeMonitorPositionDayPnl(
  quantity: number,
  entryPrice: number,
  liveLastPrice: number,
  previousClose: number | null,
  holding: HoldingSnapshot | undefined,
): number | null {
  if (quantity <= 0) {
    return null;
  }

  if (
    holding &&
    holding.m2m !== null &&
    Number.isFinite(holding.m2m)
  ) {
    const effectiveQty = holding.quantity + holding.t1Quantity;
    if (effectiveQty > 0) {
      return (holding.m2m / effectiveQty) * quantity;
    }
  }

  const close =
    previousClose ??
    (holding && holding.closePrice > 0 ? holding.closePrice : null);

  if (close !== null && close > 0 && liveLastPrice > 0) {
    return (liveLastPrice - close) * quantity;
  }

  if (
    holding &&
    holding.dayChange !== null &&
    Number.isFinite(holding.dayChange)
  ) {
    return holding.dayChange * quantity;
  }

  if (entryPrice > 0 && liveLastPrice > 0) {
    return (liveLastPrice - entryPrice) * quantity;
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

function holdingsMapFromLivePortfolio(
  livePortfolio: LiveKitePortfolioResult,
): Map<string, HoldingSnapshot> {
  const holdingsBySymbol = new Map<string, HoldingSnapshot>();

  if (livePortfolio.status !== "OK") {
    return holdingsBySymbol;
  }

  for (const holding of livePortfolio.holdings) {
    const symbol = normalizeSymbol(holding.tradingsymbol);
    holdingsBySymbol.set(symbol, {
      quantity: holding.quantity,
      t1Quantity: Math.max(0, Math.round(holding.t1_quantity ?? 0)),
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
      m2m:
        typeof holding.m2m === "number" && Number.isFinite(holding.m2m)
          ? holding.m2m
          : null,
    });
  }

  return holdingsBySymbol;
}

function sumMonitorDayPnl(
  pending: PendingMonitorRow[],
  holdingsBySymbol: Map<string, HoldingSnapshot>,
): number | null {
  let dayPnlTotal = 0;
  let hasDayPnl = false;

  for (const item of pending) {
    const holding = holdingsBySymbol.get(item.stock);
    const liveLast = resolveLiveLastPrice(undefined, holding, item.entryPrice);
    const positionDayPnl = computeMonitorPositionDayPnl(
      item.quantity,
      item.entryPrice,
      liveLast,
      holding && holding.closePrice > 0 ? holding.closePrice : null,
      holding,
    );

    if (positionDayPnl !== null) {
      hasDayPnl = true;
      dayPnlTotal += positionDayPnl;
    }
  }

  return hasDayPnl ? roundPnl(dayPnlTotal) : null;
}

function buildMonitorLiveTicks(
  pending: PendingMonitorRow[],
  holdingsBySymbol: Map<string, HoldingSnapshot>,
): MonitorLiveTick[] {
  const ticks: MonitorLiveTick[] = [];

  for (const item of pending) {
    const holding = holdingsBySymbol.get(item.stock);
    const liveLast = resolveLiveLastPrice(undefined, holding, item.entryPrice);
    const unrealizedPnl = (liveLast - item.entryPrice) * item.quantity;
    const pnlPct =
      item.entryPrice > 0
        ? ((liveLast - item.entryPrice) / item.entryPrice) * 100
        : 0;
    const positionDayPnl = computeMonitorPositionDayPnl(
      item.quantity,
      item.entryPrice,
      liveLast,
      holding && holding.closePrice > 0 ? holding.closePrice : null,
      holding,
    );
    const { status } = resolveStopStatus(liveLast, item.stopLoss);

    ticks.push({
      id: item.id,
      currentPrice: roundPrice(liveLast),
      unrealizedPnl: roundPnl(unrealizedPnl),
      pnlPct,
      positionDayPnl:
        positionDayPnl === null ? null : roundPnl(positionDayPnl),
      stopStatus: status,
    });
  }

  return ticks;
}

async function buildPendingMonitorRows(
  supabase: Client,
  userId: string,
  holdingsBySymbol: Map<string, HoldingSnapshot>,
): Promise<PendingMonitorRow[]> {
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
    return [];
  }

  const todayKey = tradingDateKey();
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

    if (!isExecutedOpenMonitorDecision(row.signals, holding)) {
      continue;
    }

    const entryPrice = resolveMonitorEntryPrice(
      plannedEntry,
      parseFillPrice(row.signals),
      holding,
    );

    const quantity =
      Math.max(0, Math.round(Number(row.quantity ?? 0))) > 0
        ? Math.min(
            Math.max(0, Math.round(Number(row.quantity ?? 0))),
            holding!.quantity,
          )
        : holding!.quantity;

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

  return pending;
}

export async function getOpenMonitorLiveSnapshot(
  supabase: Client,
  userId: string,
  livePortfolio?: LiveKitePortfolioResult,
): Promise<MonitorLiveSnapshot> {
  const live =
    livePortfolio ?? (await fetchLiveKitePortfolioCached(supabase, userId));
  const holdingsBySymbol = holdingsMapFromLivePortfolio(live);
  const pending = await buildPendingMonitorRows(
    supabase,
    userId,
    holdingsBySymbol,
  );

  if (pending.length === 0) {
    return { dayPnl: null, ticks: [] };
  }

  return {
    dayPnl: sumMonitorDayPnl(pending, holdingsBySymbol),
    ticks: buildMonitorLiveTicks(pending, holdingsBySymbol),
  };
}

export async function getOpenMonitorDayPnl(
  supabase: Client,
  userId: string,
  livePortfolio?: LiveKitePortfolioResult,
): Promise<number | null> {
  const snapshot = await getOpenMonitorLiveSnapshot(
    supabase,
    userId,
    livePortfolio,
  );
  return snapshot.dayPnl;
}

export async function getOpenMonitorPositions(
  supabase: Client,
  userId: string,
  options?: {
    livePortfolio?: LiveKitePortfolioResult;
    includePositions?: boolean;
  },
): Promise<OpenMonitorResult> {
  const livePortfolio =
    options?.livePortfolio ??
    (await fetchLiveKitePortfolioCached(supabase, userId));
  const holdingsBySymbol = holdingsMapFromLivePortfolio(livePortfolio);
  const pending = await buildPendingMonitorRows(
    supabase,
    userId,
    holdingsBySymbol,
  );

  if (pending.length === 0) {
    return { positions: [], dayPnl: null };
  }

  const includePositions = options?.includePositions !== false;
  const dayPnl = sumMonitorDayPnl(pending, holdingsBySymbol);

  if (!includePositions) {
    return { positions: [], dayPnl };
  }

  const monitors: OpenMonitorPosition[] = [];

  for (const item of pending) {
    const holding = holdingsBySymbol.get(item.stock);
    const liveLast = resolveLiveLastPrice(undefined, holding, item.entryPrice);

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
    dayPnl,
  };
}

export function runOpenMonitorEntrySelfCheck(): void {
  const holding: HoldingSnapshot = {
    quantity: 1,
    t1Quantity: 0,
    lastPrice: 5058.7,
    averagePrice: 5058.7,
    closePrice: 5040,
    dayChange: 18.7,
    m2m: null,
  };

  const resolved = resolveMonitorEntryPrice(5067, null, holding);
  if (Math.abs(resolved - 5058.7) > 0.01) {
    throw new Error("resolveMonitorEntryPrice should prefer Zerodha average price");
  }

  const fromFill = resolveMonitorEntryPrice(5067, 5059.2, undefined);
  if (Math.abs(fromFill - 5059.2) > 0.01) {
    throw new Error("resolveMonitorEntryPrice should use fill price when holdings missing");
  }

  const derived = resolveLiveLastPrice(undefined, holding, 5058.7);
  if (Math.abs(derived - 5058.7) > 0.01) {
    throw new Error("resolveLiveLastPrice should derive LTP from close + day_change");
  }

  const flatDay = resolveLiveLastPrice(
    undefined,
    { ...holding, dayChange: 0, lastPrice: 5058.7 },
    5058.7,
  );
  if (Math.abs(flatDay - 5058.7) > 0.01) {
    throw new Error("resolveLiveLastPrice must not treat day_change 0 as yesterday close");
  }

  const openedTodayPnl = computeMonitorPositionDayPnl(
    1,
    5058.7,
    5058.7,
    5040,
    holding,
  );
  if (openedTodayPnl === null || Math.abs(openedTodayPnl - 18.7) > 0.01) {
    throw new Error("computeMonitorPositionDayPnl should use prior close for day P&L");
  }

  const overnightPnl = computeMonitorPositionDayPnl(
    1,
    5058.7,
    5067,
    5040,
    holding,
  );
  if (overnightPnl === null || Math.abs(overnightPnl - 27) > 0.01) {
    throw new Error("computeMonitorPositionDayPnl should use live LTP vs prior close");
  }

  const filledSignals = {
    trend: 0,
    momentum: 0,
    volume: 0,
    order_id: "2086696629296996352",
    fill_price: 5058.7,
    filled_at: "2026-08-10T09:30:00.000Z",
  };

  if (
    isExecutedOpenMonitorDecision(filledSignals, holding) !== true ||
    isExecutedOpenMonitorDecision(filledSignals, undefined) !== false ||
    isExecutedOpenMonitorDecision(null, holding) !== false
  ) {
    throw new Error("isExecutedOpenMonitorDecision must require broker fill and live holding");
  }
}
