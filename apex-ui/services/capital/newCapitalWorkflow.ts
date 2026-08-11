import { assemblePortfolioOverview } from "@/services/portfolio/assembleOverview";
import type { NewCapitalViewModel } from "@/types/newCapital";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

export async function assembleNewCapitalWorkflow(
  supabase: Client,
  userId: string,
  deployableInr?: number | null,
): Promise<NewCapitalViewModel> {
  const overview = await assemblePortfolioOverview(supabase, userId, deployableInr ?? null);
  const cash =
    deployableInr ??
    overview.allocation?.cash_available_inr ??
    null;

  if (cash === null || cash <= 0) {
    return {
      built_at: new Date().toISOString(),
      available: null,
      message: "Connect broker and sync funds to plan new capital deployment.",
    };
  }

  const topHoldings =
    overview.allocation?.holdings
      .slice()
      .sort((a, b) => b.allocation_pct - a.allocation_pct)
      .slice(0, 3)
      .map((row) => row.tradingsymbol) ?? [];

  const sacredCoreNote =
    overview.allocation && Math.abs(overview.allocation.drift.core) >= 10
      ? "Core bucket is off policy — rebalance before adding size."
      : null;

  const guidance =
    topHoldings.length > 0
      ? `Deploy in tranches toward policy targets — research before adding to ${topHoldings[0]}.`
      : "Build core positions gradually — one high-conviction name at a time.";

  return {
    built_at: new Date().toISOString(),
    available: {
      deployable_inr: Math.round(cash),
      headline: `${Math.round(cash).toLocaleString("en-IN")} available to deploy`,
      guidance,
      suggested_symbols: topHoldings,
      sacred_core_note: sacredCoreNote,
    },
    message: "New capital follows policy — not impulse.",
  };
}

export function runNewCapitalSelfCheck(): void {
  if (typeof assembleNewCapitalWorkflow !== "function") {
    throw new Error("New capital self-check failed");
  }
}
