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
  /can i afford/i,
  /afford this/i,
  /afford to buy/i,
  /enough cash/i,
  /margin/i,
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
      proof_href: null,
      built_at: builtAt,
    };
  }

  const top = allocation.holdings
    .slice()
    .sort((a, b) => b.allocation_pct - a.allocation_pct)[0];

  const tooConcentrated = top && top.allocation_pct >= 35;
  const coreDriftHigh = Math.abs(allocation.drift.core) >= 10;

  if (/can i afford|afford this|afford to buy|enough cash|margin/i.test(question)) {
    const cash = allocation.cash_available_inr ?? 0;
    const canAfford = cash >= 25_000;

    return {
      question,
      answer_word: "Wait",
      headline: canAfford ? "Wait · size against policy" : "Wait · cash buffer thin",
      reason: canAfford
        ? `₹${Math.round(cash).toLocaleString("en-IN")} deployable — confirm tranche plan before acting.`
        : "Low deployable cash — build buffer before new buys.",
      uncertainty: "Medium",
      symbol: top?.tradingsymbol ?? null,
      proof_href: null,
      built_at: builtAt,
    };
  }

  if (/concentrat|overweight/i.test(question) && tooConcentrated) {
    return {
      question,
      answer_word: "Wait",
      headline: "Wait · concentration risk",
      reason: `${top.tradingsymbol} is ${top.allocation_pct.toFixed(0)}% of portfolio — research before adding size.`,
      uncertainty: "Medium",
      symbol: top.tradingsymbol,
      proof_href: null,
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
      proof_href: null,
      built_at: builtAt,
    };
  }

  if (/diversif|allocation/i.test(question)) {
    return {
      question,
      answer_word: "Wait",
      headline: coreDriftHigh ? "Wait · rebalance first" : "Wait · policy steady",
      reason: coreDriftHigh
        ? `Core drift ${allocation.drift.core > 0 ? "+" : ""}${allocation.drift.core.toFixed(0)}% — align buckets before new buys.`
        : allocation.policy_note,
      uncertainty: "Medium",
      symbol: top?.tradingsymbol ?? null,
      proof_href: null,
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
    proof_href: null,
    built_at: builtAt,
  };
}

export function runPortfolioAskSelfCheck(): void {
  if (!isPortfolioQuestion("Am I too concentrated?")) {
    throw new Error("Portfolio ask self-check failed");
  }

  if (!isPortfolioQuestion("Can I afford this trade?")) {
    throw new Error("Portfolio ask self-check failed: afford pattern");
  }
}
