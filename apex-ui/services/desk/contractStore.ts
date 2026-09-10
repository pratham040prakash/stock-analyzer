import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database, Json } from "@/types/database";
import type { TodayContract } from "@/lib/dailyLoop/todayContract";

type Client = SupabaseClient<Database>;

function asContract(payload: Json | null): TodayContract | null {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return null;
  }

  const parsed = payload as unknown as TodayContract;
  if (!parsed.kiteLine || !parsed.rule || !parsed.dateKey) {
    return null;
  }

  return parsed;
}

export async function readServerContract(
  supabase: Client,
  userId: string,
  dateKey: string,
): Promise<TodayContract | null> {
  const { data, error } = await supabase
    .from("today_contracts")
    .select("payload")
    .eq("user_id", userId)
    .eq("contract_date", dateKey)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return asContract(data.payload);
}

export async function writeServerContract(
  supabase: Client,
  userId: string,
  contract: TodayContract,
): Promise<TodayContract | null> {
  const { data, error } = await supabase
    .from("today_contracts")
    .upsert(
      {
        user_id: userId,
        contract_date: contract.dateKey,
        payload: contract as unknown as Json,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "user_id,contract_date" },
    )
    .select("payload")
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return asContract(data.payload) ?? contract;
}

export async function listServerContracts(
  supabase: Client,
  dateKey: string,
): Promise<Array<{ userId: string; contract: TodayContract }>> {
  const { data, error } = await supabase
    .from("today_contracts")
    .select("user_id, payload")
    .eq("contract_date", dateKey);

  if (error || !data) {
    return [];
  }

  const rows: Array<{ userId: string; contract: TodayContract }> = [];
  for (const row of data) {
    const contract = asContract(row.payload);
    if (!contract) {
      continue;
    }
    rows.push({ userId: row.user_id, contract });
  }
  return rows;
}

export async function listContractHistory(
  supabase: Client,
  userId: string,
  sinceDate: string,
): Promise<TodayContract[]> {
  const { data, error } = await supabase
    .from("today_contracts")
    .select("payload")
    .eq("user_id", userId)
    .gte("contract_date", sinceDate)
    .order("contract_date", { ascending: false });

  if (error || !data) {
    return [];
  }

  const contracts: TodayContract[] = [];
  for (const row of data) {
    const contract = asContract(row.payload);
    if (contract) {
      contracts.push(contract);
    }
  }
  return contracts;
}

export async function claimDeskAlert(
  supabase: Client,
  userId: string,
  dateKey: string,
  alertKey: string,
): Promise<boolean> {
  const { error } = await supabase.from("desk_alerts").insert({
    user_id: userId,
    date_key: dateKey,
    alert_key: alertKey,
  });

  if (!error) {
    return true;
  }

  return false;
}
