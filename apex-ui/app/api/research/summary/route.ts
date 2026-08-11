import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assembleResearchSummary } from "@/services/research/assembleResearchSummary";
import { createClient } from "@/lib/supabase/server";

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

  if (!symbol || symbol.length > 20 || !/^[A-Z0-9&.-]+$/.test(symbol)) {
    return apiError("Valid symbol query param required", 400);
  }

  const summary = await assembleResearchSummary(symbol);

  return NextResponse.json({ status: "ok", summary });
}
