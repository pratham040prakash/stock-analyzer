"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { isNseCashSessionOpen } from "@/lib/broker/marketSession";
import type { MonitorLiveTick } from "@/services/monitor/openPositions";

type LivePnlResponse = {
  portfolio_day_pnl: number | null;
  positions_pnl?: number | null;
  monitor_open_pnl?: number | null;
  monitor_day_pnl: number | null;
  position_ticks?: MonitorLiveTick[];
};

type Options = {
  enabled: boolean;
};

/** One shared poll — avoids duplicate Kite calls (rate limits). */
export const DAY_PNL_REFRESH_MS = 5_000;

export function useDayPnlPoll({ enabled }: Options) {
  const [positionsPnl, setPositionsPnl] = useState<number | null>(null);
  const [portfolioDayPnl, setPortfolioDayPnl] = useState<number | null>(null);
  const [monitorOpenPnl, setMonitorOpenPnl] = useState<number | null>(null);
  const [positionTicks, setPositionTicks] = useState<MonitorLiveTick[]>([]);
  const requestRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setPositionsPnl(null);
      setPortfolioDayPnl(null);
      setMonitorOpenPnl(null);
      setPositionTicks([]);
      return;
    }

    const requestId = ++requestRef.current;

    try {
      const res = await apiFetch("/api/today/pnl", {
        method: "GET",
        cache: "no-store",
      });
      const data = await parseApiJson<LivePnlResponse>(res, "Day P&L");

      if (requestId !== requestRef.current) {
        return;
      }

      if (!res.ok || !data) {
        return;
      }

      setPositionsPnl(
        typeof data.positions_pnl === "number" ? data.positions_pnl : null,
      );
      setPortfolioDayPnl(data.portfolio_day_pnl ?? null);
      setMonitorOpenPnl(data.monitor_open_pnl ?? null);
      setPositionTicks(data.position_ticks ?? []);
    } catch {
      // Keep the last known values on transient failures.
    }
  }, [enabled]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const tick = () => {
      if (isNseCashSessionOpen()) {
        void refresh();
      }
    };

    const intervalId = window.setInterval(tick, DAY_PNL_REFRESH_MS);
    return () => window.clearInterval(intervalId);
  }, [enabled, refresh]);

  return { positionsPnl, portfolioDayPnl, monitorOpenPnl, positionTicks, refresh };
}
