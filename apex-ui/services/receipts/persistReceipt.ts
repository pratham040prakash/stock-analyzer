import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import type { MorningBriefViewModel } from "@/types/morningBrief";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export type PersistReceiptInput = {
  symbol: string;
  executionKind: "BUY" | "SELL" | "WAIT" | "OBSERVE";
  verdictWord?: string;
  headline?: string;
  subline?: string;
  trustScore?: number;
  trustDelta?: number;
  orderId?: string;
  fillSide?: "buy" | "sell";
  fillQuantity?: number;
  fillPrice?: number;
  fillAmount?: number;
  decisionMemoryId?: string | null;
  briefSnapshot?: MorningBriefViewModel | null;
};

export type DecisionReceiptRow = {
  id: string;
  receipt_date: string;
  symbol: string;
  execution_kind: string;
  verdict_word: string | null;
  headline: string | null;
  subline: string | null;
  trust_score: number | null;
  trust_delta: number | null;
  order_id: string | null;
  fill_side: string | null;
  fill_quantity: number | null;
  fill_price: number | null;
  fill_amount: number | null;
  brief_snapshot: unknown;
  dismissed_at: string | null;
  created_at: string;
};

export async function persistDecisionReceipt(
  supabase: Client,
  userId: string,
  input: PersistReceiptInput,
): Promise<DecisionReceiptRow | null> {
  const receiptDate = tradingDateKey();
  const normalized = input.symbol.trim().toUpperCase();

  if (!normalized) {
    return null;
  }

  const { data, error } = await supabase
    .from("decision_receipts")
    .insert({
      user_id: userId,
      receipt_date: receiptDate,
      symbol: normalized,
      execution_kind: input.executionKind,
      verdict_word: input.verdictWord ?? null,
      headline: input.headline ?? null,
      subline: input.subline ?? null,
      trust_score: input.trustScore ?? null,
      trust_delta: input.trustDelta ?? null,
      order_id: input.orderId ?? null,
      fill_side: input.fillSide ?? null,
      fill_quantity: input.fillQuantity ?? null,
      fill_price: input.fillPrice ?? null,
      fill_amount: input.fillAmount ?? null,
      decision_memory_id: input.decisionMemoryId ?? null,
      brief_snapshot: input.briefSnapshot ?? null,
    })
    .select("*")
    .maybeSingle();

  if (error) {
    if (error.code === "23505") {
      const { data: existing } = await supabase
        .from("decision_receipts")
        .select("*")
        .eq("user_id", userId)
        .eq("receipt_date", receiptDate)
        .eq("symbol", normalized)
        .eq("order_id", input.orderId ?? "")
        .maybeSingle();

      return (existing as DecisionReceiptRow | null) ?? null;
    }

    return null;
  }

  return (data as DecisionReceiptRow | null) ?? null;
}

export async function listDecisionReceipts(
  supabase: Client,
  userId: string,
  days = 30,
): Promise<DecisionReceiptRow[]> {
  const since = new Date();
  since.setDate(since.getDate() - Math.max(1, days));

  const { data, error } = await supabase
    .from("decision_receipts")
    .select("*")
    .eq("user_id", userId)
    .gte("receipt_date", since.toISOString().slice(0, 10))
    .order("created_at", { ascending: false })
    .limit(100);

  if (error || !data) {
    return [];
  }

  return data as DecisionReceiptRow[];
}

export async function dismissDecisionReceipt(
  supabase: Client,
  userId: string,
  receiptId: string,
): Promise<boolean> {
  const { error } = await supabase
    .from("decision_receipts")
    .update({ dismissed_at: new Date().toISOString() })
    .eq("id", receiptId)
    .eq("user_id", userId);

  return !error;
}

export async function persistDisciplineWaitReceipt(
  supabase: Client,
  userId: string,
  input: {
    symbol?: string;
    action: string;
    intent: string;
    commitDate: string;
    streakCount?: number;
  },
): Promise<DecisionReceiptRow | null> {
  const symbol = (input.symbol?.trim() || "SESSION").toUpperCase();
  const executionKind =
    input.action.toLowerCase().includes("wait") ||
    input.action.toLowerCase().includes("hold") ||
    input.intent === "protect"
      ? "WAIT"
      : "OBSERVE";

  return persistDecisionReceipt(supabase, userId, {
    symbol,
    executionKind,
    verdictWord: executionKind,
    headline: `Followed today's ${executionKind.toLowerCase()} plan`,
    subline: `Discipline commit · ${input.action}`,
    orderId: `discipline:${input.commitDate}:${symbol}`,
  });
}

export function runReceiptSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Receipt self-check failed: ${message}`);
    }
  };

  assert(tradingDateKey().length === 10, "Receipt date key must be YYYY-MM-DD");
}
