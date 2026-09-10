"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import PositionsView from "@/components/portfolio/PositionsView";
import NewCapitalPanel from "@/components/capital/NewCapitalPanel";
import ThesisInvalidationBanner from "@/components/thesis/ThesisInvalidationBanner";
import PortfolioBookHero from "@/components/portfolio/PortfolioBookHero";
import PortfolioHoldingCard from "@/components/portfolio/PortfolioHoldingCard";
import PortfolioPolicyPanel from "@/components/portfolio/PortfolioPolicyPanel";
import { buildPortfolioHealthSummary } from "@/services/portfolio/buildPortfolioHealthSummary";
import { buildSectorCapSummary } from "@/services/portfolio/sectorCapPolicy";
import type { HoldingHealthChip } from "@/services/portfolio/holdingHealth";
import { isYoungBook, orderYoungBookHoldings } from "@/lib/dailyLoop/firstBuyToday";
import { readTodayContract, type TodayContract } from "@/lib/dailyLoop/todayContract";
import TodayKiteContract from "@/components/dailyLoop/TodayKiteContract";
import ApexErrorBoundary from "@/components/ui/ApexErrorBoundary";
import { ApexShell, ApexTitle } from "@/components/ui/apex";
import { useDayPnlPoll } from "@/lib/useDayPnlPoll";
import { usePortfolioPoll } from "@/lib/usePortfolioPoll";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import type { PortfolioOverviewViewModel } from "@/types/portfolioOverview";
import type { NewCapitalViewModel } from "@/types/newCapital";
import type { ThesisInvalidationWarning } from "@/types/thesisInvalidation";

type FundsResponse = {
  ledger_cash: number;
  collateral: number;
  margin_available: number;
  portfolio_value?: number | null;
  total_capital?: number | null;
  available_cash: number;
  status?: "OK" | "PARTIAL" | "ERROR" | "NOT_CONNECTED" | "TOKEN_EXPIRED";
  message?: string;
};

type OverviewResponse = {
  status: string;
  overview: PortfolioOverviewViewModel;
};

type NewCapitalResponse = {
  status: string;
  workflow: NewCapitalViewModel;
};

type ThesisWatchResponse = {
  status: string;
  warnings: ThesisInvalidationWarning[];
};

type ReceiptsResponse = {
  status: string;
  receipts: Array<{ id: string }>;
};

type Props = {
  connectionStatus: ConnectionStatus;
  userName: string;
};

export default function PortfolioPageClient({
  connectionStatus,
}: Props) {
  const [overview, setOverview] = useState<PortfolioOverviewViewModel | null>(
    null,
  );
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [fundsSynced, setFundsSynced] = useState(false);
  const [fundsSyncError, setFundsSyncError] = useState<string | null>(null);
  const [availableCash, setAvailableCash] = useState<number | undefined>();
  const [newCapital, setNewCapital] = useState<NewCapitalViewModel | null>(null);
  const [newCapitalLoading, setNewCapitalLoading] = useState(true);
  const [thesisWarnings, setThesisWarnings] = useState<ThesisInvalidationWarning[]>([]);
  const [portfolioProofHref, setPortfolioProofHref] = useState<string | null>(null);
  const [todayContract, setTodayContract] = useState<TodayContract | null>(null);

  const loadFunds = useCallback(async (options?: { silent?: boolean }) => {
    setFundsSyncError(null);

    try {
      const response = await apiFetch("/api/funds", { cache: "no-store" });
      const data = await parseApiJson<FundsResponse>(response, "Funds");

      if (!response.ok || !data) {
        setFundsSyncError("Could not sync funds.");
        return;
      }

      setAvailableCash(data.available_cash);
      setFundsSynced(data.status === "OK" || data.status === "PARTIAL");
    } catch {
      setFundsSyncError("Could not sync funds.");
    }
  }, []);

  const loadOverview = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setOverviewLoading(true);
    }

    try {
      const response = await apiFetch("/api/portfolio/overview", {
        cache: "no-store",
      });
      const data = await parseApiJson<OverviewResponse>(response, "Portfolio overview");

      if (response.ok && data?.overview) {
        setOverview(data.overview);
      }
    } finally {
      if (!options?.silent) {
        setOverviewLoading(false);
      }
    }
  }, []);

  const loadNewCapital = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setNewCapitalLoading(true);
    }

    try {
      const response = await apiFetch("/api/capital/new", { cache: "no-store" });
      const data = await parseApiJson<NewCapitalResponse>(response, "New capital");

      if (response.ok && data?.workflow) {
        setNewCapital(data.workflow);
      }
    } finally {
      if (!options?.silent) {
        setNewCapitalLoading(false);
      }
    }
  }, []);

  const loadThesisWatch = useCallback(async () => {
    const response = await apiFetch("/api/thesis/watch", { cache: "no-store" });
    const data = await parseApiJson<ThesisWatchResponse>(response, "Thesis watch");

    if (response.ok && data?.warnings) {
      setThesisWarnings(data.warnings);
    }
  }, []);

  const loadPortfolioProof = useCallback(async () => {
    const response = await apiFetch("/api/receipts?days=7", { cache: "no-store" });
    const data = await parseApiJson<ReceiptsResponse>(response, "Receipts");

    if (response.ok && data?.receipts?.[0]?.id) {
      setPortfolioProofHref(
        `/app/review?tab=receipts&receipt=${encodeURIComponent(data.receipts[0].id)}`,
      );
    } else {
      setPortfolioProofHref(null);
    }
  }, []);

  const refreshAll = useCallback(async (options?: { silent?: boolean }) => {
    const silent = options?.silent ?? false;
    await Promise.all([
      loadOverview({ silent }),
      loadFunds({ silent: silent || fundsSynced }),
      loadNewCapital({ silent }),
      loadThesisWatch(),
      loadPortfolioProof(),
    ]);
  }, [
    fundsSynced,
    loadFunds,
    loadNewCapital,
    loadOverview,
    loadPortfolioProof,
    loadThesisWatch,
  ]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    setTodayContract(readTodayContract());
  }, []);

  const pollEnabled = connectionStatus === "CONNECTED";
  usePortfolioPoll({
    enabled: pollEnabled,
    onRefresh: () => {
      void refreshAll({ silent: true });
    },
  });

  const {
    portfolioDayPnl: liveDayPnl,
    liveHoldings,
    liveHoldingsTotalValue,
    lastSyncedAt: liveLastSyncedAt,
  } = useDayPnlPoll({ enabled: pollEnabled });

  const portfolio = overview?.portfolio;
  const displayHoldings =
    liveHoldings.length > 0 ? liveHoldings : (portfolio?.holdings ?? []);
  const displayValue =
    liveHoldingsTotalValue ?? portfolio?.total_value ?? null;

  const healthSummary = useMemo(
    () => buildPortfolioHealthSummary(overview?.health ?? []),
    [overview?.health],
  );

  const sectorCapSummary = useMemo(
    () =>
      buildSectorCapSummary({
        holdings: displayHoldings,
        totalValue: displayValue,
      }),
    [displayHoldings, displayValue],
  );

  const openHoldings = useMemo(
    () => orderYoungBookHoldings(displayHoldings.filter((row) => row.quantity > 0)),
    [displayHoldings],
  );
  const youngBook = isYoungBook({
    openHoldingsCount: openHoldings.length,
    portfolioValue: displayValue,
  });
  const healthBySymbol = useMemo(() => {
    const map: Record<string, HoldingHealthChip> = {};
    for (const chip of overview?.health ?? []) {
      map[chip.symbol.toUpperCase()] = chip;
    }
    return map;
  }, [overview?.health]);
  const bucketBySymbol = useMemo(() => {
    const map: Record<string, "core" | "tactical" | "cash"> = {};

    for (const row of overview?.allocation?.holdings ?? []) {
      map[row.tradingsymbol.toUpperCase()] = row.bucket;
    }

    return map;
  }, [overview?.allocation?.holdings]);
  const showNewCapital = Boolean(newCapital?.available);
  const openPositions = overview?.positions ?? [];

  return (
    <ApexShell>
      <header className="space-y-4">
        <ApexSurfaceNav />
        <ApexTitle className="sr-only">Portfolio</ApexTitle>
      </header>

      <ApexErrorBoundary fallbackTitle="Portfolio data could not render.">
        <div className="space-y-4">
          <PortfolioBookHero
            connectionStatus={connectionStatus}
            bookValue={displayValue}
            dayPnl={liveDayPnl ?? portfolio?.day_pnl ?? null}
            cashInr={availableCash}
            lastSyncedAt={liveLastSyncedAt}
            proofHref={youngBook ? null : portfolioProofHref}
          />

          {youngBook && todayContract ? (
            <TodayKiteContract contract={todayContract} />
          ) : null}

          {fundsSyncError ? (
            <p className="text-sm text-amber-100/85">{fundsSyncError}</p>
          ) : null}

          <ThesisInvalidationBanner warnings={thesisWarnings} />

          {connectionStatus === "TOKEN_EXPIRED" ? (
            <section className="rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-4">
              <p className="text-sm text-amber-100/90">
                Zerodha session expired. Reconnect to refresh the book.
              </p>
            </section>
          ) : connectionStatus === "NOT_CONNECTED" ? (
            <section className="rounded-2xl border border-white/[0.08] bg-white/[0.03] px-4 py-4">
              <p className="text-sm text-apex-text/90">
                Connect Zerodha to see live holdings.
              </p>
            </section>
          ) : null}

          {overviewLoading && openHoldings.length === 0 ? (
            <p className="text-sm text-apex-muted/70">Loading your book…</p>
          ) : null}

          {openHoldings.map((holding) => (
            <PortfolioHoldingCard
              key={holding.tradingsymbol}
              holding={holding}
              health={
                youngBook
                  ? undefined
                  : healthBySymbol[holding.tradingsymbol.toUpperCase()]
              }
              bucket={
                youngBook
                  ? undefined
                  : bucketBySymbol[holding.tradingsymbol.toUpperCase()]
              }
              quiet={youngBook}
            />
          ))}

          <PortfolioPolicyPanel
            allocation={overview?.allocation}
            health={overview?.health?.length ? healthSummary : null}
            sector={openHoldings.length > 0 ? sectorCapSummary : null}
            youngBook={youngBook}
            nextSymbol={todayContract?.watchSymbol}
          />

          {showNewCapital ? (
            <NewCapitalPanel workflow={newCapital} loading={newCapitalLoading} />
          ) : null}

          {openPositions.length > 0 ? (
            <PositionsView positions={openPositions} loading={overviewLoading} />
          ) : null}
        </div>
      </ApexErrorBoundary>
    </ApexShell>
  );
}
