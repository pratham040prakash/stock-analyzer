import { listInvestmentTheses } from "@/services/thesis/thesisRepository";
import type { ThesisInvalidationWarning } from "@/types/thesisInvalidation";
import type { PortfolioOverviewViewModel } from "@/types/portfolioOverview";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

function healthIsWeak(grade: string | undefined): boolean {
  return grade === "Risk";
}

export async function evaluateThesisInvalidation(
  supabase: Client,
  userId: string,
  overview: PortfolioOverviewViewModel | null,
): Promise<ThesisInvalidationWarning[]> {
  const theses = await listInvestmentTheses(supabase, userId);
  const warnings: ThesisInvalidationWarning[] = [];

  if (!overview?.health?.length) {
    return warnings;
  }

  for (const thesis of theses) {
    if (!thesis.invalidation?.trim()) {
      continue;
    }

    const health = overview.health.find(
      (chip) => chip.symbol.toUpperCase() === thesis.symbol.toUpperCase(),
    );

    if (health && healthIsWeak(health.grade)) {
      warnings.push({
        symbol: thesis.symbol,
        message: `${thesis.symbol} health is ${health.grade} — revisit invalidation rule.`,
        invalidation: thesis.invalidation,
        health_status: health.grade,
      });
      continue;
    }

    const holding = overview.portfolio?.holdings.find(
      (row) => row.tradingsymbol.toUpperCase() === thesis.symbol.toUpperCase(),
    );

    const pnlPct =
      holding && holding.average_price > 0
        ? ((holding.last_price - holding.average_price) / holding.average_price) * 100
        : null;

    if (pnlPct !== null && pnlPct <= -15) {
      warnings.push({
        symbol: thesis.symbol,
        message: `${thesis.symbol} is down ${Math.abs(pnlPct).toFixed(0)}% — check thesis invalidation.`,
        invalidation: thesis.invalidation,
        health_status: health?.grade ?? "unknown",
      });
    }
  }

  return warnings.slice(0, 5);
}

export function runThesisInvalidationSelfCheck(): void {
  if (typeof evaluateThesisInvalidation !== "function") {
    throw new Error("Thesis invalidation self-check failed");
  }
}
