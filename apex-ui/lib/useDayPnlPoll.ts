"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { MonitorLiveTick } from "@/services/monitor/openPositions";
import type { ZerodhaPositionPnlRow } from "@/services/brokers/zerodha";

type LivePnlResponse = {
  portfolio_day_pnl: number | null;
  positions_pnl?: number | null;
  positions_breakdown?: ZerodhaPositionPnlRow[];
  monitor_open_pnl?: number | null;
  monitor_day_pnl: number | null;
  position_ticks?: MonitorLiveTick[];
};

type Options = {
  enabled: boolean;
};

function parsePositionsBreakdown(value: unknown): ZerodhaPositionPnlRow[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const rows: ZerodhaPositionPnlRow[] = [];

  for (const item of value) {
    if (
      !item ||
      typeof item !== "object" ||
      typeof (item as ZerodhaPositionPnlRow).symbol !== "string" ||
      typeof (item as ZerodhaPositionPnlRow).quantity !== "number" ||
      typeof (item as ZerodhaPositionPnlRow).average_price !== "number" ||
      typeof (item as ZerodhaPositionPnlRow).last_price !== "number" ||
      typeof (item as ZerodhaPositionPnlRow).pnl !== "number"
    ) {
      continue;
    }

    rows.push(item as ZerodhaPositionPnlRow);
  }

  return rows;
}

/** One shared poll — avoids duplicate Kite calls (rate limits). */
export const DAY_PNL_REFRESH_MS = 5_000;

export function useDayPnlPoll({ enabled }: Options) {
  const [positionsPnl, setPositionsPnl] = useState<number | null>(null);
  const [positionsBreakdown, setPositionsBreakdown] = useState<
    ZerodhaPositionPnlRow[]
  >([]);
  const [portfolioDayPnl, setPortfolioDayPnl] = useState<number | null>(null);
  const [monitorOpenPnl, setMonitorOpenPnl] = useState<number | null>(null);
  const [positionTicks, setPositionTicks] = useState<MonitorLiveTick[]>([]);
  const requestRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setPositionsPnl(null);
      setPositionsBreakdown([]);
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
      setPositionsBreakdown(parsePositionsBreakdown(data.positions_breakdown));
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

    const intervalId = window.setInterval(() => {
      void refresh();
    }, DAY_PNL_REFRESH_MS);
    return () => window.clearInterval(intervalId);
  }, [enabled, refresh]);

  return {
    positionsPnl,
    positionsBreakdown,
    portfolioDayPnl,
    monitorOpenPnl,
    positionTicks,
    refresh,
  };
}
