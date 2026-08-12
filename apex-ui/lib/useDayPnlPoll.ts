"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { LIVE_KITE_REFRESH_MS } from "@/lib/liveKiteRefresh";
import {
  liveHoldingsSnapshotEqual,
  positionTicksSnapshotEqual,
  positionsBreakdownSnapshotEqual,
} from "@/lib/livePortfolioSnapshot";
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

function clearLivePnlState(setters: {
  setPositionsPnl: (value: number | null) => void;
  setPositionsBreakdown: (value: ZerodhaPositionPnlRow[]) => void;
  setPositionsNetLegs: (value: number) => void;
  setLiveKiteStatus: (value: string | null) => void;
  setPortfolioDayPnl: (value: number | null) => void;
  setMonitorOpenPnl: (value: number | null) => void;
  setPositionTicks: (value: MonitorLiveTick[]) => void;
  setLiveHoldings: (value: PortfolioHoldingRow[]) => void;
  setLiveHoldingsTotalValue: (value: number | null) => void;
  setLiveHoldingsTotalPnl: (value: number | null) => void;
  setLastSyncedAt: (value: string | null) => void;
}) {
  setters.setPositionsPnl(null);
  setters.setPositionsBreakdown([]);
  setters.setPositionsNetLegs(0);
  setters.setLiveKiteStatus(null);
  setters.setPortfolioDayPnl(null);
  setters.setMonitorOpenPnl(null);
  setters.setPositionTicks([]);
  setters.setLiveHoldings([]);
  setters.setLiveHoldingsTotalValue(null);
  setters.setLiveHoldingsTotalPnl(null);
  setters.setLastSyncedAt(null);
}

/** @deprecated Use LIVE_KITE_REFRESH_MS */
export const DAY_PNL_REFRESH_MS = LIVE_KITE_REFRESH_MS;

const POLL_FAILURE_THRESHOLD = 1;

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
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const requestRef = useRef(0);
  const failureCountRef = useRef(0);
  const hasLiveDataRef = useRef(false);
  const liveHoldingsRef = useRef<PortfolioHoldingRow[]>([]);
  const positionsBreakdownRef = useRef<ZerodhaPositionPnlRow[]>([]);
  const positionTicksRef = useRef<MonitorLiveTick[]>([]);
  const portfolioDayPnlRef = useRef<number | null>(null);
  const positionsPnlRef = useRef<number | null>(null);
  const monitorOpenPnlRef = useRef<number | null>(null);
  const liveHoldingsTotalValueRef = useRef<number | null>(null);
  const liveHoldingsTotalPnlRef = useRef<number | null>(null);

  const refresh = useCallback(async (options?: { silent?: boolean }) => {
    if (!enabled) {
      clearLivePnlState({
        setPositionsPnl,
        setPositionsBreakdown,
        setPositionsNetLegs,
        setLiveKiteStatus,
        setPortfolioDayPnl,
        setMonitorOpenPnl,
        setPositionTicks,
        setLiveHoldings,
        setLiveHoldingsTotalValue,
        setLiveHoldingsTotalPnl,
        setLastSyncedAt,
      });
      setPollError(null);
      failureCountRef.current = 0;
      setIsPolling(false);
      return;
    }

    const requestId = ++requestRef.current;
    if (!options?.silent || !hasLiveDataRef.current) {
      setIsPolling(true);
    }

    try {
      const res = await apiFetch("/api/today/pnl", {
        method: "GET",
        cache: "no-store",
      });
      const data = await parseApiJson<LivePnlResponse>(res, "Day P&L");

      if (requestId !== requestRef.current) {
        return;
      }

      if (data?.live_kite_status === "TOKEN_EXPIRED") {
        clearLivePnlState({
          setPositionsPnl,
          setPositionsBreakdown,
          setPositionsNetLegs,
          setLiveKiteStatus,
          setPortfolioDayPnl,
          setMonitorOpenPnl,
          setPositionTicks,
          setLiveHoldings,
          setLiveHoldingsTotalValue,
          setLiveHoldingsTotalPnl,
          setLastSyncedAt,
        });
        setLiveKiteStatus("TOKEN_EXPIRED");
        setPollError("Zerodha session expired — reconnect to refresh live P&L.");
        failureCountRef.current = 0;
        setIsPolling(false);
        return;
      }

      if (!res.ok || !data || data.status !== "ok") {
        failureCountRef.current += 1;
        if (failureCountRef.current >= POLL_FAILURE_THRESHOLD) {
          setPollError("Live P&L sync failed — showing last known values.");
        }
        setIsPolling(false);
        return;
      }

      failureCountRef.current = 0;
      setPollError(null);
      hasLiveDataRef.current = true;

      const positionsPnlValue =
        typeof data.positions_pnl === "number"
          ? data.positions_pnl
          : typeof data.kite_native_pnl === "number"
            ? data.kite_native_pnl
            : null;
      const nextPositionsBreakdown = parsePositionsBreakdown(data.positions_breakdown);
      const nextLiveHoldings = parseLiveHoldings(data.holdings_live);
      const nextPositionTicks = data.position_ticks ?? [];
      const nextPortfolioDayPnl = data.portfolio_day_pnl ?? null;
      const nextMonitorOpenPnl = data.monitor_open_pnl ?? null;
      const nextLiveHoldingsTotalValue =
        typeof data.holdings_total_value === "number"
          ? data.holdings_total_value
          : null;
      const nextLiveHoldingsTotalPnl =
        typeof data.holdings_total_pnl === "number"
          ? data.holdings_total_pnl
          : null;

      const holdingsChanged = !liveHoldingsSnapshotEqual(
        liveHoldingsRef.current,
        nextLiveHoldings,
      );
      const breakdownChanged = !positionsBreakdownSnapshotEqual(
        positionsBreakdownRef.current,
        nextPositionsBreakdown,
      );
      const ticksChanged = !positionTicksSnapshotEqual(
        positionTicksRef.current,
        nextPositionTicks,
      );
      const positionsPnlChanged = positionsPnlRef.current !== positionsPnlValue;
      const portfolioDayPnlChanged = portfolioDayPnlRef.current !== nextPortfolioDayPnl;
      const monitorOpenPnlChanged = monitorOpenPnlRef.current !== nextMonitorOpenPnl;
      const totalValueChanged =
        liveHoldingsTotalValueRef.current !== nextLiveHoldingsTotalValue;
      const totalPnlChanged =
        liveHoldingsTotalPnlRef.current !== nextLiveHoldingsTotalPnl;

      if (
        !holdingsChanged &&
        !breakdownChanged &&
        !ticksChanged &&
        !positionsPnlChanged &&
        !portfolioDayPnlChanged &&
        !monitorOpenPnlChanged &&
        !totalValueChanged &&
        !totalPnlChanged
      ) {
        setIsPolling(false);
        return;
      }

      if (positionsPnlChanged) {
        positionsPnlRef.current = positionsPnlValue;
        setPositionsPnl(positionsPnlValue);
      }

      if (breakdownChanged) {
        positionsBreakdownRef.current = nextPositionsBreakdown;
        setPositionsBreakdown(nextPositionsBreakdown);
      }

      setPositionsNetLegs(
        typeof data.positions_net_legs === "number" ? data.positions_net_legs : 0,
      );
      setLiveKiteStatus(
        typeof data.live_kite_status === "string" ? data.live_kite_status : null,
      );

      if (portfolioDayPnlChanged) {
        portfolioDayPnlRef.current = nextPortfolioDayPnl;
        setPortfolioDayPnl(nextPortfolioDayPnl);
      }

      if (monitorOpenPnlChanged) {
        monitorOpenPnlRef.current = nextMonitorOpenPnl;
        setMonitorOpenPnl(nextMonitorOpenPnl);
      }

      if (ticksChanged) {
        positionTicksRef.current = nextPositionTicks;
        setPositionTicks(nextPositionTicks);
      }

      if (holdingsChanged) {
        liveHoldingsRef.current = nextLiveHoldings;
        setLiveHoldings(nextLiveHoldings);
      }

      if (nextLiveHoldingsTotalValue !== null && totalValueChanged) {
        liveHoldingsTotalValueRef.current = nextLiveHoldingsTotalValue;
        setLiveHoldingsTotalValue(nextLiveHoldingsTotalValue);
      }

      if (nextLiveHoldingsTotalPnl !== null && totalPnlChanged) {
        liveHoldingsTotalPnlRef.current = nextLiveHoldingsTotalPnl;
        setLiveHoldingsTotalPnl(nextLiveHoldingsTotalPnl);
      }

      setLastSyncedAt(new Date().toISOString());
      setIsPolling(false);
    } catch {
      if (requestId !== requestRef.current) {
        return;
      }

      failureCountRef.current += 1;
      if (failureCountRef.current >= POLL_FAILURE_THRESHOLD) {
        setPollError("Live P&L sync failed — showing last known values.");
      }
      setIsPolling(false);
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
    lastSyncedAt,
    pollError,
    isPolling,
    refresh,
  };
}
