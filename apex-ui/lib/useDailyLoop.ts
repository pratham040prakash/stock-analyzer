"use client";

import { useEffect, useMemo, useState } from "react";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import { getDecisionActionText } from "@/lib/dailyLoop/actionText";
import { readLastOutcome, readTrustDelta, readTrustScore } from "@/lib/dailyLoop/storage";
import { buildExecutionPlanInput } from "@/services/execution/buildExecutionPlanInput";
import {
  generateExecutionPlanSafe,
  type ExecutionPlanSafeOutput,
} from "@/services/execution/executionPlanEngine";
import type { OutcomeEvaluationOutput } from "@/services/learning/outcomeEngine";
import { getTrustDisplay } from "@/services/learning/trustEngine";

export type DailyLoopDecision = {
  action: string;
  stock?: string;
  amount?: number;
  structureScore?: number;
  confidence?: number;
  confidenceMetrics?: {
    probability?: number;
  };
};

type DailyLoopState = {
  actionText: string;
  plan: ExecutionPlanSafeOutput | null;
  planLoading: boolean;
  trustScore: number;
  trustDelta: number;
  trustMessage: string;
  lastOutcome: OutcomeEvaluationOutput | null;
};

export function useDailyLoop(
  decision: DailyLoopDecision,
  entryTiming: EntryTimingState,
): DailyLoopState {
  const [plan, setPlan] = useState<ExecutionPlanSafeOutput | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [trustScore, setTrustScore] = useState(50);
  const [trustDelta, setTrustDelta] = useState(0);
  const [lastOutcome, setLastOutcome] = useState<OutcomeEvaluationOutput | null>(
    null,
  );

  const actionText = useMemo(
    () => getDecisionActionText(decision, entryTiming),
    [decision, entryTiming],
  );

  const trustMessage = useMemo(
    () => getTrustDisplay(trustScore).message,
    [trustScore],
  );

  useEffect(() => {
    setTrustScore(readTrustScore());
    setTrustDelta(readTrustDelta());
    setLastOutcome(readLastOutcome());
  }, []);

  useEffect(() => {
    if (decision.action !== "buy" || !decision.stock) {
      setPlan(null);
      setPlanLoading(false);
      return;
    }

    let cancelled = false;
    setPlanLoading(true);
    setPlan(null);

    void (async () => {
      const input = await buildExecutionPlanInput(decision, { entryTiming });

      if (cancelled) {
        return;
      }

      if (input) {
        setPlan(generateExecutionPlanSafe(input));
      }

      setPlanLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [decision, entryTiming]);

  return {
    actionText,
    plan,
    planLoading,
    trustScore,
    trustDelta,
    trustMessage,
    lastOutcome,
  };
}
