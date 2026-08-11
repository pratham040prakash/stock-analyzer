import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { computeStopLoss } from "@/services/risk/riskControl";
import type { Signals } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type TradeFillInput = {
  stock: string;
  side: "buy" | "sell";
  price: number;
  quantity: number;
  amount: number;
  orderId: string;
  fillSource?: "execute" | "sync";
  autoExecuted?: boolean;
};

function fillSignals(
  orderId: string,
  price: number,
  fillSource: "execute" | "sync" = "execute",
  autoExecuted = false,
): Signals {
  return {
    trend: 0,
    momentum: 0,
    volume: 0,
    order_id: orderId,
    fill_price: price,
    filled_at: new Date().toISOString(),
    monitored: fillSource === "execute",
    fill_source: fillSource,
    apex_executed: fillSource === "execute" ? true : undefined,
    auto_executed: autoExecuted ? true : undefined,
  };
}

/** Record a sync-imported order without attaching to an open APEX buy decision. */
async function logSyncOnlyBrokerFill(
  supabase: Client,
  userId: string,
  fill: TradeFillInput,
): Promise<string | null> {
  const today = tradingDateKey();

  const { data, error } = await supabase
    .from("decision_memory")
    .insert({
      user_id: userId,
      timestamp_ms: Date.now(),
      decision_date: today,
      stock: fill.stock,
      action: "hold",
      amount: fill.amount,
      confidence: 0,
      entry_price: fill.price,
      quantity: fill.quantity,
      signals: fillSignals(fill.orderId, fill.price, "sync"),
    })
    .select("id")
    .single();

  if (error || !data) {
    return null;
  }

  return data.id;
}

export function signalsIndicateBrokerFill(signals: Signals | null | undefined): boolean {
  return Boolean(signals?.order_id && signals?.filled_at);
}

export function signalsIndicateApexExecution(
  signals: Signals | null | undefined,
): boolean {
  return Boolean(signals?.apex_executed || signals?.auto_executed);
}

export type BrokerFillSummary = {
  orderId: string;
  quantity: number;
  side: "buy" | "sell";
  price?: number;
};

export type BrokerFillToday = {
  filled: boolean;
  orderId?: string;
  quantity?: number;
  side?: "buy" | "sell";
  price?: number;
};

export function describeBrokerFill(
  fill: BrokerFillSummary,
  symbol: string,
): string {
  const sideLabel = fill.side === "sell" ? "Sold" : "Bought";
  const shareLabel = fill.quantity === 1 ? "share" : "shares";
  const pricePart =
    fill.price !== undefined && Number.isFinite(fill.price)
      ? ` at ₹${fill.price.toLocaleString("en-IN")}`
      : "";

  return `${sideLabel} ${fill.quantity} ${shareLabel} of ${symbol}${pricePart}. Order ${fill.orderId}.`;
}

async function logStandaloneSellFill(
  supabase: Client,
  userId: string,
  fill: TradeFillInput,
): Promise<string | null> {
  const today = tradingDateKey();

  const { data, error } = await supabase
    .from("decision_memory")
    .insert({
      user_id: userId,
      timestamp_ms: Date.now(),
      decision_date: today,
      stock: fill.stock,
      action: "sell",
      amount: fill.amount,
      confidence: 75,
      entry_price: fill.price,
      exit_price: fill.price,
      quantity: fill.quantity,
      take_profit_taken: true,
      signals: fillSignals(fill.orderId, fill.price, fill.fillSource ?? "execute"),
    })
    .select("id")
    .single();

  if (error || !data) {
    return null;
  }

  return data.id;
}

export async function getBrokerFillToday(
  supabase: Client,
  userId: string,
  stock: string,
  dateKey = tradingDateKey(),
): Promise<BrokerFillToday> {
  const normalized = stock.trim().toUpperCase();

  if (!normalized) {
    return { filled: false };
  }

  const { data, error } = await supabase
    .from("decision_memory")
    .select("action, quantity, entry_price, exit_price, signals")
    .eq("user_id", userId)
    .eq("stock", normalized)
    .eq("decision_date", dateKey)
    .order("updated_at", { ascending: false })
    .limit(10);

  if (error || !data?.length) {
    return { filled: false };
  }

  for (const row of data) {
    const signals = row.signals as Signals | null;

    if (!signalsIndicateBrokerFill(signals)) {
      continue;
    }

    const side: "buy" | "sell" = row.action === "sell" ? "sell" : "buy";
    const price =
      side === "sell"
        ? (row.exit_price ?? signals?.fill_price ?? row.entry_price ?? undefined)
        : (signals?.fill_price ?? row.entry_price ?? undefined);

    return {
      filled: true,
      orderId: signals?.order_id,
      quantity: row.quantity ?? undefined,
      side,
      price: price ?? undefined,
    };
  }

  return { filled: false };
}

/** Broker fills initiated by APEX (execute button or auto-trade). */
export async function getApexBrokerFillToday(
  supabase: Client,
  userId: string,
  stock: string,
  dateKey = tradingDateKey(),
): Promise<BrokerFillToday> {
  const normalized = stock.trim().toUpperCase();

  if (!normalized) {
    return { filled: false };
  }

  const { data, error } = await supabase
    .from("decision_memory")
    .select("action, quantity, entry_price, exit_price, signals")
    .eq("user_id", userId)
    .eq("stock", normalized)
    .eq("decision_date", dateKey)
    .order("updated_at", { ascending: false })
    .limit(10);

  if (error || !data?.length) {
    return { filled: false };
  }

  for (const row of data) {
    const signals = row.signals as Signals | null;

    if (!signalsIndicateBrokerFill(signals) || !signalsIndicateApexExecution(signals)) {
      continue;
    }

    const side: "buy" | "sell" = row.action === "sell" ? "sell" : "buy";
    const price =
      side === "sell"
        ? (row.exit_price ?? signals?.fill_price ?? row.entry_price ?? undefined)
        : (signals?.fill_price ?? row.entry_price ?? undefined);

    return {
      filled: true,
      orderId: signals?.order_id,
      quantity: row.quantity ?? undefined,
      side,
      price: price ?? undefined,
    };
  }

  return { filled: false };
}

/** Order IDs already logged in decision_memory for the trading day. */
export async function getLoggedBrokerOrderIdsToday(
  supabase: Client,
  userId: string,
  dateKey = tradingDateKey(),
): Promise<Set<string>> {
  const { data, error } = await supabase
    .from("decision_memory")
    .select("signals")
    .eq("user_id", userId)
    .eq("decision_date", dateKey);

  if (error || !data?.length) {
    return new Set();
  }

  const orderIds = new Set<string>();

  for (const row of data) {
    const signals = row.signals as Signals | null;
    if (signals?.order_id) {
      orderIds.add(String(signals.order_id));
    }
  }

  return orderIds;
}

export async function hasBrokerFillToday(
  supabase: Client,
  userId: string,
  stock: string,
  dateKey = tradingDateKey(),
): Promise<boolean> {
  const fill = await getBrokerFillToday(supabase, userId, stock, dateKey);
  return fill.filled;
}

export async function logTradeFill(
  supabase: Client,
  userId: string,
  fill: TradeFillInput,
): Promise<string | null> {
  if (fill.side === "buy") {
    if (fill.fillSource === "sync") {
      return logSyncOnlyBrokerFill(supabase, userId, fill);
    }

    const stopLoss = computeStopLoss(fill.price);
    const today = tradingDateKey();

    const { data: existing } = await supabase
      .from("decision_memory")
      .select("id")
      .eq("user_id", userId)
      .eq("stock", fill.stock)
      .eq("action", "buy")
      .is("exit_price", null)
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();

    if (existing?.id) {
      const { error } = await supabase
        .from("decision_memory")
        .update({
          entry_price: fill.price,
          quantity: fill.quantity,
          amount: fill.amount,
          stop_loss: stopLoss,
          signals: fillSignals(
            fill.orderId,
            fill.price,
            fill.fillSource ?? "execute",
            fill.autoExecuted ?? false,
          ),
          decision_date: today,
          updated_at: new Date().toISOString(),
        })
        .eq("id", existing.id);

      return error ? null : existing.id;
    }

    const { data, error } = await supabase
      .from("decision_memory")
      .insert({
        user_id: userId,
        timestamp_ms: Date.now(),
        decision_date: today,
        stock: fill.stock,
        action: "buy",
        amount: fill.amount,
        confidence: 75,
        entry_price: fill.price,
        stop_loss: stopLoss,
        quantity: fill.quantity,
        signals: fillSignals(
          fill.orderId,
          fill.price,
          fill.fillSource ?? "execute",
          fill.autoExecuted ?? false,
        ),
      })
      .select("id")
      .single();

    if (error || !data) {
      return null;
    }

    return data.id;
  }

  const { data: open } = await supabase
    .from("decision_memory")
    .select("id, quantity, entry_price")
    .eq("user_id", userId)
    .eq("stock", fill.stock)
    .eq("action", "buy")
    .is("exit_price", null)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (!open?.id) {
    return logStandaloneSellFill(supabase, userId, fill);
  }

  const priorQty = Math.max(0, Math.round(Number(open.quantity ?? 0)));
  const remainingQty = Math.max(0, priorQty - fill.quantity);
  const entryPrice = Number(open.entry_price ?? fill.price);

  if (remainingQty > 0) {
    const { error } = await supabase
      .from("decision_memory")
      .update({
        quantity: remainingQty,
        take_profit_taken: true,
        signals: fillSignals(fill.orderId, fill.price, fill.fillSource ?? "execute"),
        updated_at: new Date().toISOString(),
      })
      .eq("id", open.id);

    return error ? null : open.id;
  }

  const pnl = (fill.price - entryPrice) * Math.max(fill.quantity, priorQty || fill.quantity);
  const { error } = await supabase
    .from("decision_memory")
    .update({
      exit_price: fill.price,
      quantity: 0,
      pnl,
      success: pnl > 0,
      signals: fillSignals(fill.orderId, fill.price, fill.fillSource ?? "execute"),
      updated_at: new Date().toISOString(),
    })
    .eq("id", open.id);

  return error ? null : open.id;
}

export async function logTradeFillSafe(
  supabase: Client,
  userId: string,
  fill: TradeFillInput,
): Promise<string | null> {
  try {
    return await logTradeFill(supabase, userId, fill);
  } catch (error) {
    console.error("Trade fill log failed:", error);
    return null;
  }
}

export function runTradeFillSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Trade fill self-check failed: ${message}`);
    }
  };

  assert(
    signalsIndicateBrokerFill({
      trend: 0,
      momentum: 0,
      volume: 0,
      order_id: "123",
      filled_at: "2026-08-10T09:00:00.000Z",
    }),
    "Fill signals must include order id and timestamp",
  );
  assert(
    !signalsIndicateBrokerFill({ trend: 1, momentum: 1, volume: 1 }),
    "Missing fill metadata must not count as broker fill",
  );

  const executeSignals = fillSignals("111", 100, "execute");
  assert(
    executeSignals.monitored === true && executeSignals.apex_executed === true,
    "Execute fills must be monitored and apex_executed",
  );

  const syncSignals = fillSignals("222", 100, "sync");
  assert(
    syncSignals.monitored === false &&
      syncSignals.fill_source === "sync" &&
      syncSignals.apex_executed === undefined,
    "Sync fills must not be monitored",
  );

  const detail = describeBrokerFill(
    { orderId: "240810000123456", quantity: 5, side: "sell", price: 312.5 },
    "JIOFIN",
  );
  assert(
    detail.includes("240810000123456") && detail.includes("JIOFIN"),
    "Broker fill detail must include order id and symbol",
  );

  assert(
    signalsIndicateApexExecution({
      trend: 0,
      momentum: 0,
      volume: 0,
      apex_executed: true,
      order_id: "1",
      filled_at: "2026-08-10T09:00:00.000Z",
    }),
    "Apex execution signals must be detected",
  );
  assert(
    !signalsIndicateApexExecution({
      trend: 0,
      momentum: 0,
      volume: 0,
      fill_source: "sync",
      order_id: "2",
      filled_at: "2026-08-10T09:00:00.000Z",
    }),
    "Sync-only fills must not count as apex execution",
  );
}
