import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { assembleNewCapitalWorkflow } from "@/services/capital/newCapitalWorkflow";
import { createClient } from "@/lib/supabase/server";
import { getTodayDailyDecision } from "@/services/decision/repository";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const artifact = await getTodayDailyDecision(supabase, user.id);
  const workflow = await assembleNewCapitalWorkflow(
    supabase,
    user.id,
    undefined,
    artifact,
  );

  return NextResponse.json({ status: "ok", workflow });
}
