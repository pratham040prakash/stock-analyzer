import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import {
  getActiveBrokerConnection,
  markBrokerConnectionExpired,
} from "@/services/broker/connections";
import {
  computePortfolioMetrics,
  fetchZerodhaHoldings,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import {
  getLatestPortfolioSnapshot,
  savePortfolioSnapshot,
} from "@/services/portfolio/repository";
import { syncUserPortfolio } from "@/services/portfolio/sync";
import { createClient } from "@/lib/supabase/server";
import {
  KITE_ACCESS_TOKEN_COOKIE,
} from "@/lib/broker/zerodhaSession";
import { cookies } from "next/headers";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ status: "NOT_CONNECTED" }, { status: 401 });
  }

  const connection = await getActiveBrokerConnection(supabase, user.id);

  if (!connection || connection.status !== "active") {
    const cached = await getLatestPortfolioSnapshot(supabase, user.id);
    if (cached) {
      return NextResponse.json({
        status: "TOKEN_EXPIRED",
        portfolio: cached,
      });
    }
    return NextResponse.json({ status: "NOT_CONNECTED" });
  }

  const holdingsResult = await fetchZerodhaHoldings(connection.accessToken);

  if (holdingsResult.status === "TOKEN_EXPIRED") {
    await markBrokerConnectionExpired(supabase, user.id);
    const cookieStore = await cookies();
    cookieStore.delete(KITE_ACCESS_TOKEN_COOKIE);

    const cached = await getLatestPortfolioSnapshot(supabase, user.id);
    return NextResponse.json({
      status: "TOKEN_EXPIRED",
      portfolio: cached ?? undefined,
    });
  }

  if (holdingsResult.status === "ERROR") {
    const cached = await getLatestPortfolioSnapshot(supabase, user.id);
    if (cached) {
      return NextResponse.json({ status: "OK", portfolio: cached, stale: true });
    }
    return apiError(holdingsResult.message, 502);
  }

  const portfolio = mapKiteHoldingsToPortfolio(holdingsResult.data);
  const metrics = computePortfolioMetrics(portfolio);

  await savePortfolioSnapshot(supabase, user.id, portfolio, metrics);

  return NextResponse.json({ status: "OK", portfolio });
}

export async function POST() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const result = await syncUserPortfolio(supabase, user.id);

  if (result.status === "OK") {
    return NextResponse.json({
      status: "OK",
      portfolio: result.portfolio,
      mentorDecision: result.mentorDecision,
    });
  }

  return NextResponse.json({ status: result.status }, { status: 200 });
}
