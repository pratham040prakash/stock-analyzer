import type { SupabaseClient } from "@supabase/supabase-js";
import {
  getExpenseMidpoint,
  getIncomeMidpoint,
  type ExpenseRange,
  type FinancialProfile,
  type IncomeRange,
} from "@/lib/financialProfile";
import type { Database } from "@/types/database";
import type { Portfolio } from "@/types/portfolio";

type Client = SupabaseClient<Database>;

export async function savePortfolioSnapshot(
  supabase: Client,
  userId: string,
  portfolio: Portfolio,
  metrics: { totalValue: number; pnl: number },
): Promise<void> {
  const { error } = await supabase.from("portfolio_snapshots").insert({
    user_id: userId,
    holdings: portfolio.holdings,
    total_value: metrics.totalValue,
    pnl: metrics.pnl,
  });

  if (error) {
    throw new Error(error.message);
  }
}

export async function getLatestPortfolioSnapshot(
  supabase: Client,
  userId: string,
): Promise<Portfolio | null> {
  const { data, error } = await supabase
    .from("portfolio_snapshots")
    .select("holdings")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return { holdings: data.holdings };
}

export async function getFinancialProfileFromDb(
  supabase: Client,
  userId: string,
): Promise<FinancialProfile | null> {
  const { data, error } = await supabase
    .from("financial_profiles")
    .select("income_range, expense_range")
    .eq("user_id", userId)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return {
    incomeRange: data.income_range as IncomeRange,
    expenseRange: data.expense_range as ExpenseRange,
  };
}

export async function upsertFinancialProfile(
  supabase: Client,
  userId: string,
  profile: FinancialProfile,
): Promise<void> {
  const investableSurplus = Math.max(
    0,
    getIncomeMidpoint(profile.incomeRange) -
      getExpenseMidpoint(profile.expenseRange),
  );

  const { error } = await supabase.from("financial_profiles").upsert(
    {
      user_id: userId,
      income_range: profile.incomeRange,
      expense_range: profile.expenseRange,
      investable_surplus: investableSurplus,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" },
  );

  if (error) {
    throw new Error(error.message);
  }
}

export async function saveMentorOutput(
  supabase: Client,
  userId: string,
  output: {
    decision: import("@/types/mentorDecision").MentorDecision;
    message: string;
    confidence: "low" | "medium" | "high";
  },
): Promise<void> {
  const { error } = await supabase.from("mentor_outputs").insert({
    user_id: userId,
    decision: output.decision,
    message: output.message,
    confidence: output.confidence,
  });

  if (error) {
    throw new Error(error.message);
  }
}

export async function getLatestPortfolioSnapshotWithMetrics(
  supabase: Client,
  userId: string,
): Promise<{
  portfolio: Portfolio;
  total_value: number;
  pnl: number;
} | null> {
  const { data, error } = await supabase
    .from("portfolio_snapshots")
    .select("holdings, total_value, pnl")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return {
    portfolio: { holdings: data.holdings },
    total_value: Number(data.total_value),
    pnl: Number(data.pnl),
  };
}

export async function getLatestMentorOutput(
  supabase: Client,
  userId: string,
): Promise<import("@/types/mentorDecision").MentorDecision | null> {
  const { data, error } = await supabase
    .from("mentor_outputs")
    .select("decision")
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return data.decision;
}
