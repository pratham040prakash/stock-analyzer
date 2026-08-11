import type { InvestmentThesisInput, InvestmentThesisRow } from "@/types/investmentThesis";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

type ThesisRecord = {
  id: string;
  symbol: string;
  thesis: string;
  invalidation: string | null;
  updated_at: string;
};

export async function listInvestmentTheses(
  supabase: Client,
  userId: string,
): Promise<InvestmentThesisRow[]> {
  const { data, error } = await supabase
    .from("investment_thesis")
    .select("id, symbol, thesis, invalidation, updated_at")
    .eq("user_id", userId)
    .order("updated_at", { ascending: false });

  if (error) {
    throw new Error(error.message);
  }

  return (data as ThesisRecord[] | null)?.map((row) => ({
    id: row.id,
    symbol: row.symbol,
    thesis: row.thesis,
    invalidation: row.invalidation,
    updated_at: row.updated_at,
  })) ?? [];
}

export async function upsertInvestmentThesis(
  supabase: Client,
  userId: string,
  input: InvestmentThesisInput,
): Promise<InvestmentThesisRow | null> {
  const symbol = input.symbol.trim().toUpperCase();
  const thesis = input.thesis.trim();

  if (!symbol || !thesis) {
    return null;
  }

  const { data, error } = await supabase
    .from("investment_thesis")
    .upsert(
      {
        user_id: userId,
        symbol,
        thesis,
        invalidation: input.invalidation?.trim() || null,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "user_id,symbol" },
    )
    .select("id, symbol, thesis, invalidation, updated_at")
    .single();

  if (error) {
    throw new Error(error.message);
  }

  return data as InvestmentThesisRow;
}

export function runThesisRepositorySelfCheck(): void {
  const symbol = "RELIANCE".trim().toUpperCase();

  if (symbol !== "RELIANCE") {
    throw new Error("Thesis repository self-check failed");
  }
}
