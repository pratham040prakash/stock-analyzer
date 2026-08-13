import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { buildChartBackedJourneyPlan } from "@/lib/journey/buildChartBackedJourneyPlan";
import { createClient } from "@/lib/supabase/server";
import { fetchStockData } from "@/services/market/stockData";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get("symbol")?.trim().toUpperCase();
  const preferSwing = searchParams.get("preferSwing") === "1";
  const activationRaw = searchParams.get("activationLevel");
  const activationLevel =
    activationRaw && Number.isFinite(Number(activationRaw))
      ? Number(activationRaw)
      : undefined;

  if (!symbol || symbol.length > 20 || !/^[A-Z0-9&.-]+$/.test(symbol)) {
    return apiError("Valid symbol query param required", 400);
  }

  const data = await fetchStockData(symbol);
  const currentRaw = searchParams.get("currentPrice");
  const currentPriceInr =
    currentRaw && Number.isFinite(Number(currentRaw)) && Number(currentRaw) > 0
      ? Number(currentRaw)
      : undefined;

  const plan = buildChartBackedJourneyPlan({
    symbol,
    prices: data.prices,
    currentPriceInr,
    activationLevelInr: activationLevel,
    preferSwing,
  });

  if (!plan) {
    return NextResponse.json({
      status: "insufficient_data",
      symbol,
      message: "Not enough daily candles to build a chart-backed path yet.",
    });
  }

  return NextResponse.json({ status: "ok", plan });
}
