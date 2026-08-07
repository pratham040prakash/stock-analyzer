import { apiError, apiOk } from "@/lib/api/response";
import { syncUserPortfolio } from "@/services/portfolio/sync";
import { createClient } from "@/lib/supabase/server";

export async function POST() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const result = await syncUserPortfolio(supabase, user.id);

  if (result.status === "OK") {
    return apiOk({
      portfolio: result.portfolio,
      mentorDecision: result.mentorDecision,
    });
  }

  return apiOk({ syncStatus: result.status });
}
