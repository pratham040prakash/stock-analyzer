import type { AllocationPolicySummary } from "@/services/portfolio/allocationPolicy";
import type { HoldingHealthChip } from "@/services/portfolio/holdingHealth";
import type { MonthlyTrendLine } from "@/services/review/buildMonthlyTrends";

export type MonthlyDoctorViewModel = {
  built_at: string;
  month_label: string;
  headline: string;
  summary: string;
  concentration_warning: string | null;
  sacred_core_ok: boolean;
  allocation: AllocationPolicySummary | null;
  health: HoldingHealthChip[];
  action_items: string[];
  trends: MonthlyTrendLine[];
};
