import type { SupabaseClient } from "@supabase/supabase-js";
import { decryptToken, encryptToken } from "@/lib/crypto/encrypt";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export async function upsertBrokerConnection(
  supabase: Client,
  userId: string,
  broker: string,
  accessToken: string,
): Promise<void> {
  const access_token_encrypted = encryptToken(accessToken);

  const { error } = await supabase.from("broker_connections").upsert(
    {
      user_id: userId,
      broker,
      access_token_encrypted,
      status: "active",
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id,broker" },
  );

  if (error) {
    throw new Error(error.message);
  }
}

export async function getActiveBrokerConnection(
  supabase: Client,
  userId: string,
  broker = "zerodha",
): Promise<{ accessToken: string; status: string } | null> {
  const { data, error } = await supabase
    .from("broker_connections")
    .select("access_token_encrypted, status")
    .eq("user_id", userId)
    .eq("broker", broker)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  if (data.status !== "active") {
    return { accessToken: "", status: data.status };
  }

  return {
    accessToken: decryptToken(data.access_token_encrypted),
    status: data.status,
  };
}

export async function markBrokerConnectionExpired(
  supabase: Client,
  userId: string,
  broker = "zerodha",
): Promise<void> {
  await supabase
    .from("broker_connections")
    .update({
      status: "expired",
      updated_at: new Date().toISOString(),
    })
    .eq("user_id", userId)
    .eq("broker", broker);
}

export async function hasActiveBrokerConnection(
  supabase: Client,
  userId: string,
  broker = "zerodha",
): Promise<boolean> {
  const { data } = await supabase
    .from("broker_connections")
    .select("status")
    .eq("user_id", userId)
    .eq("broker", broker)
    .maybeSingle();

  return data?.status === "active";
}
