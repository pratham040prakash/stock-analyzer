import { listInvestmentTheses } from "@/services/thesis/thesisRepository";
import { parseInvalidationRule } from "@/services/thesis/parseInvalidationRule";
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

  if (!overview?.portfolio?.holdings?.length && !overview?.health?.length) {
    return warnings;
  }

  for (const thesis of theses) {
    if (!thesis.invalidation?.trim()) {
      continue;
    }

    const rule = parseInvalidationRule(thesis.invalidation);
    const health = overview.health?.find(
      (chip) => chip.symbol.toUpperCase() === thesis.symbol.toUpperCase(),
    );

    const holding = overview.portfolio?.holdings.find(
      (row) => row.tradingsymbol.toUpperCase() === thesis.symbol.toUpperCase(),
    );

    const pnlPct =
      holding && holding.average_price > 0
        ? ((holding.last_price - holding.average_price) / holding.average_price) * 100
        : null;

    if (rule.kind === "price_below" && holding && holding.last_price <= rule.threshold) {
      warnings.push({
        symbol: thesis.symbol,
        message: `${thesis.symbol} at ${Math.round(holding.last_price)} — below your ${rule.threshold} invalidation.`,
        invalidation: thesis.invalidation,
        health_status: health?.grade ?? "unknown",
      });
      continue;
    }

    if (rule.kind === "drawdown_pct" && pnlPct !== null && pnlPct <= -rule.threshold) {
      warnings.push({
        symbol: thesis.symbol,
        message: `${thesis.symbol} drawdown ${Math.abs(pnlPct).toFixed(0)}% — past your ${rule.threshold}% rule.`,
        invalidation: thesis.invalidation,
        health_status: health?.grade ?? "unknown",
      });
      continue;
    }

    if (health && healthIsWeak(health.grade)) {
      warnings.push({
        symbol: thesis.symbol,
        message: `${thesis.symbol} health is ${health.grade} — revisit invalidation rule.`,
        invalidation: thesis.invalidation,
        health_status: health.grade,
      });
      continue;
    }

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
