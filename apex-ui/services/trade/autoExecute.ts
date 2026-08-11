import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { logger } from "@/lib/logging/logger";
import { normalizeSymbol } from "@/lib/stockPool";
import { isAutoTradingEnabled } from "@/lib/tradingPreferences";
import { executeTradeSafe } from "@/services/trade/execute";
import type { ExecuteTradeResult } from "@/services/trade/execute";
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
  | "already_executed"
  | "already_filled"
  | "in_flight";

export type AutoTradeSkipChecks = {
  autoEnabled: boolean;
  isBuy: boolean;
  autoExecutedToday: boolean;
  autoInFlight: boolean;
  brokerFillToday: boolean;
};

export function shouldSkipAutoTrade(checks: AutoTradeSkipChecks): AutoTradeSkipReason | null {
  if (!checks.autoEnabled) {
    return "auto_disabled";
  }

  if (!checks.isBuy) {
    return "not_buy";
  }

  if (checks.autoExecutedToday) {
    return "already_executed";
  }

  if (checks.brokerFillToday) {
    return "already_filled";
  }

  if (checks.autoInFlight) {
    return "in_flight";
  }

  return null;
}

function isRetryableAutoTradeFailure(result: ExecuteTradeResult | null | undefined): boolean {
  if (!result) {
    return true;
  }

  return (
    result.status === "ENTRY_BLOCKED" ||
    result.status === "ERROR" ||
    result.status === "INSUFFICIENT_FUNDS" ||
    result.status === "RISK_BLOCKED"
  );
}

async function listAutoTradeSignalsToday(
  supabase: Client,
  userId: string,
  dateKey = tradingDateKey(),
): Promise<Signals[]> {
  const { data, error } = await supabase
    .from("decision_memory")
    .select("signals")
    .eq("user_id", userId)
    .eq("decision_date", dateKey);

  if (error || !data?.length) {
    return [];
  }

  return data
    .map((row) => row.signals as Signals | null)
    .filter((signals): signals is Signals => Boolean(signals));
}

export async function hasAutoTradeSucceededToday(
  supabase: Client,
  userId: string,
  dateKey = tradingDateKey(),
): Promise<boolean> {
  const signals = await listAutoTradeSignalsToday(supabase, userId, dateKey);
  return signals.some((entry) => entry.auto_executed === true);
}

export async function hasAutoTradeInFlightToday(
  supabase: Client,
  userId: string,
  dateKey = tradingDateKey(),
): Promise<boolean> {
  const { count, error } = await supabase
    .from("auto_trade_locks")
    .select("user_id", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("trade_date", dateKey);

  if (error) {
    const signals = await listAutoTradeSignalsToday(supabase, userId, dateKey);
    return signals.some(
      (entry) =>
        entry.auto_trade_attempted === true && entry.auto_executed !== true,
    );
  }

  return (count ?? 0) > 0;
}

async function recordAutoTradeAttempt(
  supabase: Client,
  userId: string,
  stock: string,
): Promise<boolean> {
  const today = tradingDateKey();
  const normalized = normalizeSymbol(stock);

  if (!normalized) {
    return false;
  }

  const { error: lockError } = await supabase.from("auto_trade_locks").insert({
    user_id: userId,
    trade_date: today,
    stock: normalized,
  });

  if (lockError) {
    if (lockError.code === "23505") {
      return false;
    }

    logger.warn("auto_trade_lock_insert_failed", {
      route: "autoExecute",
      userId,
      stock: normalized,
      code: lockError.code,
    });
    return false;
  }

  const { error: auditError } = await supabase.from("decision_memory").insert({
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

  if (auditError) {
    logger.warn("auto_trade_audit_insert_failed", {
      route: "autoExecute",
      userId,
      stock: normalized,
      code: auditError.code,
    });
  }

  return true;
}

async function clearAutoTradeAttempt(
  supabase: Client,
  userId: string,
  stock: string,
): Promise<void> {
  const today = tradingDateKey();
  const normalized = normalizeSymbol(stock);

  if (!normalized) {
    return;
  }

  await supabase
    .from("auto_trade_locks")
    .delete()
    .eq("user_id", userId)
    .eq("trade_date", today);

  const { data, error } = await supabase
    .from("decision_memory")
    .select("id, signals")
    .eq("user_id", userId)
    .eq("decision_date", today)
    .eq("stock", normalized)
    .eq("action", "hold");

  if (error || !data?.length) {
    return;
  }

  for (const row of data) {
    const signals = row.signals as Signals | null;
    if (signals?.auto_trade_attempted && !signals?.auto_executed) {
      await supabase.from("decision_memory").delete().eq("id", row.id);
    }
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
    const autoExecutedToday = await hasAutoTradeSucceededToday(supabase, userId);
    const autoInFlight = await hasAutoTradeInFlightToday(supabase, userId);
    const brokerFillToday = stock
      ? await hasBrokerFillToday(supabase, userId, stock)
      : false;

    const skipReason = shouldSkipAutoTrade({
      autoEnabled,
      isBuy,
      autoExecutedToday,
      autoInFlight,
      brokerFillToday,
    });

    if (skipReason) {
      if (skipReason !== "auto_disabled" && skipReason !== "not_buy") {
        logger.info("auto_trade_skipped", {
          route: "autoExecute",
          userId,
          reason: skipReason,
          stock: stock || decision.stock,
        });
      }
      return;
    }

    if (!stock || !decision.amount) {
      return;
    }

    const locked = await recordAutoTradeAttempt(supabase, userId, stock);
    if (!locked) {
      logger.info("auto_trade_skipped", {
        route: "autoExecute",
        userId,
        reason: "in_flight",
        stock,
      });
      return;
    }

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
      logger.info("auto_trade_executed", {
        route: "autoExecute",
        userId,
        stock: result.stock,
        orderId: result.orderId,
        quantity: result.quantity,
      });
      return;
    }

    if (isRetryableAutoTradeFailure(result)) {
      await clearAutoTradeAttempt(supabase, userId, stock);
    }

    if (result) {
      logger.warn("auto_trade_failed", {
        route: "autoExecute",
        userId,
        stock,
        status: result.status,
        reason: "reason" in result ? result.reason : undefined,
      });
    }
  } catch (error) {
    logger.error("auto_trade_hook_failed", {
      route: "autoExecute",
      userId,
      error: error instanceof Error ? error.message : "unknown",
    });
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
      autoExecutedToday: false,
      autoInFlight: false,
      brokerFillToday: false,
    }) === "auto_disabled",
    "Disabled auto trading must skip",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: false,
      autoExecutedToday: false,
      autoInFlight: false,
      brokerFillToday: false,
    }) === "not_buy",
    "Non-buy decisions must skip auto trade",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: true,
      autoExecutedToday: true,
      autoInFlight: false,
      brokerFillToday: false,
    }) === "already_executed",
    "Successful auto trade today must skip",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: true,
      autoExecutedToday: false,
      autoInFlight: false,
      brokerFillToday: true,
    }) === "already_filled",
    "Existing broker fill today must skip",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: true,
      autoExecutedToday: false,
      autoInFlight: true,
      brokerFillToday: false,
    }) === "in_flight",
    "In-flight auto trade must skip duplicate requests",
  );

  assert(
    shouldSkipAutoTrade({
      autoEnabled: true,
      isBuy: true,
      autoExecutedToday: false,
      autoInFlight: false,
      brokerFillToday: false,
    }) === null,
    "Fresh buy with auto enabled must not skip",
  );

  assert(
    isRetryableAutoTradeFailure({ status: "ENTRY_BLOCKED", reason: "Late session" }),
    "Entry blocks must allow retry after clearing attempt marker",
  );
  assert(
    !isRetryableAutoTradeFailure({ status: "OK", stock: "X", amount: 1, price: 1, quantity: 1, orderId: "1" }),
    "Successful orders must not be treated as retryable failures",
  );
}
