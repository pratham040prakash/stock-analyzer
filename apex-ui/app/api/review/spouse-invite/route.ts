import { apiError, apiOk } from "@/lib/api/response";
import { getAppBaseUrl } from "@/lib/env/config";
import { assembleSpouseReviewInvite } from "@/services/review/assembleSpouseReviewInvite";
import { isSpouseReviewInviteEnabled } from "@/services/review/spouseReviewInviteConfig";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";
import { getDisciplineStreak } from "@/services/discipline/streak";
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

  if (!isSpouseReviewInviteEnabled()) {
    return apiOk({
      enabled: false,
      invite: null,
    });
  }

  const [history, streak] = await Promise.all([
    getDisciplineHistory(supabase, user.id, 7),
    getDisciplineStreak(supabase, user.id),
  ]);

  const investorLabel =
    typeof user.user_metadata?.full_name === "string" &&
    user.user_metadata.full_name.trim()
      ? user.user_metadata.full_name.trim()
      : user.email ?? "APEX investor";

  const appBase = getAppBaseUrl();
  const howItWorksUrl = appBase
    ? `${appBase}/app/you/how-it-works`
    : "/app/you/how-it-works";

  const invite = assembleSpouseReviewInvite({
    investorLabel,
    summary: history.summary,
    streakCount: streak.streakCount,
    howItWorksUrl,
  });

  return apiOk({
    enabled: true,
    invite,
  });
}
