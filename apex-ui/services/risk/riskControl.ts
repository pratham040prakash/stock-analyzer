import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import type { MarketTrend } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export const MAX_DAILY_TRADES = 3;
export const MAX_DAILY_LOSS_PCT = 0.02;
export const STOP_LOSS_MULTIPLIER = 0.95;
export const BEAR_MODE_SIZE_FACTOR = 0.5;

export type RiskPosition = {
  stopLoss: number;
};

export type RiskCheckContext = {
  userId: string;
  amount: number;
  portfolioValue: number;
  marketTrend?: MarketTrend;
};

export type RiskCheckResult = {
  allowed: boolean;
  reason?: string;
};

export function computeStopLoss(entryPrice: number): number {
  return entryPrice * STOP_LOSS_MULTIPLIER;
}

export function checkStopLoss(
  position: RiskPosition,
  currentPrice: number,
): boolean {
  return currentPrice <= position.stopLoss;
}

export function applyBearModeAmount(
  amount: number,
  marketTrend?: MarketTrend,
): number {
  if (marketTrend === "bearish") {
    return Math.round(amount * BEAR_MODE_SIZE_FACTOR);
  }
  return amount;
}

async function countTodayTrades(
  supabase: Client,
  userId: string,
): Promise<number> {
  const today = tradingDateKey();

  const { count, error } = await supabase
    .from("decision_memory")
    .select("id", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("decision_date", today)
    .eq("action", "buy");

  if (error) {
    return 0;
  }

  return count ?? 0;
}

async function getTodayRealizedPnl(
  supabase: Client,
  userId: string,
): Promise<number> {
  const today = tradingDateKey();

  const { data, error } = await supabase
    .from("decision_memory")
    .select("pnl")
    .eq("user_id", userId)
    .eq("decision_date", today)
    .not("pnl", "is", null);

  if (error || !data) {
    return 0;
  }

  return data.reduce((sum, row) => sum + Number(row.pnl ?? 0), 0);
}

export async function runRiskChecks(
  supabase: Client,
  context: RiskCheckContext,
): Promise<RiskCheckResult> {
  const { userId, amount, portfolioValue } = context;

  if (amount <= 0) {
    return { allowed: false, reason: "Trade amount must be positive" };
  }

  const tradeCount = await countTodayTrades(supabase, userId);
  if (tradeCount >= MAX_DAILY_TRADES) {
    return {
      allowed: false,
      reason: `Daily trade limit reached (${MAX_DAILY_TRADES} trades)`,
    };
  }

  if (portfolioValue > 0) {
    const todayPnl = await getTodayRealizedPnl(supabase, userId);
    const lossLimit = portfolioValue * MAX_DAILY_LOSS_PCT;

    if (todayPnl < 0 && Math.abs(todayPnl) >= lossLimit) {
      return {
        allowed: false,
        reason: `Daily loss limit reached (${MAX_DAILY_LOSS_PCT * 100}% of portfolio)`,
      };
    }
  }

  return { allowed: true };
}

export async function runRiskChecksSafe(
  supabase: Client,
  context: RiskCheckContext,
): Promise<RiskCheckResult> {
  try {
    return await runRiskChecks(supabase, context);
  } catch (error) {
    console.error("Risk checks failed:", error);
    return {
      allowed: false,
      reason: "Risk checks unavailable — trade blocked for safety",
    };
  }
}
