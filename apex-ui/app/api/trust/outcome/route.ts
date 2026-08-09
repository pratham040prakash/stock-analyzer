import { apiError, apiOk } from "@/lib/api/response";
import { getUserTrustSnapshot } from "@/services/decision/trustOutcome";
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

  try {
    const trust = await getUserTrustSnapshot(supabase, user.id);
    return apiOk({ trust });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load trust outcome";
    return apiError(message, 500);
  }
}
