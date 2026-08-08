import { createAdminClient } from "@/lib/supabase/admin";
import { apiError, apiOk } from "@/lib/api/response";
import { updateOpenDecisionOutcomes } from "@/services/decision/outcomeUpdater";

export async function GET(req: Request) {
  const cronSecret = process.env.CRON_SECRET;

  if (!cronSecret) {
    return apiError("CRON_SECRET is not configured", 500);
  }

  if (req.headers.get("authorization") !== `Bearer ${cronSecret}`) {
    return new Response("Unauthorized", { status: 401 });
  }

  try {
    const admin = createAdminClient();
    const result = await updateOpenDecisionOutcomes(admin);

    return apiOk({
      ...result,
      ranAt: new Date().toISOString(),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Outcome cron failed";
    return apiError(message, 500);
  }
}
