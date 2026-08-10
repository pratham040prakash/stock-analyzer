import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import {
  fetchLiveKitePortfolioCached,
  type LiveKitePortfolioResult,
} from "@/services/broker/kitePortfolio";
import { checkStopLoss } from "@/services/risk/riskControl";
import type { ZerodhaLiveQuote } from "@/services/brokers/zerodha";
import { fetchZerodhaQuotes } from "@/services/brokers/zerodha";
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
  /** Open P&L vs avg — matches Zerodha Positions column. */
  openPnl: number | null;
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
  /** Sum of open P&L vs avg — matches Zerodha Positions P&L column. */
  openPnl: number | null;
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
  /** Zerodha net-position unrealised P&L when available. */
  brokerPnl: number | null;
};

type SyncHoldContext = {
  symbols: Set<string>;
  orderIds: Set<string>;
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

function effectiveHoldingQuantity(holding: HoldingSnapshot): number {
  return Math.max(0, holding.quantity) + Math.max(0, holding.t1Quantity);
}

/** APEX execute fills only — excludes Kite sync attaching manual trades to old decisions. */
function isSyncAttachedGhostFill(
  sig: Signals,
  decisionDate: string | null | undefined,
): boolean {
  if (sig.fill_source === "sync") {
    return true;
  }

  if (sig.fill_source === "execute") {
    return false;
  }

  const filledDay = sig.filled_at?.slice(0, 10);
  if (!filledDay || filledDay !== tradingDateKey()) {
    return false;
  }

  return Boolean(decisionDate && decisionDate !== filledDay);
}

function isApexExecuteFill(
  sig: Signals | null,
  decisionDate?: string | null,
): boolean {
  if (!sig) {
    return false;
  }

  if (isSyncAttachedGhostFill(sig, decisionDate)) {
    return false;
  }

  if (sig.fill_source === "sync") {
    return false;
  }

  if (sig.fill_source === "execute" || sig.apex_executed === true) {
    return true;
  }

  return false;
}

async function loadSyncHoldContext(
  supabase: Client,
  userId: string,
  dateKey = tradingDateKey(),
): Promise<SyncHoldContext> {
  const { data, error } = await supabase
    .from("decision_memory")
    .select("stock, signals")
    .eq("user_id", userId)
    .eq("decision_date", dateKey)
    .eq("action", "hold");

  if (error || !data?.length) {
    return { symbols: new Set(), orderIds: new Set() };
  }

  const symbols = new Set<string>();
  const orderIds = new Set<string>();

  for (const row of data) {
    const sig = row.signals as Signals | null;
    if (sig?.fill_source !== "sync" || !sig.order_id) {
      continue;
    }

    const stock = normalizeSymbol(row.stock ?? "");
    if (!stock) {
      continue;
    }

    symbols.add(stock);
    orderIds.add(String(sig.order_id));
  }

  return { symbols, orderIds };
}

function stripBrokerFillSignals(signals: Signals | null): Signals {
  return {
    trend: signals?.trend ?? 0,
    momentum: signals?.momentum ?? 0,
    volume: signals?.volume ?? 0,
    monitored: false,
  };
}

/** Remove sync-attached broker fills from open buy rows (persisted ghosts). */
async function sanitizeSyncGhostOpenBuys(
  supabase: Client,
  userId: string,
  syncContext: SyncHoldContext,
): Promise<void> {
  const { data: rows, error } = await supabase
    .from("decision_memory")
    .select("id, stock, signals")
    .eq("user_id", userId)
    .eq("action", "buy")
    .is("exit_price", null);

  if (error || !rows?.length) {
    return;
  }

  for (const row of rows) {
    const sig = row.signals as Signals | null;
    if (!signalsIndicateBrokerFill(sig)) {
      continue;
    }

    const stock = normalizeSymbol(row.stock ?? "");
    const orderId = sig?.order_id ? String(sig.order_id) : "";
    const shouldStrip =
      sig?.fill_source === "sync" ||
      (orderId && syncContext.orderIds.has(orderId)) ||
      (stock && syncContext.symbols.has(stock) && sig?.apex_executed !== true);

    if (!shouldStrip) {
      continue;
    }

    await supabase
      .from("decision_memory")
      .update({
        signals: stripBrokerFillSignals(sig),
        updated_at: new Date().toISOString(),
      })
      .eq("id", row.id);
  }
}

/** Manual Kite buys synced today must not appear on the APEX monitor strip. */
function isManualSyncMonitorGhost(
  stock: string,
  signals: unknown,
  syncContext: SyncHoldContext,
  row: { created_at?: string | null; decision_date?: string | null },
): boolean {
  const sig = signals as Signals | null;

  if (!sig) {
    return true;
  }

  if (sig.apex_executed === true) {
    return false;
  }

  const orderId = sig.order_id ? String(sig.order_id) : "";
  if (orderId && syncContext.orderIds.has(orderId)) {
    return true;
  }

  const todayKey = tradingDateKey();
  const filledDay = sig.filled_at?.slice(0, 10);
  const createdDay = row.created_at?.slice(0, 10);

  if (
    createdDay &&
    createdDay < todayKey &&
    row.decision_date === todayKey &&
    filledDay === todayKey &&
    sig.fill_source !== "execute"
  ) {
    return true;
  }

  if (syncContext.symbols.has(stock)) {
    return true;
  }

  return false;
}

/** Monitor strip only tracks executed buys that are still held at the broker. */
export function isExecutedOpenMonitorDecision(
  signals: unknown,
  holding: HoldingSnapshot | undefined,
  plannedEntry?: number,
  decisionDate?: string | null,
): boolean {
  const sig = signals as Signals | null;

  if (!signalsIndicateBrokerFill(sig)) {
    return false;
  }

  if (sig?.monitored === false) {
    return false;
  }

  if (!isApexExecuteFill(sig, decisionDate)) {
    return false;
  }

  if (!holding || effectiveHoldingQuantity(holding) < 1) {
    return false;
  }

  return true;
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

/** Resolve display LTP — live quote / broker last_price first (matches Zerodha LTP). */
export function resolveLiveLastPrice(
  quote: ZerodhaLiveQuote | undefined,
  holding: HoldingSnapshot | undefined,
  entryPrice: number,
): number {
  if (quote?.lastPrice && quote.lastPrice > 0) {
    return quote.lastPrice;
  }

  if (holding?.lastPrice && holding.lastPrice > 0) {
    return holding.lastPrice;
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

/** Zerodha Positions P&L: (LTP − avg) × qty using broker snapshot. */
function computeBrokerOpenPnl(
  quantity: number,
  entryPrice: number,
  holding: HoldingSnapshot | undefined,
): { ltp: number; pnl: number; pnlPct: number } {
  const avg =
    holding && holding.averagePrice > 0 ? holding.averagePrice : entryPrice;
  const ltp =
    holding && holding.lastPrice > 0
      ? holding.lastPrice
      : resolveLiveLastPrice(undefined, holding, avg);

  if (
    holding &&
    holding.brokerPnl !== null &&
    Number.isFinite(holding.brokerPnl)
  ) {
    const effectiveQty = effectiveHoldingQuantity(holding);
    const pnl =
      effectiveQty > 0 && quantity !== effectiveQty
        ? (holding.brokerPnl / effectiveQty) * quantity
        : holding.brokerPnl;
    const pnlPct = avg > 0 ? ((ltp - avg) / avg) * 100 : 0;

    return {
      ltp: roundPrice(ltp),
      pnl: roundPnl(pnl),
      pnlPct,
    };
  }

  const pnl = (ltp - avg) * quantity;
  const pnlPct = avg > 0 ? ((ltp - avg) / avg) * 100 : 0;

  return {
    ltp: roundPrice(ltp),
    pnl: roundPnl(pnl),
    pnlPct,
  };
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
      brokerPnl:
        typeof holding.pnl === "number" && Number.isFinite(holding.pnl)
          ? holding.pnl
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

function sumMonitorOpenPnl(
  pending: PendingMonitorRow[],
  holdingsBySymbol: Map<string, HoldingSnapshot>,
): number | null {
  let openTotal = 0;
  let hasOpenPnl = false;

  for (const item of pending) {
    const holding = holdingsBySymbol.get(item.stock);
    const { pnl } = computeBrokerOpenPnl(
      item.quantity,
      item.entryPrice,
      holding,
    );
    openTotal += pnl;
    hasOpenPnl = true;
  }

  return hasOpenPnl ? roundPnl(openTotal) : null;
}

function buildMonitorLiveTicks(
  pending: PendingMonitorRow[],
  holdingsBySymbol: Map<string, HoldingSnapshot>,
): MonitorLiveTick[] {
  const ticks: MonitorLiveTick[] = [];

  for (const item of pending) {
    const holding = holdingsBySymbol.get(item.stock);
    const { ltp, pnl, pnlPct } = computeBrokerOpenPnl(
      item.quantity,
      item.entryPrice,
      holding,
    );
    const positionDayPnl = computeMonitorPositionDayPnl(
      item.quantity,
      item.entryPrice,
      ltp,
      holding && holding.closePrice > 0 ? holding.closePrice : null,
      holding,
    );
    const { status } = resolveStopStatus(ltp, item.stopLoss);

    ticks.push({
      id: item.id,
      currentPrice: ltp,
      unrealizedPnl: pnl,
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
  const syncContext = await loadSyncHoldContext(supabase, userId);
  await sanitizeSyncGhostOpenBuys(supabase, userId, syncContext);

  const { data: rows, error } = await supabase
    .from("decision_memory")
    .select(
      "id, stock, entry_price, stop_loss, quantity, amount, signals, decision_date, created_at",
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

    if (!isExecutedOpenMonitorDecision(row.signals, holding, plannedEntry, row.decision_date)) {
      continue;
    }

    if (isManualSyncMonitorGhost(stock, row.signals, syncContext, row)) {
      continue;
    }

    const entryPrice = resolveMonitorEntryPrice(
      plannedEntry,
      parseFillPrice(row.signals),
      holding,
    );

    const effectiveQty = effectiveHoldingQuantity(holding!);
    const quantity =
      Math.max(0, Math.round(Number(row.quantity ?? 0))) > 0
        ? Math.min(
            Math.max(0, Math.round(Number(row.quantity ?? 0))),
            effectiveQty,
          )
        : effectiveQty;

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

async function refreshHoldingsQuotesForMonitor(
  live: LiveKitePortfolioResult,
  pending: PendingMonitorRow[],
  holdingsBySymbol: Map<string, HoldingSnapshot>,
): Promise<void> {
  if (live.status !== "OK" || pending.length === 0) {
    return;
  }

  const symbols = [...new Set(pending.map((row) => row.stock))];
  const quotes = await fetchZerodhaQuotes(live.token.accessToken, symbols);

  for (const symbol of symbols) {
    const quote = quotes.get(symbol);
    const holding = holdingsBySymbol.get(symbol);

    if (!quote?.lastPrice || !holding) {
      continue;
    }

    const close = quote.previousClose ?? holding.closePrice;
    holdingsBySymbol.set(symbol, {
      ...holding,
      lastPrice: quote.lastPrice,
      closePrice: close > 0 ? close : holding.closePrice,
      dayChange:
        close > 0 ? quote.lastPrice - close : holding.dayChange,
    });
  }
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
    return { openPnl: null, dayPnl: null, ticks: [] };
  }

  await refreshHoldingsQuotesForMonitor(live, pending, holdingsBySymbol);

  return {
    openPnl: sumMonitorOpenPnl(pending, holdingsBySymbol),
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
    return { positions: [], openPnl: null, dayPnl: null };
  }

  await refreshHoldingsQuotesForMonitor(livePortfolio, pending, holdingsBySymbol);

  const includePositions = options?.includePositions !== false;
  const openPnl = sumMonitorOpenPnl(pending, holdingsBySymbol);
  const dayPnl = sumMonitorDayPnl(pending, holdingsBySymbol);

  if (!includePositions) {
    return { positions: [], openPnl, dayPnl };
  }

  const monitors: OpenMonitorPosition[] = [];

  for (const item of pending) {
    const holding = holdingsBySymbol.get(item.stock);
    const { ltp, pnl, pnlPct } = computeBrokerOpenPnl(
      item.quantity,
      item.entryPrice,
      holding,
    );
    const { status, distanceToStopPct } = resolveStopStatus(ltp, item.stopLoss);

    monitors.push({
      id: item.id,
      stock: item.stock,
      quantity: item.quantity,
      entryPrice: roundPrice(item.entryPrice),
      currentPrice: ltp,
      stopLoss: Math.round(item.stopLoss),
      unrealizedPnl: pnl,
      pnlPct,
      stopStatus: status,
      distanceToStopPct,
    });
  }

  return {
    positions: monitors,
    openPnl,
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
    brokerPnl: 39.5,
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
    throw new Error("resolveLiveLastPrice should prefer broker last_price");
  }

  const staleDayChange = resolveLiveLastPrice(
    undefined,
    { ...holding, lastPrice: 5067, dayChange: 18.7, closePrice: 5040 },
    5058.7,
  );
  if (Math.abs(staleDayChange - 5067) > 0.01) {
    throw new Error("resolveLiveLastPrice must not prefer stale day_change over last_price");
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
    monitored: true,
    fill_source: "execute" as const,
    order_id: "2086696629296996352",
    fill_price: 5058.7,
    filled_at: "2026-08-10T09:30:00.000Z",
  };

  const ghostSignals = {
    ...filledSignals,
    fill_source: "sync" as const,
  };

  const syncFill = {
    ...filledSignals,
    fill_source: "sync" as const,
  };

  const legacyTodayFill = {
    ...filledSignals,
    fill_source: undefined,
    filled_at: `${tradingDateKey()}T09:30:00.000Z`,
  };

  const syncGhostFill = {
    ...legacyTodayFill,
    filled_at: `${tradingDateKey()}T09:30:00.000Z`,
  };

  const legacyFill = {
    ...filledSignals,
    monitored: undefined,
    fill_source: undefined,
    filled_at: `${tradingDateKey()}T09:30:00.000Z`,
  };

  const legacyOvernightFill = {
    ...filledSignals,
    fill_source: "execute" as const,
    apex_executed: undefined,
    filled_at: "2026-08-09T09:30:00.000Z",
  };

  if (
    isExecutedOpenMonitorDecision(filledSignals, holding, 5067, tradingDateKey()) !== true ||
    isExecutedOpenMonitorDecision(legacyOvernightFill, holding, 5067, tradingDateKey()) !== true ||
    isExecutedOpenMonitorDecision(legacyFill, holding, 5067, tradingDateKey()) !== false ||
    isExecutedOpenMonitorDecision(filledSignals, undefined, 5067, tradingDateKey()) !== false ||
    isExecutedOpenMonitorDecision(null, holding, 5067, tradingDateKey()) !== false ||
    isExecutedOpenMonitorDecision(ghostSignals, holding, 5067, tradingDateKey()) !== false ||
    isExecutedOpenMonitorDecision(syncFill, holding, 5067, tradingDateKey()) !== false ||
    isExecutedOpenMonitorDecision(
      syncGhostFill,
      holding,
      5067,
      "2026-08-09",
    ) !== false
  ) {
    throw new Error("isExecutedOpenMonitorDecision must require APEX execute fills matching broker avg");
  }

  const brokerPnl = computeBrokerOpenPnl(1, 5058.7, holding);
  if (Math.abs(brokerPnl.pnl - 39.5) > 0.01 || Math.abs(brokerPnl.ltp - 5058.7) > 0.01) {
    throw new Error("computeBrokerOpenPnl must prefer broker net-position pnl when present");
  }

  const syncGhostContext: SyncHoldContext = {
    symbols: new Set(["GRASIM"]),
    orderIds: new Set(),
  };
  if (
    isManualSyncMonitorGhost(
      "GRASIM",
      { ...filledSignals, apex_executed: undefined },
      syncGhostContext,
      { created_at: `${tradingDateKey()}T08:00:00.000Z`, decision_date: tradingDateKey() },
    ) !== true
  ) {
    throw new Error("isManualSyncMonitorGhost must exclude symbols with sync hold imports today");
  }
}
