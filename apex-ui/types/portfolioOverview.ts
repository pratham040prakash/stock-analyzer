import type { AllocationPolicySummary } from "@/services/portfolio/allocationPolicy";
import type { HoldingHealthChip } from "@/services/portfolio/holdingHealth";
import type { PortfolioApiResponse } from "@/types/portfolioApi";
import type { OpenMonitorPosition } from "@/services/monitor/openPositions";

export type PortfolioOverviewViewModel = {
  status: "ok" | "partial" | "error";
  portfolio: PortfolioApiResponse | null;
  allocation: AllocationPolicySummary | null;
  health: HoldingHealthChip[];
  positions: OpenMonitorPosition[];
  research_symbol: string | null;
  message?: string;
};
