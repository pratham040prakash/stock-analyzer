import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { computeStopLoss } from "@/services/risk/riskControl";
import { fetchStockData } from "@/services/market/stockData";
import type {
  DailyDecisionOutput,
  MarketTrend,
  PortfolioSnapshotInput,
  Signals,
} from "@/types/decision";
import type { Intent } from "@/types/intent";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type DecisionLogContext = {
  userId: string;
  marketTrend?: MarketTrend;
  portfolioSnapshot?: PortfolioSnapshotInput;
  entryPrice?: number;
  intent?: Intent;
};

export type DecisionMemoryOutcome = {
  id: string;
  exitPrice: number;
  pnl: number;
  success: boolean;
};

function signalsForDecision(decision: DailyDecisionOutput): Signals | null {
  if (!decision.picks?.length) {
    return null;
  }

  if (decision.stock) {
    const matched = decision.picks.find((pick) => pick.stock === decision.stock);
    if (matched) {
      return matched.signals;
    }
  }

  return decision.picks[0]?.signals ?? null;
}

async function resolveEntryPrice(
  stock: string | undefined,
  entryPrice?: number,
): Promise<number | null> {
  if (entryPrice !== undefined && entryPrice > 0) {
    return entryPrice;
  }

  if (!stock) {
    return null;
  }

  try {
    const data = await fetchStockData(stock);
    if (!data.prices.length) {
      return null;
    }
    return data.prices[data.prices.length - 1];
  } catch {
    return null;
  }
}

export async function logDecision(
  supabase: Client,
  decision: DailyDecisionOutput,
  context: DecisionLogContext,
): Promise<string | null> {
  const entryPrice = await resolveEntryPrice(decision.stock, context.entryPrice);
  const signals = signalsForDecision(decision);
  const isBuy = decision.action === "buy";
  const stopLoss =
    isBuy && entryPrice && entryPrice > 0
      ? computeStopLoss(entryPrice)
      : null;
  const quantity =
    isBuy && entryPrice && entryPrice > 0 && decision.amount
      ? Math.floor(decision.amount / entryPrice)
      : null;

  if (isBuy && decision.stock) {
    const today = tradingDateKey();
    const { data: existing } = await supabase
      .from("decision_memory")
      .select("id")
      .eq("user_id", context.userId)
      .eq("decision_date", today)
      .eq("action", "buy")
      .eq("stock", decision.stock)
      .maybeSingle();

    if (existing?.id) {
      return existing.id;
    }
  }

  const { data, error } = await supabase
    .from("decision_memory")
    .insert({
      user_id: context.userId,
      timestamp_ms: Date.now(),
      decision_date: tradingDateKey(),
      intent: context.intent ?? decision.intent ?? null,
      stock: decision.stock ?? null,
      action: decision.action,
      amount: decision.amount ?? null,
      confidence: decision.confidence,
      signals,
      market_trend: context.marketTrend ?? null,
      portfolio_snapshot: context.portfolioSnapshot ?? null,
      entry_price: entryPrice,
      stop_loss: stopLoss,
      quantity,
    })
    .select("id")
    .single();

  if (error || !data) {
    throw new Error(error?.message ?? "Failed to log decision memory");
  }

  return data.id;
}

/** Non-blocking wrapper — never throws. */
export async function logDecisionSafe(
  supabase: Client,
  decision: DailyDecisionOutput,
  context: DecisionLogContext,
): Promise<string | null> {
  try {
    return await logDecision(supabase, decision, context);
  } catch (error) {
    console.error("Decision memory log failed:", error);
    return null;
  }
}

export async function updateStopLoss(
  supabase: Client,
  id: string,
  stopLoss: number,
): Promise<boolean> {
  const { error } = await supabase
    .from("decision_memory")
    .update({
      stop_loss: stopLoss,
      updated_at: new Date().toISOString(),
    })
    .eq("id", id);

  return !error;
}

export async function updatePositionSignals(
  supabase: Client,
  id: string,
  signals: Signals,
): Promise<boolean> {
  const { error } = await supabase
    .from("decision_memory")
    .update({
      signals,
      updated_at: new Date().toISOString(),
    })
    .eq("id", id);

  return !error;
}

export async function updatePositionAfterPartialExit(
  supabase: Client,
  id: string,
  remainingQuantity: number,
  currentPrice: number,
): Promise<boolean> {
  const { error } = await supabase
    .from("decision_memory")
    .update({
      quantity: remainingQuantity,
      take_profit_taken: true,
      updated_at: new Date().toISOString(),
    })
    .eq("id", id);

  if (error) {
    return false;
  }

  console.log("Partial take-profit recorded:", {
    id,
    remainingQuantity,
    price: currentPrice,
  });

  return true;
}

export async function updateDecisionOutcome(
  supabase: Client,
  id: string,
  currentPrice: number,
): Promise<DecisionMemoryOutcome | null> {
  try {
    const { data, error } = await supabase
      .from("decision_memory")
      .select("entry_price, quantity, amount")
      .eq("id", id)
      .maybeSingle();

    if (error || !data?.entry_price) {
      return null;
    }

    const entryPrice = Number(data.entry_price);
    let quantity = Number(data.quantity ?? 0);

    if (quantity < 1 && data.amount && entryPrice > 0) {
      quantity = Math.floor(Number(data.amount) / entryPrice);
    }

    if (quantity < 1) {
      quantity = 1;
    }

    const pnl = (currentPrice - entryPrice) * quantity;
    const success = pnl > 0;

    const { error: updateError } = await supabase
      .from("decision_memory")
      .update({
        exit_price: currentPrice,
        pnl,
        success,
        updated_at: new Date().toISOString(),
      })
      .eq("id", id);

    if (updateError) {
      return null;
    }

    return {
      id,
      exitPrice: currentPrice,
      pnl,
      success,
    };
  } catch (error) {
    console.error("Decision memory outcome update failed:", error);
    return null;
  }
}

export async function getOpenDecisionMemory(
  supabase: Client,
  userId: string,
  stock?: string,
): Promise<{ id: string; stock: string | null; entry_price: number | null }[]> {
  let query = supabase
    .from("decision_memory")
    .select("id, stock, entry_price")
    .eq("user_id", userId)
    .is("exit_price", null)
    .order("created_at", { ascending: false })
    .limit(20);

  if (stock) {
    query = query.eq("stock", stock);
  }

  const { data, error } = await query;

  if (error || !data) {
    return [];
  }

  return data;
}

export async function getOpenStopLossPositions(
  supabase: Client,
): Promise<
  {
    id: string;
    user_id: string;
    stock: string;
    entry_price: number | null;
    stop_loss: number | null;
    amount: number | null;
    quantity: number | null;
    take_profit_taken: boolean;
  }[]
> {
  const { data, error } = await supabase
    .from("decision_memory")
    .select(
      "id, user_id, stock, entry_price, stop_loss, amount, quantity, take_profit_taken",
    )
    .is("exit_price", null)
    .eq("action", "buy")
    .not("stop_loss", "is", null)
    .not("stock", "is", null)
    .order("created_at", { ascending: false })
    .limit(500);

  if (error || !data) {
    return [];
  }

  return data.map((row) => ({
    ...row,
    stock: row.stock as string,
  }));
}

export async function getAllOpenDecisionMemory(
  supabase: Client,
): Promise<
  { id: string; user_id: string; stock: string | null; entry_price: number | null }[]
> {
  const { data, error } = await supabase
    .from("decision_memory")
    .select("id, user_id, stock, entry_price")
    .is("exit_price", null)
    .not("stock", "is", null)
    .order("created_at", { ascending: false })
    .limit(500);

  if (error || !data) {
    return [];
  }

  return data;
}
