import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { normalizeSymbol } from "@/lib/stockPool";
import { isAutoTradingEnabled } from "@/lib/tradingPreferences";
import { executeTradeSafe } from "@/services/trade/execute";
import {
  hasBrokerFillToday,
  logTradeFillSafe,
} from "@/services/trade/logTradeFill";
import type { DailyDecisionOutput, MarketTrend, Signals } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type AutoTradeContext = {
  portfolioValue?: number;
  marketTrend?: MarketTrend;
};

export type AutoTradeSkipReason =
  | "auto_disabled"
  | "not_buy"
  | "already_attempted"
  | "already_filled";

export type AutoTradeSkipChecks = {
  autoEnabled: boolean;
  isBuy: boolean;
  autoAttemptedToday: boolean;
  brokerFillToday: boolean;
};

export function shouldSkipAutoTrade(checks: AutoTradeSkipChecks): AutoTradeSkipReason | null {
  if (!checks.autoEnabled) {
    return "auto_disabled";
  }

  if (!checks.isBuy) {
    return "not_buy";
  }

  if (checks.autoAttemptedToday) {
    return "already_attempted";
  }

  if (checks.brokerFillToday) {
    return "already_filled";
  }

  return null;
}

async function hasAutoTradeAttemptToday(
  supabase: Client,
  userId: string,
  dateKey = tradingDateKey(),
): Promise<boolean> {
  const { data, error } = await supabase
    .from("decision_memory")
    .select("signals")
    .eq("user_id", userId)
    .eq("decision_date", dateKey);

  if (error || !data?.length) {
    return false;
  }

  for (const row of data) {
    const signals = row.signals as Signals | null;
    if (signals?.auto_trade_attempted || signals?.auto_executed) {
      return true;
    }
  }

  return false;
}

async function recordAutoTradeAttempt(
  supabase: Client,
  userId: string,
  stock: string,
): Promise<void> {
  const today = tradingDateKey();
  const normalized = normalizeSymbol(stock);

  if (!normalized) {
    return;
  }

  const { error } = await supabase.from("decision_memory").insert({
    user_id: userId,
    timestamp_ms: Date.now(),
    decision_date: today,
    stock: normalized,
    action: "hold",
    amount: 0,
    confidence: 0,
    signals: {
      trend: 0,
      momentum: 0,
      volume: 0,
      auto_trade_attempted: true,
      filled_at: new Date().toISOString(),
    } satisfies Signals,
  });

  if (error) {
    console.warn("Auto trade attempt marker failed:", error.message);
  }
}

export async function executeTradeIfAutoEnabled(
  supabase: Client,
  userId: string,
  decision: DailyDecisionOutput,
  context: AutoTradeContext = {},
): Promise<void> {
  try {
    const autoEnabled = await isAutoTradingEnabled(supabase, userId);
    const isBuy =
      decision.action === "buy" &&
      Boolean(decision.stock) &&
      Boolean(decision.amount) &&
      (decision.amount ?? 0) > 0;

    const stock = decision.stock ? normalizeSymbol(decision.stock) : "";
    const autoAttemptedToday = await hasAutoTradeAttemptToday(supabase, userId);
    const brokerFillToday = stock
      ? await hasBrokerFillToday(supabase, userId, stock)
      : false;

    const skipReason = shouldSkipAutoTrade({
      autoEnabled,
      isBuy,
      autoAttemptedToday,
      brokerFillToday,
    });

    if (skipReason) {
      if (skipReason !== "auto_disabled" && skipReason !== "not_buy") {
        console.log("Auto trade skipped:", skipReason, stock || decision.stock);
      }
      return;
    }

    if (!stock || !decision.amount) {
      return;
    }

    await recordAutoTradeAttempt(supabase, userId, stock);

    const result = await executeTradeSafe(supabase, userId, {
      stock,
      amount: decision.amount,
      portfolioValue: context.portfolioValue,
      marketTrend: context.marketTrend,
    });

    if (result?.status === "OK") {
      await logTradeFillSafe(supabase, userId, {
        stock: result.stock,
        side: "buy",
        price: result.price,
        quantity: result.quantity,
        amount: result.amount,
        orderId: result.orderId,
        autoExecuted: true,
      });
      console.log("Auto trade executed:", result);
      return;
    }

    if (result) {
      console.warn("Auto trade skipped:", result);
    }
  } catch (error) {
    console.error("Auto trade hook failed:", error);
  }
}

export function runAutoTradeSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Auto trade self-check failed: ${message}`);
    }
  };

  assert(
    shouldSkipAutoTrade({
      autoEnabled: false,
      isBuy: true,
      autoAttemptedToday: false,
      brokerFillToday: false,
    }) === "auto_disabled",
    "Disabled auto trading must skip",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: false,
      autoAttemptedToday: false,
      brokerFillToday: false,
    }) === "not_buy",
    "Non-buy decisions must skip auto trade",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: true,
      autoAttemptedToday: true,
      brokerFillToday: false,
    }) === "already_attempted",
    "Prior auto attempt today must skip",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: true,
      autoAttemptedToday: false,
      brokerFillToday: true,
    }) === "already_filled",
    "Existing broker fill today must skip",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: true,
      autoAttemptedToday: false,
      brokerFillToday: false,
    }) === null,
    "Fresh buy with auto enabled must not skip",
  );
}
