import type { MonthlyDoctorViewModel } from "@/types/monthlyDoctor";
import type { QuarterlyReviewViewModel } from "@/types/quarterlyReview";
import type { DisciplineProcessScore } from "@/services/review/disciplineScore";
import type { DisciplineHistorySummary } from "@/types/decisionHistory";
import type { PlannedVsActualSummary } from "@/types/plannedVsActual";

export type WeeklyReviewSlice = {
  headline: string;
  summary: DisciplineHistorySummary;
  process_score: DisciplineProcessScore;
  planned_summary: PlannedVsActualSummary;
};

export type ReviewCadencePackage = {
  built_at: string;
  weekly: WeeklyReviewSlice;
  monthly: MonthlyDoctorViewModel;
  quarterly: QuarterlyReviewViewModel;
};
