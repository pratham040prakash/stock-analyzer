import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { buildPlannedVsActualRows } from "@/services/review/plannedVsActual";
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
  const days = Number(searchParams.get("days") ?? "14");

  try {
    const result = await buildPlannedVsActualRows(supabase, user.id, days);
    return NextResponse.json({ status: "ok", ...result });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load planned vs actual";
    return apiError(message, 500);
  }
}
