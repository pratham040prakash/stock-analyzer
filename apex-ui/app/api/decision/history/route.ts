import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { getDecisionHistory } from "@/services/decision/repository";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const daysParam = Number(searchParams.get("days") ?? "3");
  const days = Number.isFinite(daysParam)
    ? Math.min(7, Math.max(1, Math.round(daysParam)))
    : 3;

  const history = await getDecisionHistory(supabase, user.id, days);

  return NextResponse.json({ history });
}
