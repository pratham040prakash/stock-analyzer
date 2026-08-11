import { assembleInvestorDna } from "@/services/you/assembleInvestorDna";
import { getDisciplineHistory } from "@/services/decision/disciplineHistory";
import { getDisciplineStreak } from "@/services/discipline/streak";
import { getUserTrustSnapshot } from "@/services/decision/trustOutcome";
import { buildDisciplineProcessScore } from "@/services/review/disciplineScore";
import type { Database } from "@/types/database";
import type {
  TraderStateWord,
  TrustStateWord,
  YouSnapshotViewModel,
} from "@/types/youSnapshot";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

function resolveTraderState(
  processScore: number,
  streakCount: number,
  losses: number,
): TraderStateWord {
  if (losses >= 2) {
    return "Rebuilding";
  }

  if (processScore >= 75 && streakCount >= 3) {
    return "Growing";
  }

  if (processScore >= 55) {
    return "Steady";
  }

  return "Focused";
}

function resolveTrustState(
  trustScore: number,
  lastOutcome: string | null,
): TrustStateWord {
  if (lastOutcome === "loss") {
    return "Learning";
  }

  if (trustScore >= 70) {
    return "Earned";
  }

  return "Honest";
}

export async function assembleYouSnapshot(
  supabase: Client,
  userId: string,
): Promise<YouSnapshotViewModel> {
  const [history, streak, trust, investorDna] = await Promise.all([
    getDisciplineHistory(supabase, userId, 14),
    getDisciplineStreak(supabase, userId),
    getUserTrustSnapshot(supabase, userId),
    assembleInvestorDna(supabase, userId),
  ]);

  const process = buildDisciplineProcessScore(
    history.summary,
    streak.streakCount,
  );
  const traderState = resolveTraderState(
    process.score,
    streak.streakCount,
    history.summary.losses,
  );
  const trustState = resolveTrustState(
    trust.trustScore,
    trust.lastOutcome?.outcome ?? null,
  );

  const traderNarratives: Record<TraderStateWord, string> = {
    Growing:
      "You are building follow-through — small daily choices are compounding.",
    Steady:
      "You are holding a calm rhythm — consistency matters more than one lucky week.",
    Rebuilding:
      "Losses surfaced — tighten size, honor stops, and protect process over outcomes.",
    Focused:
      "You are in a focused stretch — one plan, one verdict, one day at a time.",
  };

  const trustNarratives: Record<TrustStateWord, string> = {
    Honest:
      "I state uncertainty plainly and never pretend outcomes are guaranteed.",
    Learning:
      "When a miss happens, I acknowledge it and adjust how I frame risk.",
    Earned:
      "Trust is earned through honest memory — not hit-rate marketing.",
  };

  return {
    built_at: new Date().toISOString(),
    trader_state: traderState,
    trader_narrative: traderNarratives[traderState],
    coaching_insight:
      history.summary.waitDays >= 2
        ? "The hardest trade this week was waiting — that discipline protects capital."
        : "Protect gains by following the same process that created them.",
    forward_line:
      "Tomorrow I'll continue watching for high-quality setups that fit your plan.",
    process_score: process.score,
    streak_count: streak.streakCount,
    trust_score: trust.trustScore,
    trust_state: trustState,
    trust_narrative: trustNarratives[trustState],
    last_week_summary: `Followed ${history.summary.followedDays} · Wait ${history.summary.waitDays} · Wins ${history.summary.wins}`,
    this_week_summary: process.message,
    visible_miss:
      history.summary.losses > 0
        ? "A recent loss surfaced — review size and stop discipline before the next act."
        : null,
    investor_dna: investorDna,
  };
}

export function runYouSnapshotSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`You snapshot self-check failed: ${message}`);
    }
  };

  const traderGrowing = resolveTraderState(80, 4, 0);
  const trustLearning = resolveTrustState(40, "loss");

  assert(traderGrowing === "Growing", "High score + streak = Growing");
  assert(trustLearning === "Learning", "Loss outcome = Learning");
}
