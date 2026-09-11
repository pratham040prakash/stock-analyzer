"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createLoadingDecision } from "@/lib/decisionOptimistic";
import { readStoredUserIntent, storeUserIntent } from "@/lib/userIntent";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { DailyDecisionOutput } from "@/types/decision";
import { decisionTodayApiPath, resolveIntent, type Intent } from "@/types/intent";

/**
 * Wave 2 invariant: intent is a presentation lens over the frozen
 * artifact. The client may switch intent locally, but the server never
 * produces a per-intent replacement without an explicit refresh
 * (?refresh=1). When the API returns an artifact whose intent differs
 * from the requested one, the hook adopts the artifact's true intent
 * so the UI stops pretending to hold a different one.
 */

export type EntryTimingState = {
  enter: boolean;
  reason: string;
};

type DecisionResponse = {
  decision: DailyDecisionOutput | null;
  entryTiming?: EntryTimingState;
  created_at?: string | null;
  intent?: Intent | null;
  daily_verdict?: "trade" | "wait" | "pause" | null;
  trading_locked?: boolean | null;
  entry_confirmed?: boolean | null;
  blockers?: string[];
};

const DEFAULT_ENTRY_TIMING: EntryTimingState = {
  enter: false,
  reason: "Waiting for confirmation",
};

type PortfolioContext = {
  stock?: string;
  allocation?: number;
  availableCash?: number;
  riskLevel?: import("@/lib/portfolioRisk").PortfolioRiskLevel;
  holdings?: { symbol: string; allocation_pct?: number }[];
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
    createLoadingDecision(),
  );
  const [isRefreshing, setIsRefreshing] = useState(enabled);
  const [entryTiming, setEntryTiming] = useState<EntryTimingState>(
    DEFAULT_ENTRY_TIMING,
  );
  const [decisionUpdatedAt, setDecisionUpdatedAt] = useState<string | null>(
    null,
  );

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

    setDecision(createLoadingDecision());
    setIsRefreshing(true);
  }, []);

  const fetchDecision = useCallback(
    async (
      targetIntent: Intent,
      options?: { force?: boolean; silent?: boolean },
    ) => {
      if (!enabled) return;

      const cached = cacheRef.current[targetIntent];
      if (cached && !options?.force) {
        if (intentRef.current === targetIntent) {
          setDecision(cached);
          setIsRefreshing(false);
        }
        return;
      }

      const keepVisibleWhileRefreshing =
        Boolean(options?.silent && cached);

      if (intentRef.current === targetIntent && !keepVisibleWhileRefreshing) {
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
          const artifactIntent = resolveIntent(data.intent ?? null);
          cacheRef.current[targetIntent] = data.decision;
          if (artifactIntent !== targetIntent) {
            cacheRef.current[artifactIntent] = data.decision;
            setIntentState(artifactIntent);
            storeUserIntent(artifactIntent);
            intentRef.current = artifactIntent;
          }
          setDecision(data.decision);
          setEntryTiming(data.entryTiming ?? DEFAULT_ENTRY_TIMING);
          setDecisionUpdatedAt(data.created_at ?? new Date().toISOString());
          onFetchedRef.current?.();
        }
      } catch {
        if (intentRef.current === targetIntent && !options?.silent) {
          setDecision(createLoadingDecision());
        }
      } finally {
        if (intentRef.current === targetIntent) {
          setIsRefreshing(false);
        }
      }
    },
    [enabled],
  );

  const refreshDecision = useCallback((options?: { silent?: boolean }) => {
    if (!options?.silent) {
      delete cacheRef.current[intentRef.current];
    }
    void fetchDecision(intentRef.current, {
      force: true,
      silent: options?.silent,
    });
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
    entryTiming,
    decisionUpdatedAt,
    isRefreshing,
    refreshDecision,
  };
}
