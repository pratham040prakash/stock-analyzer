"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { isNseCashSessionOpen } from "@/lib/broker/marketSession";

type LivePnlResponse = {
  portfolio_day_pnl: number | null;
  monitor_day_pnl: number | null;
};

type Options = {
  enabled: boolean;
};

/** One shared poll — avoids duplicate Kite calls (rate limits). */
export const DAY_PNL_REFRESH_MS = 5_000;

export function useDayPnlPoll({ enabled }: Options) {
  const [portfolioDayPnl, setPortfolioDayPnl] = useState<number | null>(null);
  const [monitorDayPnl, setMonitorDayPnl] = useState<number | null>(null);
  const requestRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setPortfolioDayPnl(null);
      setMonitorDayPnl(null);
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

      setPortfolioDayPnl(data.portfolio_day_pnl ?? null);
      setMonitorDayPnl(data.monitor_day_pnl ?? null);
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

  return { portfolioDayPnl, monitorDayPnl, refresh };
}
