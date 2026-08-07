"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createOptimisticDecision } from "@/lib/decisionOptimistic";
import { readStoredUserIntent, storeUserIntent } from "@/lib/userIntent";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { DailyDecisionOutput } from "@/types/decision";
import { decisionTodayApiPath, resolveIntent, type Intent } from "@/types/intent";

type DecisionResponse = {
  decision: DailyDecisionOutput | null;
};

type PortfolioContext = {
  stock?: string;
  allocation?: number;
};

type Options = {
  enabled: boolean;
  portfolioContext?: PortfolioContext;
  onFetched?: () => void;
};

export function useIntentDecision({
  enabled,
  portfolioContext,
  onFetched,
}: Options) {
  const initialIntent = resolveIntent(readStoredUserIntent());

  const [intent, setIntentState] = useState<Intent>(initialIntent);
  const [decision, setDecision] = useState<DailyDecisionOutput>(() =>
    createOptimisticDecision(initialIntent, portfolioContext ?? {}),
  );
  const [isRefreshing, setIsRefreshing] = useState(enabled);

  const cacheRef = useRef<Partial<Record<Intent, DailyDecisionOutput>>>({});
  const intentRef = useRef(intent);
  const portfolioContextRef = useRef(portfolioContext);
  const onFetchedRef = useRef(onFetched);

  intentRef.current = intent;
  portfolioContextRef.current = portfolioContext;
  onFetchedRef.current = onFetched;

  const setIntent = useCallback((next: Intent) => {
    setIntentState(next);
    storeUserIntent(next);

    const cached = cacheRef.current[next];
    if (cached) {
      setDecision(cached);
      setIsRefreshing(false);
      return;
    }

    setDecision(
      createOptimisticDecision(next, portfolioContextRef.current ?? {}),
    );
    setIsRefreshing(true);
  }, []);

  const fetchDecision = useCallback(
    async (targetIntent: Intent, options?: { force?: boolean }) => {
      if (!enabled) return;

      const cached = cacheRef.current[targetIntent];
      if (cached && !options?.force) {
        if (intentRef.current === targetIntent) {
          setDecision(cached);
          setIsRefreshing(false);
        }
        return;
      }

      if (intentRef.current === targetIntent) {
        setIsRefreshing(true);
      }

      try {
        const res = await apiFetch(decisionTodayApiPath(targetIntent), {
          method: "GET",
        });
        const data = await parseApiJson<DecisionResponse>(
          res,
          "Daily decision",
        );

        if (intentRef.current !== targetIntent) {
          return;
        }

        if (data?.decision) {
          cacheRef.current[targetIntent] = data.decision;
          setDecision(data.decision);
          onFetchedRef.current?.();
        }
      } catch {
        // Keep optimistic decision visible on failure.
      } finally {
        if (intentRef.current === targetIntent) {
          setIsRefreshing(false);
        }
      }
    },
    [enabled],
  );

  const refreshDecision = useCallback(() => {
    delete cacheRef.current[intentRef.current];
    void fetchDecision(intentRef.current, { force: true });
  }, [fetchDecision]);

  useEffect(() => {
    if (!enabled) {
      setIsRefreshing(false);
      return;
    }

    void fetchDecision(intent);
  }, [enabled, intent, fetchDecision]);

  return {
    intent,
    setIntent,
    decision,
    isRefreshing,
    refreshDecision,
  };
}
