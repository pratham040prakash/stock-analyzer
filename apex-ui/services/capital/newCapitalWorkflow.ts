import { assemblePortfolioOverview } from "@/services/portfolio/assembleOverview";
import type { NewCapitalViewModel } from "@/types/newCapital";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { DailyDecisionArtifact } from "@/types/decision";

type Client = SupabaseClient<Database>;

/**
 * Wave 2 non-contradiction guard.
 *
 * When today's frozen artifact is locked or WAIT, new-capital guidance
 * must not invite immediate deployment. It may still surface how much
 * capital is available and the policy notes, but tranche 1 (the "act
 * now" slice) is muted with a deterministic wait reason.
 */
export function isCapitalDeploymentBlocked(
  artifact: DailyDecisionArtifact | null,
): { blocked: boolean; reason: string | null } {
  if (!artifact) {
    return {
      blocked: true,
      reason: "No frozen decision for today — hold new capital until Today authorises.",
    };
  }
  if (artifact.tradingLocked || artifact.daily_verdict !== "trade") {
    const primary = artifact.blockers[0];
    return {
      blocked: true,
      reason: primary
        ? `Today is Wait — ${primary}`
        : "Today is Wait — hold new capital deployment.",
    };
  }
  return { blocked: false, reason: null };
}

export async function assembleNewCapitalWorkflow(
  supabase: Client,
  userId: string,
  deployableInr?: number | null,
  artifact: DailyDecisionArtifact | null = null,
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

  const artifactGate = isCapitalDeploymentBlocked(artifact);
  const guidance = artifactGate.blocked
    ? artifactGate.reason ?? "Today is Wait — hold new capital deployment."
    : topHoldings.length > 0
      ? `Deploy in tranches toward policy targets — research before adding to ${topHoldings[0]}.`
      : "Build core positions gradually — one high-conviction name at a time.";

  const roundedCash = Math.round(cash);
  const trancheAmounts = [0.4, 0.35, 0.25].map((ratio) =>
    Math.round(roundedCash * ratio),
  );

  const tranches = artifactGate.blocked
    ? [
        {
          label: "Tranche 1 · hold",
          amount_inr: 0,
          note:
            artifactGate.reason ??
            "Today's decision is Wait — do not deploy new capital today.",
        },
        {
          label: "Tranche 2 · queue",
          amount_inr: trancheAmounts[1],
          note: "Queue for next authorised buy — do not act until Today authorises.",
        },
        {
          label: "Tranche 3 · reserve",
          amount_inr: trancheAmounts[2],
          note: "Hold for volatility or next monthly doctor review.",
        },
      ]
    : [
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
    message: artifactGate.blocked
      ? artifactGate.reason ?? "New capital waits for Today."
      : "New capital follows policy — not impulse.",
  };
}

export function runNewCapitalSelfCheck(): void {
  if (typeof assembleNewCapitalWorkflow !== "function") {
    throw new Error("New capital self-check failed");
  }

  const missing = isCapitalDeploymentBlocked(null);
  if (!missing.blocked || !missing.reason) {
    throw new Error(
      "New capital self-check failed: missing artifact must block deployment",
    );
  }

  const now = "2026-09-11T09:00:00.000Z";
  const tradingArtifact: DailyDecisionArtifact = {
    schema_version: "1",
    decision_id: "2026-09-11:test",
    decision_date: "2026-09-11",
    frozen_at: now,
    intent: "grow",
    action: "buy",
    symbol: { status: "known", value: "HDFCBANK", observed_at: now },
    approved_size: { kind: "buy_amount", amount_inr: 5000 },
    daily_verdict: "trade",
    tradingLocked: false,
    entryConfirmed: true,
    capital_state: {
      status: "known",
      value: { available_cash_inr: 1, portfolio_value_inr: 1 },
      observed_at: now,
    },
    broker_state: {
      status: "known",
      value: { broker: "zerodha", connection: "connected" },
      observed_at: now,
    },
    market_state: {
      status: "known",
      value: { trend: "sideways", session: "market_open" },
      observed_at: now,
    },
    source_timestamps: {
      portfolio: { status: "known", value: now, observed_at: now },
      capital: { status: "known", value: now, observed_at: now },
      broker: { status: "known", value: now, observed_at: now },
      market: { status: "known", value: now, observed_at: now },
      entry: { status: "known", value: now, observed_at: now },
    },
    evidence_ids: [],
    evidence: [],
    blockers: [],
    decision_metadata: {
      producer: "getDecision/evaluateDailyDecision",
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
    },
    frozen_portfolio: { positions: [], total_value_inr: 0, pnl_inr: 0 },
    projection: {
      decision: "BUY_MORE",
      action: "buy",
      confidence: 80,
      reason: "Buy",
      confidence_factors: [],
      actions: [],
      stock: "HDFCBANK",
      amount: 5000,
    },
  };

  const trading = isCapitalDeploymentBlocked(tradingArtifact);
  if (trading.blocked) {
    throw new Error(
      "New capital self-check failed: trade-authorised artifact must not block",
    );
  }

  const locked = isCapitalDeploymentBlocked({
    ...tradingArtifact,
    tradingLocked: true,
    daily_verdict: "wait",
    blockers: ["Capital unknown"],
  });
  if (!locked.blocked || !locked.reason) {
    throw new Error(
      "New capital self-check failed: locked artifact must block deployment",
    );
  }
}
