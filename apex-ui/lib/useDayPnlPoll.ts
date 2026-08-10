"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { isNseCashSessionOpen } from "@/lib/broker/marketSession";

type DayPnlResponse = {
  day_pnl: number | null;
};

type Options = {
  enabled: boolean;
};

export const DAY_PNL_REFRESH_MS = 5_000;

export function useDayPnlPoll({ enabled }: Options) {
  const [dayPnl, setDayPnl] = useState<number | null>(null);
  const requestRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setDayPnl(null);
      return;
    }

    const requestId = ++requestRef.current;

    try {
      const res = await apiFetch("/api/portfolio/day-pnl", {
        method: "GET",
        cache: "no-store",
      });
      const data = await parseApiJson<DayPnlResponse>(res, "Day P&L");

      if (requestId !== requestRef.current) {
        return;
      }

      if (!res.ok || !data) {
        return;
      }

      setDayPnl(data.day_pnl ?? null);
    } catch {
      // Keep the last known value on transient failures.
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

  return { dayPnl, refresh };
}
