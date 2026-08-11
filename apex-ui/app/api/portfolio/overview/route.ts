import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assemblePortfolioOverview } from "@/services/portfolio/assembleOverview";
import { getActiveBrokerConnection } from "@/services/broker/connections";
import { fetchZerodhaMargins } from "@/services/brokers/zerodha";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let cashAvailable: number | null = null;
  const connection = await getActiveBrokerConnection(supabase, user.id);

  if (connection?.status === "active" && connection.accessToken) {
    const margins = await fetchZerodhaMargins(connection.accessToken);
    if (margins.status === "OK") {
      cashAvailable = margins.marginAvailable;
    }
  }

  const overview = await assemblePortfolioOverview(supabase, user.id, cashAvailable);

  return NextResponse.json(
    { status: "ok", overview },
    { headers: { "Cache-Control": "no-store, must-revalidate" } },
  );
}
