import { assemblePortfolioOverview } from "@/services/portfolio/assembleOverview";
import type { MonthlyDoctorViewModel } from "@/types/monthlyDoctor";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

function monthLabel(date = new Date()): string {
  return date.toLocaleDateString("en-IN", {
    month: "long",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
}

export async function assembleMonthlyDoctor(
  supabase: Client,
  userId: string,
): Promise<MonthlyDoctorViewModel> {
  const overview = await assemblePortfolioOverview(supabase, userId);
  const allocation = overview.allocation;
  const health = overview.health ?? [];
  const builtAt = new Date().toISOString();

  const actionItems: string[] = [];
  let concentrationWarning: string | null = null;
  let sacredCoreOk = true;

  if (allocation) {
    const top = allocation.holdings
      .slice()
      .sort((a, b) => b.allocation_pct - a.allocation_pct)[0];

    if (top && top.allocation_pct >= 35) {
      concentrationWarning = `${top.tradingsymbol} is ${top.allocation_pct.toFixed(0)}% of portfolio — review concentration.`;
      actionItems.push(`Research ${top.tradingsymbol} before adding size.`);
      sacredCoreOk = top.allocation_pct < 50;
    }

    if (Math.abs(allocation.drift.core) >= 10) {
      actionItems.push(
        `Core allocation drift ${allocation.drift.core > 0 ? "+" : ""}${allocation.drift.core.toFixed(0)}% vs policy.`,
      );
    }

    if (Math.abs(allocation.drift.tactical) >= 10) {
      actionItems.push(
        `Tactical pool drift ${allocation.drift.tactical > 0 ? "+" : ""}${allocation.drift.tactical.toFixed(0)}%.`,
      );
    }
  }

  const riskHoldings = health.filter((chip) => chip.grade === "Risk");

  for (const chip of riskHoldings.slice(0, 3)) {
    actionItems.push(`${chip.symbol}: ${chip.reason}`);
  }

  if (overview.status !== "ok") {
    actionItems.push("Connect broker for a complete monthly review.");
  }

  const headline =
    actionItems.length === 0
      ? "Portfolio health looks steady this month."
      : "A few areas need attention this month.";

  const summary =
    allocation?.policy_note ??
    "Sync your broker to run allocation and health checks.";

  return {
    built_at: builtAt,
    month_label: monthLabel(),
    headline,
    summary,
    concentration_warning: concentrationWarning,
    sacred_core_ok: sacredCoreOk,
    allocation,
    health,
    action_items: actionItems.slice(0, 5),
  };
}

export function runMonthlyDoctorSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Monthly doctor self-check failed: ${message}`);
    }
  };

  assert(monthLabel().length > 3, "Month label must render");
}
