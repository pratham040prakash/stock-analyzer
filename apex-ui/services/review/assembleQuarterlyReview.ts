import { istDateKey, shiftIstDateKey } from "@/lib/dailyLoop/disciplineDates";
import { assemblePortfolioOverview } from "@/services/portfolio/assembleOverview";
import { buildPlannedVsActualRows } from "@/services/review/plannedVsActual";
import { listInvestmentTheses } from "@/services/thesis/thesisRepository";
import type { QuarterlyReviewViewModel } from "@/types/quarterlyReview";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

function quarterLabel(date = new Date()): string {
  const month = Number(
    date.toLocaleDateString("en-IN", { month: "numeric", timeZone: "Asia/Kolkata" }),
  );
  const year = date.toLocaleDateString("en-IN", {
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
  const quarter = Math.ceil(month / 3);

  return `Q${quarter} ${year}`;
}

export async function assembleQuarterlyReview(
  supabase: Client,
  userId: string,
): Promise<QuarterlyReviewViewModel> {
  const sinceKey = shiftIstDateKey(istDateKey(), -90);
  const [planned, overview, theses] = await Promise.all([
    buildPlannedVsActualRows(supabase, userId, 90),
    assemblePortfolioOverview(supabase, userId),
    listInvestmentTheses(supabase, userId),
  ]);

  const aligned = planned.summary.aligned;
  const deviated = planned.summary.deviated;
  const total = aligned + deviated + planned.summary.planned_only + planned.summary.actual_only;
  const disciplineScore =
    total > 0 ? Math.round((aligned / total) * 100) : 0;

  const actionItems: string[] = [];
  let concentrationWarning: string | null = null;
  let sacredCoreOk = true;

  if (overview.allocation) {
    const top = overview.allocation.holdings
      .slice()
      .sort((a, b) => b.allocation_pct - a.allocation_pct)[0];

    if (top && top.allocation_pct >= 35) {
      concentrationWarning = `${top.tradingsymbol} is ${top.allocation_pct.toFixed(0)}% — review thesis before adding.`;
      sacredCoreOk = top.allocation_pct < 50;
      actionItems.push(`Research ${top.tradingsymbol} this quarter.`);
    }
  }

  if (deviated >= 3) {
    actionItems.push("Three or more plan deviations — tighten daily commit ritual.");
  }

  if (aligned >= 5 && deviated === 0) {
    actionItems.push("Process held — protect gains with same position sizing.");
  }

  if (overview.status !== "ok") {
    actionItems.push("Connect broker for a complete quarterly review.");
  }

  const thesisProgress =
    overview.allocation?.holdings
      .slice()
      .sort((a, b) => b.allocation_pct - a.allocation_pct)
      .slice(0, 5)
      .map((row) => {
        const documented = theses.some(
          (thesis) => thesis.symbol.toUpperCase() === row.tradingsymbol.toUpperCase(),
        );

        return {
          symbol: row.tradingsymbol,
          status: documented ? ("documented" as const) : ("missing" as const),
          note: documented
            ? `${row.allocation_pct.toFixed(0)}% · thesis on file`
            : `${row.allocation_pct.toFixed(0)}% · add thesis in Research`,
        };
      }) ?? [];

  const missingTheses = thesisProgress.filter((row) => row.status === "missing").length;

  if (missingTheses > 0) {
    actionItems.push(`Document thesis for ${missingTheses} top holding(s) this quarter.`);
  }

  const goalFraming =
    sacredCoreOk && deviated <= aligned
      ? "On track for long-term compounding — protect process over prediction."
      : "Quarterly reset: align buckets and thesis before adding risk.";

  const headline =
    deviated === 0 && aligned > 0
      ? "Quarterly process looks steady."
      : deviated > aligned
        ? "Quarterly review: plan vs action needs attention."
        : "Quarterly check-in — stay consistent.";

  const summary = `Since ${sinceKey}: ${aligned} aligned days · ${deviated} deviations · discipline ${disciplineScore}/100.`;

  return {
    built_at: new Date().toISOString(),
    quarter_label: quarterLabel(),
    headline,
    summary,
    discipline_score: disciplineScore,
    aligned_days: aligned,
    deviated_days: deviated,
    concentration_warning: concentrationWarning,
    sacred_core_ok: sacredCoreOk,
    action_items: actionItems.slice(0, 5),
    thesis_progress: thesisProgress,
    goal_framing: goalFraming,
  };
}

export function runQuarterlyReviewSelfCheck(): void {
  if (quarterLabel().length < 4) {
    throw new Error("Quarterly review self-check failed: label");
  }
}
