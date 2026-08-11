import { createAdminClient } from "@/lib/supabase/admin";
import { apiError, apiOk } from "@/lib/api/response";
import { runReviewDigestCron } from "@/services/review/runReviewDigestCron";

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
    const result = await runReviewDigestCron(admin);

    return apiOk(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Review digest cron failed";
    return apiError(message, 500);
  }
}
