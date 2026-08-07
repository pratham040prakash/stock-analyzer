import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { evaluateDailyDecision } from "@/services/decision/engine";
import { getTodayDailyDecision } from "@/services/decision/repository";
import { computePortfolioMetrics } from "@/services/brokers/zerodha";
import {
  getFinancialProfileFromDb,
  getLatestMentorOutput,
  getLatestPortfolioSnapshotWithMetrics,
} from "@/services/portfolio/repository";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const stored = await getTodayDailyDecision(supabase, user.id);
  if (stored) {
    const { created_at, ...decision } = stored;
    return NextResponse.json({
      decision,
      source: "database",
      created_at,
    });
  }

  const snapshot = await getLatestPortfolioSnapshotWithMetrics(
    supabase,
    user.id,
  );

  if (!snapshot) {
    return NextResponse.json({ decision: null });
  }

  const financialProfile = await getFinancialProfileFromDb(supabase, user.id);
  const lastMentorOutput = await getLatestMentorOutput(supabase, user.id);

  const metrics = computePortfolioMetrics(snapshot.portfolio);
  const decision = evaluateDailyDecision({
    portfolioSnapshot: {
      holdings: snapshot.portfolio.holdings,
      total_value: snapshot.total_value || metrics.totalValue,
      pnl: snapshot.pnl || metrics.pnl,
    },
    financialProfile,
    lastMentorOutput,
  });

  return NextResponse.json({
    decision,
    source: "computed",
  });
}
