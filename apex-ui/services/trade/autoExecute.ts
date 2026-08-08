import { isAutoTradingEnabled } from "@/lib/tradingPreferences";
import { executeTradeSafe } from "@/services/trade/execute";
import type { DailyDecisionOutput, MarketTrend } from "@/types/decision";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type AutoTradeContext = {
  portfolioValue?: number;
  marketTrend?: MarketTrend;
};

export async function executeTradeIfAutoEnabled(
  supabase: Client,
  userId: string,
  decision: DailyDecisionOutput,
  context: AutoTradeContext = {},
): Promise<void> {
  try {
    const autoEnabled = await isAutoTradingEnabled(supabase, userId);

    if (!autoEnabled) {
      return;
    }

    if (
      decision.action !== "buy" ||
      !decision.stock ||
      !decision.amount ||
      decision.amount <= 0
    ) {
      return;
    }

    const result = await executeTradeSafe(supabase, userId, {
      stock: decision.stock,
      amount: decision.amount,
      portfolioValue: context.portfolioValue,
      marketTrend: context.marketTrend,
    });

    if (result?.status === "OK") {
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
