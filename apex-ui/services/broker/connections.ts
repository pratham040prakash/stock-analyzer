import type { SupabaseClient } from "@supabase/supabase-js";
import { brokerError, brokerLog } from "@/lib/broker/log";
import { decryptToken, encryptToken } from "@/lib/crypto/encrypt";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

export type BrokerConnectionInput = {
  accessToken: string;
  publicToken: string;
  kiteUserId: string;
};

export function mapBrokerDbError(message: string): string {
  const lower = message.toLowerCase();
  if (
    lower.includes("broker_connections") &&
    (lower.includes("does not exist") || lower.includes("schema cache"))
  ) {
    return "Database table broker_connections is missing. Run apex-ui/supabase/schema.sql in Supabase SQL editor.";
  }
  return message;
}

export async function upsertBrokerConnection(
  supabase: Client,
  userId: string,
  broker: string,
  tokens: BrokerConnectionInput,
): Promise<void> {
  const access_token_encrypted = encryptToken(tokens.accessToken);
  const public_token_encrypted = encryptToken(tokens.publicToken);

  brokerLog("Saving broker connection", {
    user_id: userId,
    broker,
    kite_user_id: tokens.kiteUserId,
  });

  const { data, error } = await supabase
    .from("broker_connections")
    .upsert(
      {
        user_id: userId,
        broker,
        access_token_encrypted,
        public_token_encrypted,
        kite_user_id: tokens.kiteUserId,
        status: "active",
        updated_at: new Date().toISOString(),
      },
      { onConflict: "user_id,broker" },
    )
    .select("id, status, kite_user_id")
    .single();

  if (error) {
    brokerError("broker_connections upsert failed", {
      user_id: userId,
      message: error.message,
      code: error.code,
    });
    throw new Error(mapBrokerDbError(error.message));
  }

  brokerLog("broker_connections upsert success", {
    user_id: userId,
    row_id: data?.id,
    status: data?.status,
    kite_user_id: data?.kite_user_id,
  });
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

  if (error) {
    brokerError("broker_connections select failed", {
      user_id: userId,
      message: error.message,
    });
    return null;
  }

  if (!data) {
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
  const { data, error } = await supabase
    .from("broker_connections")
    .select("status")
    .eq("user_id", userId)
    .eq("broker", broker)
    .maybeSingle();

  if (error) {
    brokerError("broker_connections status check failed", {
      user_id: userId,
      message: error.message,
    });
    return false;
  }

  return data?.status === "active";
}

export async function getBrokerConnectionStatus(
  supabase: Client,
  userId: string,
  broker = "zerodha",
): Promise<{ connected: boolean; status: string | null; kiteUserId: string | null }> {
  const { data, error } = await supabase
    .from("broker_connections")
    .select("status, kite_user_id")
    .eq("user_id", userId)
    .eq("broker", broker)
    .maybeSingle();

  if (error) {
    brokerError("broker_connections session lookup failed", {
      user_id: userId,
      message: error.message,
    });
    return { connected: false, status: null, kiteUserId: null };
  }

  if (!data) {
    return { connected: false, status: null, kiteUserId: null };
  }

  return {
    connected: data.status === "active",
    status: data.status,
    kiteUserId: data.kite_user_id,
  };
}
