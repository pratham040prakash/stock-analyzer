import { NextResponse } from "next/server";
import { apiError } from "@/lib/api/response";
import { reconcileBrokerForReview } from "@/services/review/reconcileBroker";
import { createClient } from "@/lib/supabase/server";

export async function POST() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const result = await reconcileBrokerForReview(supabase, user.id);

  return NextResponse.json({
    status: result.synced ? "ok" : "error",
    ...result,
  });
}
