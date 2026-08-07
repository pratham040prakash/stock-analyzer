import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import {
  deployableFundsForIntent,
  getAllocation,
} from "@/lib/allocation";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import { getActiveBrokerConnection } from "@/services/broker/connections";
import {
  computePortfolioMetrics,
  fetchZerodhaMargins,
} from "@/services/brokers/zerodha";
import { getDecision } from "@/services/decision/engine";
import {
  getTodayDailyDecision,
  saveDailyDecision,
} from "@/services/decision/repository";
import {
  getFinancialProfileFromDb,
  getLatestMentorOutput,
  getLatestPortfolioSnapshotWithMetrics,
} from "@/services/portfolio/repository";
import { createClient } from "@/lib/supabase/server";
import type { DailyDecisionOutput } from "@/types/decision";
import type { Intent } from "@/types/intent";
import { parseUserIntent, resolveIntent } from "@/types/intent";
import type { Portfolio } from "@/types/portfolio";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@/types/database";

type Client = SupabaseClient<Database>;

function topAllocationPercent(holdings: Portfolio["holdings"]): number {
  const totalValue = holdings.reduce(
    (sum, holding) => sum + holding.quantity * holding.currentPrice,
    0,
  );

  if (totalValue <= 0 || holdings.length === 0) {
    return 0;
  }

  const topValue = Math.max(
    ...holdings.map((holding) => holding.quantity * holding.currentPrice),
  );

  return (topValue / totalValue) * 100;
}

async function enrichDecisionWithAllocation(
  supabase: Client,
  userId: string,
  intent: Intent,
  decision: DailyDecisionOutput,
  holdings: Portfolio["holdings"],
): Promise<DailyDecisionOutput> {
  const connection = await getActiveBrokerConnection(supabase, userId);

  if (connection?.status !== "active") {
    return { ...decision, recommended_allocation: [] };
  }

  const marginsResult = await fetchZerodhaMargins(connection.accessToken);

  if (marginsResult.status !== "OK") {
    return { ...decision, recommended_allocation: [] };
  }

  const risk = portfolioRiskFromAllocation(topAllocationPercent(holdings))
    .risk_level;
  const deployable = deployableFundsForIntent(
    marginsResult.availableCash,
    intent,
  );
  const recommended_allocation = getAllocation(deployable, intent, risk);

  return { ...decision, recommended_allocation };
}

function decisionResponsePayload(
  decision: DailyDecisionOutput,
  intent: Intent,
  extras: Record<string, unknown> = {},
) {
  const allocation = decision.recommended_allocation ?? [];

  return {
    decision,
    intent: decision.intent ?? intent,
    action: decision.action,
    message: decision.message ?? null,
    opportunities: decision.opportunities ?? null,
    allocation,
    ...extras,
  };
}

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const intent = resolveIntent(parseUserIntent(searchParams.get("intent")));

  const stored = await getTodayDailyDecision(supabase, user.id);

  const snapshot = await getLatestPortfolioSnapshotWithMetrics(
    supabase,
    user.id,
  );

  if (!snapshot) {
    if (stored) {
      const { created_at, ...decision } = stored;
      return NextResponse.json(
        decisionResponsePayload(decision, intent, {
          source: "database",
          created_at,
        }),
      );
    }

    return NextResponse.json({
      decision: null,
      intent: null,
      action: null,
      message: null,
      opportunities: null,
      allocation: [],
    });
  }

  const financialProfile = await getFinancialProfileFromDb(supabase, user.id);
  const lastMentorOutput = await getLatestMentorOutput(supabase, user.id);

  const metrics = computePortfolioMetrics(snapshot.portfolio);
  const baseDecision = getDecision({
    portfolioSnapshot: {
      holdings: snapshot.portfolio.holdings,
      total_value: snapshot.total_value || metrics.totalValue,
      pnl: snapshot.pnl || metrics.pnl,
    },
    financialProfile,
    lastMentorOutput,
    intent,
  });

  const decision = await enrichDecisionWithAllocation(
    supabase,
    user.id,
    intent,
    baseDecision,
    snapshot.portfolio.holdings,
  );

  try {
    await saveDailyDecision(supabase, user.id, decision);
  } catch {
    // History persistence should not block today's decision.
  }

  const storedAfterSave = await getTodayDailyDecision(supabase, user.id);

  return NextResponse.json(
    decisionResponsePayload(decision, intent, {
      source: storedAfterSave ? "database" : "computed",
      created_at: storedAfterSave?.created_at ?? stored?.created_at,
    }),
  );
}
