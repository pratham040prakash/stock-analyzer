"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { MorningBriefResponse, MorningBriefViewModel } from "@/types/morningBrief";
import type { UserIntent } from "@/types/intent";

type Options = {
  enabled: boolean;
  intent: UserIntent;
  refreshKey?: string | null;
};

export function useMorningBrief({ enabled, intent, refreshKey }: Options) {
  const [brief, setBrief] = useState<MorningBriefViewModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setBrief(null);
      setError(null);
      return;
    }

    const requestId = ++requestRef.current;
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch(
        `/api/today/brief?intent=${encodeURIComponent(intent)}`,
        { cache: "no-store" },
      );
      const data = await parseApiJson<MorningBriefResponse>(
        response,
        "Morning brief",
      );

      if (requestId !== requestRef.current) {
        return;
      }

      if (!response.ok || !data?.brief) {
        setError(data?.message ?? "Could not load morning brief.");
        return;
      }

      setBrief(data.brief);
      if (data.brief.failure_message) {
        setError(data.brief.failure_message);
      }
    } catch (loadError) {
      if (requestId === requestRef.current) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Could not load morning brief.",
        );
      }
    } finally {
      if (requestId === requestRef.current) {
        setLoading(false);
      }
    }
  }, [enabled, intent]);

  useEffect(() => {
    void refresh();
  }, [refresh, refreshKey]);

  return {
    brief,
    loading,
    error,
    refresh,
  };
}
