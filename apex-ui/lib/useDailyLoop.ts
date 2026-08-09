"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import { getDecisionActionText } from "@/lib/dailyLoop/actionText";
import {
  persistLastOutcome,
  persistTrustUpdate,
  readLastOutcome,
  readTrustDelta,
  readTrustScore,
} from "@/lib/dailyLoop/storage";
import { buildExecutionPlanInput } from "@/services/execution/buildExecutionPlanInput";
import {
  generateExecutionPlanSafe,
  type ExecutionPlanSafeOutput,
} from "@/services/execution/executionPlanEngine";
import type { OutcomeEvaluationOutput } from "@/services/learning/outcomeEngine";
import { getTrustDisplay } from "@/services/learning/trustEngine";
import type { StockPick } from "@/types/decision";
import type { UserIntent } from "@/types/intent";

export type DailyLoopDecision = {
  action: string;
  stock?: string;
  amount?: number;
  structureScore?: number;
  confidence?: number;
  reason?: string;
  message?: string;
  confidence_factors?: string[];
  validation?: {
    risk_ok?: boolean;
  };
  confidenceMetrics?: {
    probability?: number;
  };
  picks?: StockPick[];
};

type DailyLoopState = {
  actionText: string;
  plan: ExecutionPlanSafeOutput | null;
  planLoading: boolean;
  trustScore: number;
  trustDelta: number;
  trustMessage: string;
  lastOutcome: OutcomeEvaluationOutput | null;
  lastOutcomeStock: string | null;
  refreshTrust: () => Promise<void>;
};

type TrustOutcomeApiResponse = {
  status: string;
  trust?: {
    trustScore: number;
    trustDelta: number;
    trustMessage: string;
    lastOutcome: OutcomeEvaluationOutput | null;
    lastClosedAt: string | null;
    stock: string | null;
  };
};

async function fetchTrustOutcomeFromServer(): Promise<
  TrustOutcomeApiResponse["trust"] | null
> {
  try {
    const response = await fetch("/api/trust/outcome", { cache: "no-store" });

    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as TrustOutcomeApiResponse;

    if (payload.status !== "ok" || !payload.trust) {
      return null;
    }

    return payload.trust;
  } catch {
    return null;
  }
}

export function useDailyLoop(
  decision: DailyLoopDecision,
  entryTiming: EntryTimingState,
  intent: UserIntent,
): DailyLoopState {
  const [plan, setPlan] = useState<ExecutionPlanSafeOutput | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [trustScore, setTrustScore] = useState(50);
  const [trustDelta, setTrustDelta] = useState(0);
  const [trustMessage, setTrustMessage] = useState(
    () => getTrustDisplay(readTrustScore()).message,
  );
  const [lastOutcome, setLastOutcome] = useState<OutcomeEvaluationOutput | null>(
    null,
  );
  const [lastOutcomeStock, setLastOutcomeStock] = useState<string | null>(null);

  const applyServerTrust = useCallback(
    (serverTrust: NonNullable<TrustOutcomeApiResponse["trust"]>) => {
      persistTrustUpdate(serverTrust.trustScore, serverTrust.trustDelta);

      if (serverTrust.lastOutcome) {
        persistLastOutcome(serverTrust.lastOutcome);
      }

      setTrustScore(serverTrust.trustScore);
      setTrustDelta(serverTrust.trustDelta);
      setTrustMessage(serverTrust.trustMessage);
      setLastOutcome(serverTrust.lastOutcome);
      setLastOutcomeStock(serverTrust.stock);
    },
    [],
  );

  const refreshTrust = useCallback(async () => {
    const serverTrust = await fetchTrustOutcomeFromServer();

    if (!serverTrust) {
      return;
    }

    applyServerTrust(serverTrust);
  }, [applyServerTrust]);

  const actionText = useMemo(
    () => getDecisionActionText(decision, entryTiming, intent),
    [decision, entryTiming, intent],
  );

  useEffect(() => {
    setTrustScore(readTrustScore());
    setTrustDelta(readTrustDelta());
    setLastOutcome(readLastOutcome());
    setTrustMessage(getTrustDisplay(readTrustScore()).message);

    let cancelled = false;

    void (async () => {
      const serverTrust = await fetchTrustOutcomeFromServer();

      if (cancelled || !serverTrust) {
        return;
      }

      applyServerTrust(serverTrust);
    })();

    return () => {
      cancelled = true;
    };
  }, [applyServerTrust]);

  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void refreshTrust();
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [refreshTrust]);

  useEffect(() => {
    const shouldLoadPlan =
      intent === "grow" &&
      decision.action === "buy" &&
      Boolean(decision.stock);

    if (!shouldLoadPlan) {
      setPlan(null);
      setPlanLoading(false);
      return;
    }

    let cancelled = false;
    setPlanLoading(true);
    setPlan(null);

    void (async () => {
      const input = await buildExecutionPlanInput(decision, {
        entryTiming,
        intent,
      });

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
  }, [decision, entryTiming, intent]);

  return {
    actionText,
    plan,
    planLoading,
    trustScore,
    trustDelta,
    trustMessage,
    lastOutcome,
    lastOutcomeStock,
    refreshTrust,
  };
}
