import { assemblePortfolioOverview } from "@/services/portfolio/assembleOverview";
import type { AskAnswerViewModel } from "@/types/askAnswer";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

const PORTFOLIO_PATTERNS = [
  /too concentrated/i,
  /concentration/i,
  /overweight/i,
  /diversif/i,
  /portfolio health/i,
  /allocation/i,
];

export function isPortfolioQuestion(question: string): boolean {
  return PORTFOLIO_PATTERNS.some((pattern) => pattern.test(question));
}

export async function assemblePortfolioAskAnswer(
  supabase: Client,
  userId: string,
  question: string,
): Promise<AskAnswerViewModel> {
  const overview = await assemblePortfolioOverview(supabase, userId);
  const allocation = overview.allocation;
  const builtAt = new Date().toISOString();

  if (!allocation || (overview.portfolio?.holdings.length ?? 0) === 0) {
    return {
      question,
      answer_word: "Wait",
      headline: "Connect broker for portfolio-aware answers.",
      reason: "Sync Zerodha to see concentration and allocation drift.",
      uncertainty: "High",
      symbol: null,
      built_at: builtAt,
    };
  }

  const top = allocation.holdings
    .slice()
    .sort((a, b) => b.allocation_pct - a.allocation_pct)[0];

  const tooConcentrated = top && top.allocation_pct >= 35;
  const coreDriftHigh = Math.abs(allocation.drift.core) >= 10;

  if (/concentrat|overweight/i.test(question) && tooConcentrated) {
    return {
      question,
      answer_word: "Wait",
      headline: `Wait · concentration risk`,
      reason: `${top.tradingsymbol} is ${top.allocation_pct.toFixed(0)}% of portfolio — research before adding size.`,
      uncertainty: "Medium",
      symbol: top.tradingsymbol,
      built_at: builtAt,
    };
  }

  if (/concentrat|overweight/i.test(question) && !tooConcentrated) {
    return {
      question,
      answer_word: "Wait",
      headline: "Wait · concentration looks OK",
      reason: `Top holding ${top?.tradingsymbol ?? "—"} is within policy bounds today.`,
      uncertainty: "Medium",
      symbol: top?.tradingsymbol ?? null,
      built_at: builtAt,
    };
  }

  if (/diversif|allocation/i.test(question)) {
    return {
      question,
      answer_word: coreDriftHigh ? "Wait" : "Wait",
      headline: coreDriftHigh ? "Wait · rebalance first" : "Wait · policy steady",
      reason: coreDriftHigh
        ? `Core drift ${allocation.drift.core > 0 ? "+" : ""}${allocation.drift.core.toFixed(0)}% — align buckets before new buys.`
        : allocation.policy_note,
      uncertainty: "Medium",
      symbol: top?.tradingsymbol ?? null,
      built_at: builtAt,
    };
  }

  return {
    question,
    answer_word: "Wait",
    headline: "Wait · review portfolio",
    reason: overview.allocation?.policy_note ?? "Open Portfolio for allocation detail.",
    uncertainty: "Medium",
    symbol: top?.tradingsymbol ?? null,
    built_at: builtAt,
  };
}

export function runPortfolioAskSelfCheck(): void {
  if (!isPortfolioQuestion("Am I too concentrated?")) {
    throw new Error("Portfolio ask self-check failed");
  }
}
