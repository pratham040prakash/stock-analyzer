import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { getDecision } from "@/services/decision/engine";
import {
  getTodayDailyDecision,
  saveDailyDecision,
} from "@/services/decision/repository";
import { computePortfolioMetrics } from "@/services/brokers/zerodha";
import {
  getFinancialProfileFromDb,
  getLatestMentorOutput,
  getLatestPortfolioSnapshotWithMetrics,
} from "@/services/portfolio/repository";
import { createClient } from "@/lib/supabase/server";
import { parseUserIntent, resolveIntent } from "@/types/intent";

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
      return NextResponse.json({
        decision,
        intent: decision.intent ?? null,
        action: decision.action,
        message: decision.message ?? null,
        opportunities: decision.opportunities ?? null,
        source: "database",
        created_at,
      });
    }
    return NextResponse.json({
      decision: null,
      intent: null,
      action: null,
      message: null,
      opportunities: null,
    });
  }

  const financialProfile = await getFinancialProfileFromDb(supabase, user.id);
  const lastMentorOutput = await getLatestMentorOutput(supabase, user.id);

  const metrics = computePortfolioMetrics(snapshot.portfolio);
  const decision = getDecision({
    portfolioSnapshot: {
      holdings: snapshot.portfolio.holdings,
      total_value: snapshot.total_value || metrics.totalValue,
      pnl: snapshot.pnl || metrics.pnl,
    },
    financialProfile,
    lastMentorOutput,
    intent,
  });

  try {
    await saveDailyDecision(supabase, user.id, decision);
  } catch {
    // History persistence should not block today's decision.
  }

  const storedAfterSave = await getTodayDailyDecision(supabase, user.id);

  return NextResponse.json({
    decision,
    intent: decision.intent ?? intent ?? null,
    action: decision.action,
    message: decision.message ?? null,
    opportunities: decision.opportunities ?? null,
    source: storedAfterSave ? "database" : "computed",
    created_at: storedAfterSave?.created_at ?? stored?.created_at,
  });
}
