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
};

function utcDateString(date = new Date()): string {
  return date.toISOString().slice(0, 10);
}

function fillSignals(orderId: string, price: number): Signals {
  return {
    trend: 0,
    momentum: 0,
    volume: 0,
    order_id: orderId,
    fill_price: price,
    filled_at: new Date().toISOString(),
    monitored: true,
  } as Signals;
}

export async function logTradeFill(
  supabase: Client,
  userId: string,
  fill: TradeFillInput,
): Promise<string | null> {
  if (fill.side === "buy") {
    const stopLoss = computeStopLoss(fill.price);
    const today = utcDateString();

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
          signals: fillSignals(fill.orderId, fill.price),
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
        signals: fillSignals(fill.orderId, fill.price),
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
    return null;
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
        signals: fillSignals(fill.orderId, fill.price),
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
      signals: fillSignals(fill.orderId, fill.price),
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
