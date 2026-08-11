"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import TodayPortfolioHoldings from "@/components/dailyLoop/TodayPortfolioHoldings";
import TodayTrustStrip from "@/components/dailyLoop/TodayTrustStrip";
import AllocationVsPolicy from "@/components/portfolio/AllocationVsPolicy";
import AllocationHoldingsDrift from "@/components/portfolio/AllocationHoldingsDrift";
import { HoldingHealthList } from "@/components/portfolio/HoldingHealthChip";
import PositionsView from "@/components/portfolio/PositionsView";
import ResearchHandoffLink from "@/components/portfolio/ResearchHandoffLink";
import NewCapitalPanel from "@/components/capital/NewCapitalPanel";
import ThesisInvalidationBanner from "@/components/thesis/ThesisInvalidationBanner";
import PortfolioHealthSummary from "@/components/portfolio/PortfolioHealthSummary";
import { buildPortfolioHealthSummary } from "@/services/portfolio/buildPortfolioHealthSummary";
import ApexErrorBoundary from "@/components/ui/ApexErrorBoundary";
import { ApexCard, ApexShell, ApexTitle } from "@/components/ui/apex";
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
  userName,
}: Props) {
  const [overview, setOverview] = useState<PortfolioOverviewViewModel | null>(
    null,
  );
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [fundsLoading, setFundsLoading] = useState(false);
  const [fundsSynced, setFundsSynced] = useState(false);
  const [fundsSyncError, setFundsSyncError] = useState<string | null>(null);
  const [ledgerCash, setLedgerCash] = useState<number | undefined>();
  const [collateral, setCollateral] = useState<number | undefined>();
  const [availableCash, setAvailableCash] = useState<number | undefined>();
  const [totalCapital, setTotalCapital] = useState<number | undefined>();
  const [newCapital, setNewCapital] = useState<NewCapitalViewModel | null>(null);
  const [newCapitalLoading, setNewCapitalLoading] = useState(true);
  const [thesisWarnings, setThesisWarnings] = useState<ThesisInvalidationWarning[]>([]);
  const [portfolioProofHref, setPortfolioProofHref] = useState<string | null>(null);

  const loadFunds = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setFundsLoading(true);
    }
    setFundsSyncError(null);

    try {
      const response = await apiFetch("/api/funds", { cache: "no-store" });
      const data = await parseApiJson<FundsResponse>(response, "Funds");

      if (!response.ok || !data) {
        setFundsSyncError("Could not sync funds.");
        return;
      }

      setLedgerCash(data.ledger_cash);
      setCollateral(data.collateral);
      setAvailableCash(data.available_cash);
      setTotalCapital(data.total_capital ?? undefined);
      setFundsSynced(data.status === "OK" || data.status === "PARTIAL");
    } catch {
      setFundsSyncError("Could not sync funds.");
    } finally {
      setFundsLoading(false);
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

  const loadNewCapital = useCallback(async () => {
    setNewCapitalLoading(true);

    try {
      const response = await apiFetch("/api/capital/new", { cache: "no-store" });
      const data = await parseApiJson<NewCapitalResponse>(response, "New capital");

      if (response.ok && data?.workflow) {
        setNewCapital(data.workflow);
      }
    } finally {
      setNewCapitalLoading(false);
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
      loadNewCapital(),
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

  const pollEnabled = connectionStatus === "CONNECTED";
  usePortfolioPoll({
    enabled: pollEnabled,
    onRefresh: () => {
      void refreshAll({ silent: true });
    },
  });

  const {
    positionsPnl: livePositionsPnl,
    positionsBreakdown: livePositionsBreakdown,
    portfolioDayPnl: liveDayPnl,
    liveHoldings,
    liveHoldingsTotalValue,
    liveHoldingsTotalPnl,
    lastSyncedAt: liveLastSyncedAt,
    pollError: livePollError,
    isPolling: livePnlPolling,
  } = useDayPnlPoll({ enabled: pollEnabled });

  const portfolio = overview?.portfolio;
  const displayHoldings =
    liveHoldings.length > 0 ? liveHoldings : (portfolio?.holdings ?? []);
  const displayValue =
    liveHoldingsTotalValue ?? portfolio?.total_value ?? null;
  const displayTotalPnl =
    liveHoldingsTotalPnl ?? portfolio?.total_pnl ?? null;
  const resolvedOpenPnl =
    livePositionsPnl ?? portfolio?.positions_pnl ?? null;

  const healthSummary = useMemo(
    () => buildPortfolioHealthSummary(overview?.health ?? []),
    [overview?.health],
  );

  const bucketBySymbol = useMemo(() => {
    const map: Record<string, { bucket: "core" | "tactical" | "cash"; drift_pct: number }> =
      {};

    for (const row of overview?.allocation?.holdings ?? []) {
      map[row.tradingsymbol.toUpperCase()] = {
        bucket: row.bucket,
        drift_pct: row.drift_pct,
      };
    }

    return map;
  }, [overview?.allocation?.holdings]);

  return (
    <ApexShell>
      <header className="mb-6 space-y-4">
        <ApexSurfaceNav />
        <div className="space-y-2">
          <ApexTitle>Portfolio</ApexTitle>
          <p className="text-sm text-apex-muted">
            Live holdings, allocation policy, and health for {userName}.
          </p>
        </div>
      </header>

      <ApexCard hover={false} padding="none" className="overflow-hidden">
        <ApexErrorBoundary fallbackTitle="Portfolio data could not render.">
        <div className="p-6 space-y-4">
          <TodayTrustStrip
            connectionStatus={connectionStatus}
            marginAvailable={availableCash}
            ledgerCash={ledgerCash}
            collateral={collateral}
            portfolioValue={displayValue ?? undefined}
            totalCapital={totalCapital}
            openPnl={resolvedOpenPnl}
            portfolioDayPnl={liveDayPnl ?? portfolio?.day_pnl ?? null}
            positionsBreakdown={livePositionsBreakdown}
            lastSyncedAt={liveLastSyncedAt}
            portfolioStale={portfolio?.stale === true}
            pollError={livePollError}
            breakdownLoading={false}
            isPolling={livePnlPolling}
            fundsLoading={fundsLoading}
            fundsSynced={fundsSynced}
            fundsSyncError={fundsSyncError}
            proofHref={portfolioProofHref}
          />

          <ThesisInvalidationBanner warnings={thesisWarnings} />

          {overview?.health?.length ? (
            <PortfolioHealthSummary summary={healthSummary} />
          ) : null}

          {overviewLoading ? (
            <p className="text-sm text-apex-muted/70">Loading overview…</p>
          ) : connectionStatus === "TOKEN_EXPIRED" ? (
            <section className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-4">
              <p className="text-sm text-amber-100/90">
                Zerodha session expired. Reconnect to refresh holdings, allocation,
                and health data.
              </p>
            </section>
          ) : connectionStatus === "NOT_CONNECTED" ? (
            <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4">
              <p className="text-sm text-apex-text/90">
                Connect Zerodha to see allocation policy, health chips, and live
                positions.
              </p>
            </section>
          ) : null}

          {overview?.allocation ? (
            <>
              <AllocationVsPolicy allocation={overview.allocation} />
              <AllocationHoldingsDrift allocation={overview.allocation} />
            </>
          ) : null}

          {overview?.health?.length ? (
            <HoldingHealthList chips={overview.health} linkResearch />
          ) : null}

          <ResearchHandoffLink symbol={overview?.research_symbol ?? null} />

          <NewCapitalPanel workflow={newCapital} loading={newCapitalLoading} />

          <TodayPortfolioHoldings
            holdings={displayHoldings}
            totalValue={displayValue}
            totalPnl={displayTotalPnl}
            stale={portfolio?.stale === true}
            bucketBySymbol={bucketBySymbol}
            loading={
              overviewLoading &&
              displayHoldings.length === 0 &&
              connectionStatus === "CONNECTED"
            }
            showEmptyWhenSynced={
              !overviewLoading &&
              displayHoldings.length === 0 &&
              connectionStatus === "CONNECTED"
            }
          />

          <PositionsView
            positions={overview?.positions ?? []}
            loading={overviewLoading}
          />
        </div>
        </ApexErrorBoundary>
      </ApexCard>
    </ApexShell>
  );
}
