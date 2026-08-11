import { listDecisionReceipts } from "@/services/receipts/persistReceipt";
import { getDisciplineStreak } from "@/services/discipline/streak";
import type { InvestorBehaviorTag, InvestorDnaViewModel } from "@/types/investorDna";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

function resolveBehaviorTag(
  waitCount: number,
  actCount: number,
  streak: number,
): InvestorBehaviorTag {
  const total = waitCount + actCount;

  if (total === 0 && streak === 0) {
    return "Building habit";
  }

  if (waitCount >= actCount + 2) {
    return "Disciplined waiter";
  }

  if (actCount >= waitCount + 2) {
    return "Active executor";
  }

  return "Mixed rhythm";
}

export async function assembleInvestorDna(
  supabase: Client,
  userId: string,
): Promise<InvestorDnaViewModel> {
  const [receipts, streak] = await Promise.all([
    listDecisionReceipts(supabase, userId, 14),
    getDisciplineStreak(supabase, userId),
  ]);

  const waitReceipts = receipts.filter(
    (row) => row.execution_kind === "WAIT" || row.execution_kind === "OBSERVE",
  ).length;
  const actReceipts = receipts.filter(
    (row) => row.execution_kind === "BUY" || row.execution_kind === "SELL",
  ).length;
  const behaviorTag = resolveBehaviorTag(
    waitReceipts,
    actReceipts,
    streak.streakCount,
  );

  const summaries: Record<InvestorBehaviorTag, string> = {
    "Disciplined waiter":
      "You favor waiting over acting — capital preservation is your edge.",
    "Active executor":
      "You act when the plan says act — watch size and avoid impulse adds.",
    "Mixed rhythm":
      "Your rhythm mixes wait and act — tighten daily commits for consistency.",
    "Building habit":
      "Early days — log discipline daily to build a reliable pattern.",
  };

  const insight =
    waitReceipts > actReceipts
      ? "Best next step: honor WAIT receipts before chasing new ideas."
      : actReceipts > 0
        ? "Best next step: confirm each act matched the morning verdict."
        : "Best next step: commit to today's plan before market open.";

  return {
    behavior_tag: behaviorTag,
    summary: summaries[behaviorTag],
    wait_receipts: waitReceipts,
    act_receipts: actReceipts,
    discipline_streak: streak.streakCount,
    insight,
  };
}

export function runInvestorDnaSelfCheck(): void {
  const tag = resolveBehaviorTag(3, 1, 2);

  if (tag !== "Disciplined waiter") {
    throw new Error("Investor DNA self-check failed: waiter tag");
  }
}
