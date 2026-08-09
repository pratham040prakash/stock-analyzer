"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
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
  const [dayPnl, setDayPnl] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const requestRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setPositions([]);
      setDayPnl(null);
      return;
    }

    const requestId = ++requestRef.current;
    setLoading(true);

    try {
      const res = await apiFetch("/api/monitor/open", { method: "GET" });
      const data = await parseApiJson<MonitorResponse>(res, "Open monitor");

      if (requestId !== requestRef.current) {
        return;
      }

      if (!res.ok || !data) {
        setPositions([]);
        setDayPnl(null);
        return;
      }

      setPositions(data.positions ?? []);
      setDayPnl(data.dayPnl ?? null);
    } catch {
      if (requestId !== requestRef.current) {
        return;
      }
      setPositions([]);
      setDayPnl(null);
    } finally {
      if (requestId === requestRef.current) {
        setLoading(false);
      }
    }
  }, [enabled]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    positions,
    dayPnl: dayPnl,
    loading,
    refresh,
  };
}
