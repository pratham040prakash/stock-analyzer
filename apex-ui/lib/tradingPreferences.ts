import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export async function isAutoTradingEnabled(
  supabase: Client,
  userId: string,
): Promise<boolean> {
  const { data, error } = await supabase
    .from("financial_profiles")
    .select("auto_trading_enabled")
    .eq("user_id", userId)
    .maybeSingle();

  if (error || !data) {
    return false;
  }

  return Boolean(data.auto_trading_enabled);
}

export async function setAutoTradingEnabled(
  supabase: Client,
  userId: string,
  enabled: boolean,
): Promise<void> {
  const { data: existing, error: readError } = await supabase
    .from("financial_profiles")
    .select("income_range, expense_range, investable_surplus")
    .eq("user_id", userId)
    .maybeSingle();

  if (readError) {
    throw new Error(readError.message);
  }

  if (existing) {
    const { error } = await supabase
      .from("financial_profiles")
      .update({
        auto_trading_enabled: enabled,
        updated_at: new Date().toISOString(),
      })
      .eq("user_id", userId);

    if (error) {
      throw new Error(error.message);
    }

    return;
  }

  const { error } = await supabase.from("financial_profiles").insert({
    user_id: userId,
    income_range: "<50K",
    expense_range: "<30K",
    investable_surplus: 0,
    auto_trading_enabled: enabled,
    updated_at: new Date().toISOString(),
  });

  if (error) {
    throw new Error(error.message);
  }
}
