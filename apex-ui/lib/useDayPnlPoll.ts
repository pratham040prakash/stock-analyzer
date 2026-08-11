"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { LIVE_KITE_REFRESH_MS } from "@/lib/liveKiteRefresh";
import type { MonitorLiveTick } from "@/services/monitor/openPositions";
import type { ZerodhaPositionPnlRow } from "@/services/brokers/zerodha";
import type { PortfolioHoldingRow } from "@/types/portfolioApi";

type LivePnlResponse = {
  status?: string;
  portfolio_day_pnl: number | null;
  positions_pnl?: number | null;
  positions_breakdown?: ZerodhaPositionPnlRow[];
  holdings_live?: PortfolioHoldingRow[];
  holdings_total_value?: number | null;
  holdings_total_pnl?: number | null;
  positions_net_legs?: number;
  kite_native_pnl?: number | null;
  live_kite_status?: string;
  live_kite_message?: string;
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

function parseLiveHoldings(value: unknown): PortfolioHoldingRow[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const rows: PortfolioHoldingRow[] = [];

  for (const item of value) {
    if (
      !item ||
      typeof item !== "object" ||
      typeof (item as PortfolioHoldingRow).tradingsymbol !== "string" ||
      typeof (item as PortfolioHoldingRow).quantity !== "number" ||
      typeof (item as PortfolioHoldingRow).average_price !== "number" ||
      typeof (item as PortfolioHoldingRow).last_price !== "number" ||
      typeof (item as PortfolioHoldingRow).pnl !== "number" ||
      typeof (item as PortfolioHoldingRow).value !== "number" ||
      typeof (item as PortfolioHoldingRow).allocation_pct !== "number"
    ) {
      continue;
    }

    rows.push(item as PortfolioHoldingRow);
  }

  return rows;
}

/** @deprecated Use LIVE_KITE_REFRESH_MS */
export const DAY_PNL_REFRESH_MS = LIVE_KITE_REFRESH_MS;

export function useDayPnlPoll({ enabled }: Options) {
  const [positionsPnl, setPositionsPnl] = useState<number | null>(null);
  const [positionsBreakdown, setPositionsBreakdown] = useState<
    ZerodhaPositionPnlRow[]
  >([]);
  const [positionsNetLegs, setPositionsNetLegs] = useState(0);
  const [liveKiteStatus, setLiveKiteStatus] = useState<string | null>(null);
  const [portfolioDayPnl, setPortfolioDayPnl] = useState<number | null>(null);
  const [monitorOpenPnl, setMonitorOpenPnl] = useState<number | null>(null);
  const [positionTicks, setPositionTicks] = useState<MonitorLiveTick[]>([]);
  const [liveHoldings, setLiveHoldings] = useState<PortfolioHoldingRow[]>([]);
  const [liveHoldingsTotalValue, setLiveHoldingsTotalValue] = useState<
    number | null
  >(null);
  const [liveHoldingsTotalPnl, setLiveHoldingsTotalPnl] = useState<
    number | null
  >(null);
  const requestRef = useRef(0);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setPositionsPnl(null);
      setPositionsBreakdown([]);
      setPositionsNetLegs(0);
      setLiveKiteStatus(null);
      setPortfolioDayPnl(null);
      setMonitorOpenPnl(null);
      setPositionTicks([]);
      setLiveHoldings([]);
      setLiveHoldingsTotalValue(null);
      setLiveHoldingsTotalPnl(null);
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

      if (!res.ok || !data || data.status !== "ok") {
        return;
      }

      const positionsPnlValue =
        typeof data.positions_pnl === "number"
          ? data.positions_pnl
          : typeof data.kite_native_pnl === "number"
            ? data.kite_native_pnl
            : null;

      setPositionsPnl(positionsPnlValue);
      setPositionsBreakdown(parsePositionsBreakdown(data.positions_breakdown));
      setPositionsNetLegs(
        typeof data.positions_net_legs === "number" ? data.positions_net_legs : 0,
      );
      setLiveKiteStatus(
        typeof data.live_kite_status === "string" ? data.live_kite_status : null,
      );
      setPortfolioDayPnl(data.portfolio_day_pnl ?? null);
      setMonitorOpenPnl(data.monitor_open_pnl ?? null);
      setPositionTicks(data.position_ticks ?? []);
      setLiveHoldings(parseLiveHoldings(data.holdings_live));
      setLiveHoldingsTotalValue(
        typeof data.holdings_total_value === "number"
          ? data.holdings_total_value
          : null,
      );
      setLiveHoldingsTotalPnl(
        typeof data.holdings_total_pnl === "number"
          ? data.holdings_total_pnl
          : null,
      );
    } catch {
      // Keep the last known values on transient failures.
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
    positionsPnl,
    positionsBreakdown,
    positionsNetLegs,
    liveKiteStatus,
    portfolioDayPnl,
    monitorOpenPnl,
    positionTicks,
    liveHoldings,
    liveHoldingsTotalValue,
    liveHoldingsTotalPnl,
    refresh,
  };
}
