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

  const roundedCash = Math.round(cash);
  const trancheAmounts = [0.4, 0.35, 0.25].map((ratio) =>
    Math.round(roundedCash * ratio),
  );

  const tranches = [
    {
      label: "Tranche 1 · core alignment",
      amount_inr: trancheAmounts[0],
      note: "Close largest policy drift bucket first.",
    },
    {
      label: "Tranche 2 · conviction add",
      amount_inr: trancheAmounts[1],
      note: topHoldings[0]
        ? `Only after Research confirms ${topHoldings[0]} thesis.`
        : "Only after thesis is documented.",
    },
    {
      label: "Tranche 3 · reserve",
      amount_inr: trancheAmounts[2],
      note: "Hold for volatility or next monthly doctor review.",
    },
  ];

  return {
    built_at: new Date().toISOString(),
    available: {
      deployable_inr: roundedCash,
      headline: `${roundedCash.toLocaleString("en-IN")} available to deploy`,
      guidance,
      suggested_symbols: topHoldings,
      sacred_core_note: sacredCoreNote,
      tranches,
    },
    message: "New capital follows policy — not impulse.",
  };
}

export function runNewCapitalSelfCheck(): void {
  if (typeof assembleNewCapitalWorkflow !== "function") {
    throw new Error("New capital self-check failed");
  }
}
