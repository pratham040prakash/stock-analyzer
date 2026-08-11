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

  const refresh = useCallback(async () => {
    if (!enabled) {
      setPositions([]);
      return;
    }

    const requestId = ++requestRef.current;
    setLoading(true);

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

      setPositions(data.positions ?? []);
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
      void refreshRef.current();
    }, LIVE_KITE_REFRESH_MS);

    return () => window.clearInterval(intervalId);
  }, [enabled]);

  return {
    positions,
    loading,
    refresh,
  };
}
