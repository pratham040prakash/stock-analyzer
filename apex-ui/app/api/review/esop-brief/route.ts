import { apiError, apiOk } from "@/lib/api/response";
import { getAppBaseUrl } from "@/lib/env/config";
import { assembleEsopReviewBrief } from "@/services/review/assembleEsopReviewBrief";
import { isEsopReviewPersonaEnabled } from "@/services/review/esopReviewPersonaConfig";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";
import { getDisciplineStreak } from "@/services/discipline/streak";
import { getOperatingProfileFromDb } from "@/services/operatingProfile/repository";
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

  if (!isEsopReviewPersonaEnabled()) {
    return apiOk({
      enabled: false,
      brief: null,
    });
  }

  const [history, streak, operatingProfile] = await Promise.all([
    getDisciplineHistory(supabase, user.id, 7),
    getDisciplineStreak(supabase, user.id),
    getOperatingProfileFromDb(supabase, user.id),
  ]);

  const investorLabel =
    typeof user.user_metadata?.full_name === "string" &&
    user.user_metadata.full_name.trim()
      ? user.user_metadata.full_name.trim()
      : user.email ?? "APEX investor";

  const appBase = getAppBaseUrl();
  const reviewWeeklyUrl = appBase
    ? `${appBase}/app/review?tab=weekly`
    : "/app/review?tab=weekly";
  const reviewQuarterlyUrl = appBase
    ? `${appBase}/app/review?tab=quarterly`
    : "/app/review?tab=quarterly";

  const brief = assembleEsopReviewBrief({
    investorLabel,
    investmentStyle: operatingProfile?.investmentStyle ?? null,
    summary: history.summary,
    streakCount: streak.streakCount,
    reviewWeeklyUrl,
    reviewQuarterlyUrl,
  });

  return apiOk({
    enabled: true,
    brief,
  });
}
