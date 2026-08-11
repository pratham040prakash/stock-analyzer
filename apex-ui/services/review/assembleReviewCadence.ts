import { istDateKey, shiftIstDateKey } from "@/lib/dailyLoop/disciplineDates";
import { buildWeeklyReviewHeadline } from "@/lib/dailyLoop/weeklyReview";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";
import { getDisciplineStreak } from "@/services/discipline/streak";
import { assembleMonthlyDoctor } from "@/services/review/assembleMonthlyDoctor";
import { assembleQuarterlyReview } from "@/services/review/assembleQuarterlyReview";
import { buildDisciplineProcessScore } from "@/services/review/disciplineScore";
import { buildPlannedVsActualRows } from "@/services/review/plannedVsActual";
import type { ReviewCadencePackage } from "@/types/reviewCadence";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export async function assembleReviewCadencePackage(
  supabase: Client,
  userId: string,
): Promise<ReviewCadencePackage> {
  const [history, streak, planned, monthly, quarterly] = await Promise.all([
    getDisciplineHistory(supabase, userId, 14),
    getDisciplineStreak(supabase, userId),
    buildPlannedVsActualRows(supabase, userId, 14),
    assembleMonthlyDoctor(supabase, userId),
    assembleQuarterlyReview(supabase, userId),
  ]);

  const processScore = buildDisciplineProcessScore(
    history.summary,
    streak.streakCount,
  );

  return {
    built_at: new Date().toISOString(),
    weekly: {
      headline: buildWeeklyReviewHeadline(history.summary),
      summary: history.summary,
      process_score: processScore,
      planned_summary: planned.summary,
    },
    monthly,
    quarterly,
  };
}

export function runReviewCadenceSelfCheck(): void {
  const key = istDateKey();
  const prior = shiftIstDateKey(key, -30);

  if (prior >= key) {
    throw new Error("Review cadence self-check failed: date shift");
  }
}
