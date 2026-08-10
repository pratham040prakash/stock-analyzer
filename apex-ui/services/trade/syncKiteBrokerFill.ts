import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { normalizeSymbol } from "@/lib/stockPool";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";
import {
  getBrokerFillToday,
  type BrokerFillToday,
} from "@/services/trade/logTradeFill";
import { syncBrokerActivityFromKite } from "@/services/trade/syncBrokerActivity";

type Client = SupabaseClient<Database>;

/** Import today's Kite trades for one symbol, then return fill status. */
export async function syncBrokerFillFromKiteTrades(
  supabase: Client,
  userId: string,
  stock: string,
  dateKey = tradingDateKey(),
): Promise<BrokerFillToday> {
  const existing = await getBrokerFillToday(supabase, userId, stock, dateKey);
  if (existing.filled) {
    return existing;
  }

  const normalized = normalizeSymbol(stock);
  if (!normalized) {
    return { filled: false };
  }

  const activity = await syncBrokerActivityFromKite(supabase, userId, dateKey);
  if (activity.status !== "OK") {
    return { filled: false };
  }

  return getBrokerFillToday(supabase, userId, normalized, dateKey);
}

export { runSyncBrokerActivitySelfCheck as runSyncKiteBrokerFillSelfCheck } from "@/services/trade/syncBrokerActivity";
