import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { createClient } from "@/lib/supabase/server";
import {
  getActiveJourneyForSymbolFromDb,
  listActiveJourneysFromDb,
  normalizeJourneySymbol,
} from "@/services/journey/repository";
import { resolveInvestmentJourneyDbError } from "@/services/journey/errors";

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get("symbol");

  if (!symbol) {
    try {
      const journeys = await listActiveJourneysFromDb(supabase, user.id);
      return NextResponse.json({ journeys });
    } catch (error) {
      const resolved = resolveInvestmentJourneyDbError(error);
      return apiError(resolved.message, resolved.status);
    }
  }

  const normalized = normalizeJourneySymbol(symbol);
  if (!normalized) {
    return apiError("Valid symbol required", 400);
  }

  try {
    const journey = await getActiveJourneyForSymbolFromDb(
      supabase,
      user.id,
      normalized,
    );

    return NextResponse.json({ journey });
  } catch (error) {
    const resolved = resolveInvestmentJourneyDbError(error);
    return apiError(resolved.message, resolved.status);
  }
}
