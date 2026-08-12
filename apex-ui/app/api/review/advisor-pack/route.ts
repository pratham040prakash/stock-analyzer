import { apiError, apiOk } from "@/lib/api/response";
import { assembleAdvisorReviewPack } from "@/services/review/assembleAdvisorReviewPack";
import {
  isAdvisorPilotEnabled,
  readAdvisorPilotSeats,
} from "@/services/review/advisorPilotConfig";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";
import { getDisciplineStreak } from "@/services/discipline/streak";
import { listDecisionReceipts } from "@/services/receipts/persistReceipt";
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

  if (!isAdvisorPilotEnabled()) {
    return apiOk({
      enabled: false,
      seats: 0,
      pack: null,
    });
  }

  const seats = readAdvisorPilotSeats();
  const [receipts, history, streak] = await Promise.all([
    listDecisionReceipts(supabase, user.id, 30),
    getDisciplineHistory(supabase, user.id, 7),
    getDisciplineStreak(supabase, user.id),
  ]);

  const clientLabel =
    typeof user.user_metadata?.full_name === "string" &&
    user.user_metadata.full_name.trim()
      ? user.user_metadata.full_name.trim()
      : user.email ?? "APEX client";

  const pack = assembleAdvisorReviewPack({
    clientLabel,
    seats,
    receipts,
    summary: history.summary,
    streakCount: streak.streakCount,
  });

  return apiOk({
    enabled: true,
    seats,
    pack,
  });
}
