import type { SupabaseClient } from "@supabase/supabase-js";
import {
  getActiveBrokerConnection,
  markBrokerConnectionExpired,
} from "@/services/broker/connections";
import {
  computePortfolioMetrics,
  fetchZerodhaHoldings,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { evaluateMentor } from "@/services/mentor/engine";
import {
  getFinancialProfileFromDb,
  saveMentorOutput,
  savePortfolioSnapshot,
} from "@/services/portfolio/repository";
import { syncBrokerActivityFromKite } from "@/services/trade/syncBrokerActivity";
import type { Database } from "@/types/database";
import type { Portfolio } from "@/types/portfolio";
import type { MentorDecision } from "@/types/mentorDecision";

type Client = SupabaseClient<Database>;

/**
 * Wave 1 invariant: the sync path may refresh portfolio/broker/mentor
 * source data only. It must never produce or overwrite the frozen daily
 * decision artifact — that authority lives exclusively behind
 * /api/decision/today (single canonical producer).
 */

export type SyncResult =
  | {
      status: "OK";
      portfolio: Portfolio;
      mentorDecision: MentorDecision;
      brokerActivity?: {
        imported: number;
        skipped: number;
        symbols: string[];
        tradesSeen: number;
        ordersSeen: number;
        openOrders: number;
      };
    }
  | { status: "NOT_CONNECTED" }
  | { status: "TOKEN_EXPIRED" }
  | { status: "ERROR"; message: string };

export async function syncUserPortfolio(
  supabase: Client,
  userId: string,
): Promise<SyncResult> {
  const connection = await getActiveBrokerConnection(supabase, userId);

  if (!connection) {
    return { status: "NOT_CONNECTED" };
  }

  if (connection.status !== "active" || !connection.accessToken) {
    return { status: "TOKEN_EXPIRED" };
  }

  const holdingsResult = await fetchZerodhaHoldings(connection.accessToken);

  if (holdingsResult.status === "TOKEN_EXPIRED") {
    await markBrokerConnectionExpired(supabase, userId);
    return { status: "TOKEN_EXPIRED" };
  }

  if (holdingsResult.status === "ERROR") {
    return { status: "ERROR", message: holdingsResult.message };
  }

  const portfolio = mapKiteHoldingsToPortfolio(holdingsResult.data);
  const metrics = computePortfolioMetrics(portfolio);

  await savePortfolioSnapshot(supabase, userId, portfolio, metrics);

  const brokerActivityResult = await syncBrokerActivityFromKite(supabase, userId);
  const brokerActivity =
    brokerActivityResult.status === "OK"
      ? {
          imported: brokerActivityResult.imported,
          skipped: brokerActivityResult.skipped,
          symbols: brokerActivityResult.symbols,
          tradesSeen: brokerActivityResult.tradesSeen,
          ordersSeen: brokerActivityResult.ordersSeen,
          openOrders: brokerActivityResult.openOrders,
        }
      : undefined;

  const financialProfile = await getFinancialProfileFromDb(supabase, userId);
  const mentorResult = evaluateMentor({
    portfolio,
    financialProfile,
  });

  await saveMentorOutput(supabase, userId, mentorResult);

  // Wave 1: do NOT produce or persist a daily decision here. The frozen
  // artifact is produced exclusively by /api/decision/today.

  return {
    status: "OK",
    portfolio,
    mentorDecision: mentorResult.decision,
    brokerActivity,
  };
}

export async function syncAllUsers(
  adminClient: SupabaseClient<Database>,
): Promise<{ synced: number; failed: number; expired: number }> {
  const { data: connections, error } = await adminClient
    .from("broker_connections")
    .select("user_id")
    .eq("broker", "zerodha")
    .eq("status", "active");

  if (error || !connections) {
    throw new Error(error?.message ?? "Failed to load broker connections");
  }

  let synced = 0;
  let failed = 0;
  let expired = 0;

  for (const connection of connections) {
    const result = await syncUserPortfolio(adminClient, connection.user_id);

    if (result.status === "OK") {
      synced += 1;
    } else if (result.status === "TOKEN_EXPIRED") {
      expired += 1;
    } else {
      failed += 1;
    }
  }

  return { synced, failed, expired };
}
