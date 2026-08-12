"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { LIVE_KITE_REFRESH_MS } from "@/lib/liveKiteRefresh";
import type { OpenMonitorPosition } from "@/services/monitor/openPositions";

type MonitorResponse = {
  positions: OpenMonitorPosition[];
  dayPnl: number | null;
};

type Options = {
  enabled: boolean;
};

export function useOpenMonitor({ enabled }: Options) {
  const [positions, setPositions] = useState<OpenMonitorPosition[]>([]);
  const [loading, setLoading] = useState(false);
  const requestRef = useRef(0);
  const hasPositionsRef = useRef(false);

  const refresh = useCallback(async (options?: { silent?: boolean }) => {
    if (!enabled) {
      setPositions([]);
      hasPositionsRef.current = false;
      return;
    }

    const requestId = ++requestRef.current;
    const silent = options?.silent ?? false;

    if (!silent || !hasPositionsRef.current) {
      setLoading(true);
    }

    try {
      const res = await apiFetch("/api/monitor/open", {
        method: "GET",
        cache: "no-store",
      });
      const data = await parseApiJson<MonitorResponse>(res, "Open monitor");

      if (requestId !== requestRef.current) {
        return;
      }

      if (!res.ok || !data) {
        return;
      }

      const nextPositions = data.positions ?? [];
      setPositions(nextPositions);
      hasPositionsRef.current = nextPositions.length > 0;
    } catch {
      // Keep last-known positions on transient failures.
    } finally {
      if (requestId === requestRef.current) {
        setLoading(false);
      }
    }
  }, [enabled]);

  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;

  useEffect(() => {
    void refreshRef.current();
  }, [refresh]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void refreshRef.current({ silent: true });
    }, LIVE_KITE_REFRESH_MS);

    return () => window.clearInterval(intervalId);
  }, [enabled]);

  return {
    positions,
    loading,
    refresh,
  };
}
