"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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

export function useExploreTriggers({
  enabled,
  picks,
  refreshKey,
}: Options) {
  const [triggers, setTriggers] = useState<ExploreLiveTrigger[]>([]);
  const [loading, setLoading] = useState(false);
  const requestRef = useRef(0);
  const hasTriggersRef = useRef(false);

  const refresh = useCallback(async (options?: { silent?: boolean }) => {
    if (!enabled || picks.length === 0) {
      setTriggers([]);
      hasTriggersRef.current = false;
      return;
    }

    const requestId = ++requestRef.current;
    const silent = options?.silent ?? false;

    if (!silent || !hasTriggersRef.current) {
      setLoading(true);
    }

    try {
      const res = await apiFetch("/api/explore/triggers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ picks: picks.slice(0, 5) }),
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
      setTriggers(nextTriggers);
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
  }, [enabled, picks]);

  useEffect(() => {
    void refresh();
  }, [refresh, refreshKey]);

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

  const triggerBySymbol = useCallback(() => {
    return new Map(triggers.map((trigger) => [trigger.symbol, trigger]));
  }, [triggers]);

  return {
    triggers,
    triggerBySymbol: triggerBySymbol(),
    loading,
    refresh,
  };
}
