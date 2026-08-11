import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assemblePortfolioOverview } from "@/services/portfolio/assembleOverview";
import { evaluateThesisInvalidation } from "@/services/thesis/evaluateThesisInvalidation";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const overview = await assemblePortfolioOverview(supabase, user.id);
  const warnings = await evaluateThesisInvalidation(supabase, user.id, overview);

  return NextResponse.json({ status: "ok", warnings });
}
