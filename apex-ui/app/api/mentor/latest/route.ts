import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { getLatestMentorOutput } from "@/services/portfolio/repository";
import { evaluateMentor } from "@/services/mentor/engine";
import {
  getFinancialProfileFromDb,
  getLatestPortfolioSnapshot,
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

  const stored = await getLatestMentorOutput(supabase, user.id);
  if (stored) {
    return NextResponse.json({ decision: stored, source: "database" });
  }

  const portfolio = await getLatestPortfolioSnapshot(supabase, user.id);
  if (!portfolio) {
    return NextResponse.json({ decision: null });
  }

  const financialProfile = await getFinancialProfileFromDb(supabase, user.id);
  const result = evaluateMentor({ portfolio, financialProfile });

  return NextResponse.json({ decision: result.decision, source: "computed" });
}
