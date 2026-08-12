"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { ExploreLiveTrigger } from "@/services/explore/liveTriggers";
import type { StockPick } from "@/types/decision";

type TriggersResponse = {
  triggers: ExploreLiveTrigger[];
};

type Options = {
  enabled: boolean;
  picks: StockPick[];
  refreshKey?: string | null;
};

const REFRESH_MS = 120_000;

function picksSignature(picks: StockPick[]): string {
  return picks
    .slice(0, 5)
    .map((pick) => `${pick.stock}:${pick.activationLevel ?? ""}`)
    .join("|");
}

export function runExploreTriggersSelfCheck(): void {
  const samplePick = {
    stock: "TCS",
    activationLevel: 4100,
    score: 80,
    signals: {},
  } as StockPick;

  const first = picksSignature([
    samplePick,
    { ...samplePick, stock: "INFY", activationLevel: 1800, score: 75 },
  ]);
  const second = picksSignature([
    samplePick,
    { ...samplePick, stock: "INFY", activationLevel: 1800, score: 70 },
  ]);

  if (first !== second) {
    throw new Error("explore triggers self-check failed: signature drift");
  }
}

export function useExploreTriggers({
  enabled,
  picks,
  refreshKey,
}: Options) {
  const [triggers, setTriggers] = useState<ExploreLiveTrigger[]>([]);
  const [loading, setLoading] = useState(false);
  const requestRef = useRef(0);
  const hasTriggersRef = useRef(false);
  const picksRef = useRef(picks);
  picksRef.current = picks;

  const signature = useMemo(() => picksSignature(picks), [picks]);

  const refresh = useCallback(async (options?: { silent?: boolean }) => {
    const activePicks = picksRef.current;

    if (!enabled || activePicks.length === 0) {
      setTriggers([]);
      hasTriggersRef.current = false;
      setLoading(false);
      return;
    }

    const requestId = ++requestRef.current;
    const silent = options?.silent ?? hasTriggersRef.current;

    if (!silent) {
      setLoading(true);
    }

    try {
      const res = await apiFetch("/api/explore/triggers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ picks: activePicks.slice(0, 5) }),
      });
      const data = await parseApiJson<TriggersResponse>(res, "Explore triggers");

      if (requestId !== requestRef.current) {
        return;
      }

      if (!res.ok || !data) {
        if (!silent) {
          setTriggers([]);
          hasTriggersRef.current = false;
        }
        return;
      }

      const nextTriggers = data.triggers ?? [];
      setTriggers((previous) => {
        if (
          previous.length === nextTriggers.length &&
          previous.every((trigger, index) => {
            const next = nextTriggers[index];
            return (
              next &&
              trigger.symbol === next.symbol &&
              trigger.livePrice === next.livePrice &&
              trigger.label === next.label &&
              trigger.liveScanLine === next.liveScanLine &&
              trigger.gapPct === next.gapPct &&
              trigger.activationLevel === next.activationLevel
            );
          })
        ) {
          return previous;
        }

        return nextTriggers;
      });
      hasTriggersRef.current = nextTriggers.length > 0;
    } catch {
      if (requestId !== requestRef.current) {
        return;
      }
      if (!silent) {
        setTriggers([]);
        hasTriggersRef.current = false;
      }
    } finally {
      if (requestId === requestRef.current) {
        setLoading(false);
      }
    }
  }, [enabled]);

  useEffect(() => {
    void refresh({ silent: hasTriggersRef.current });
  }, [refresh, refreshKey, signature]);

  useEffect(() => {
    if (!enabled || picks.length === 0) {
      return;
    }

    const timer = window.setInterval(() => {
      void refresh({ silent: true });
    }, REFRESH_MS);

    return () => {
      window.clearInterval(timer);
    };
  }, [enabled, picks.length, refresh]);

  const triggerBySymbol = useMemo(
    () => new Map(triggers.map((trigger) => [trigger.symbol, trigger])),
    [triggers],
  );

  return {
    triggers,
    triggerBySymbol,
    loading: loading && triggers.length === 0,
    refresh,
  };
}
