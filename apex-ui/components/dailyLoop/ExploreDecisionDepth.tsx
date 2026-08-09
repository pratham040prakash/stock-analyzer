"use client";

import { useMemo } from "react";
import { buildDecisionDepth } from "@/lib/dailyLoop/decisionDepth";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  SystemContextLine,
  WatchSection,
  WhySection,
} from "@/components/dailyLoop/DecisionDepthSections";
import type { HomeDecision } from "@/components/HomeDecisionScreen";
import type { UserIntent } from "@/types/intent";
import type { ExecutionPlanConviction } from "@/services/execution/executionPlanEngine";
import { formatSetupWatchInsight } from "@/lib/dailyLoop/setupInsight";

type Props = {
  decision: HomeDecision;
  intent: UserIntent;
  entryTiming: EntryTimingState;
  topSymbol?: string;
  topAllocationPct?: number;
  planConviction?: ExecutionPlanConviction;
  delayMs: number;
};

export default function ExploreDecisionDepth({
  decision,
  intent,
  entryTiming,
  topSymbol,
  topAllocationPct,
  planConviction,
  delayMs,
}: Props) {
  const depth = useMemo(
    () =>
      buildDecisionDepth({
        action: decision.action,
        stock: decision.stock ?? topSymbol,
        confidence: decision.confidence,
        structureScore: decision.structureScore,
        reason: decision.reason,
        message: decision.message,
        confidence_factors: decision.confidence_factors,
        validation: decision.validation,
        confidenceMetrics: decision.confidenceMetrics,
        picks: decision.picks,
        allocation: decision.allocation,
        suggested_sell_percent: decision.suggested_sell_percent,
        allocationPercent: decision.allocationPercent,
        allocationReason: decision.allocationReason,
        intent,
        entryTiming,
        planConviction,
        topSymbol,
        topAllocationPct,
      }),
    [
      decision,
      entryTiming,
      intent,
      planConviction,
      topAllocationPct,
      topSymbol,
    ],
  );

  let sectionDelay = delayMs;

  const nextDelay = () => {
    const value = sectionDelay;
    sectionDelay += 80;
    return value;
  };

  if (
    depth.whyBullets.length === 0 &&
    depth.watchNext.length === 0 &&
    !depth.systemContext
  ) {
    return null;
  }

  return (
    <div className="space-y-2">
      <WhySection bullets={depth.whyBullets} delayMs={nextDelay()} />
      <WatchSection items={depth.watchNext} delayMs={nextDelay()} />
      <SystemContextLine depth={depth} delayMs={nextDelay()} />
      {depth.exploreSetupItems.length > 0 ? (
        <section
          className="rounded-xl border border-apex-border/10 bg-white/[0.02] px-4 py-3 animate-apex-fade-in"
          style={{ animationDelay: `${nextDelay()}ms` }}
        >
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Setup insight
          </p>
          <ul className="mt-2 space-y-2 text-sm leading-snug text-apex-text/80">
            {(decision.picks ?? []).slice(0, 3).map((pick, index) => {
              const item = depth.exploreSetupItems[index];
              if (!item) {
                return null;
              }

              return (
                <li key={pick.stock}>
                  <span className="font-medium text-apex-text/90">{pick.stock}</span>
                  {" — "}
                  {formatSetupWatchInsight(item)}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
