"use client";

import { useCallback, useEffect, useState } from "react";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import TodayPortfolioHoldings from "@/components/dailyLoop/TodayPortfolioHoldings";
import TodayTrustStrip from "@/components/dailyLoop/TodayTrustStrip";
import AllocationVsPolicy from "@/components/portfolio/AllocationVsPolicy";
import { HoldingHealthList } from "@/components/portfolio/HoldingHealthChip";
import PositionsView from "@/components/portfolio/PositionsView";
import ResearchHandoffLink from "@/components/portfolio/ResearchHandoffLink";
import { ApexCard, ApexShell, ApexTitle } from "@/components/ui/apex";
import { useDayPnlPoll } from "@/lib/useDayPnlPoll";
import { usePortfolioPoll } from "@/lib/usePortfolioPoll";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import type { PortfolioOverviewViewModel } from "@/types/portfolioOverview";

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
  const [fundsLoading, setFundsLoading] = useState(true);
  const [fundsSynced, setFundsSynced] = useState(false);
  const [fundsSyncError, setFundsSyncError] = useState<string | null>(null);
  const [ledgerCash, setLedgerCash] = useState<number | undefined>();
  const [collateral, setCollateral] = useState<number | undefined>();
  const [availableCash, setAvailableCash] = useState<number | undefined>();
  const [totalCapital, setTotalCapital] = useState<number | undefined>();

  const loadFunds = useCallback(async () => {
    setFundsLoading(true);
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

  const loadOverview = useCallback(async () => {
    setOverviewLoading(true);

    try {
      const response = await apiFetch("/api/portfolio/overview", {
        cache: "no-store",
      });
      const data = await parseApiJson<OverviewResponse>(response, "Portfolio overview");

      if (response.ok && data?.overview) {
        setOverview(data.overview);
      }
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    await Promise.all([loadOverview(), loadFunds()]);
  }, [loadFunds, loadOverview]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  const pollEnabled = connectionStatus === "CONNECTED";
  usePortfolioPoll({ enabled: pollEnabled, onRefresh: refreshAll });

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
          />

          {overviewLoading ? (
            <p className="text-sm text-apex-muted/70">Loading overview…</p>
          ) : connectionStatus === "NOT_CONNECTED" ? (
            <section className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-4">
              <p className="text-sm text-apex-text/90">
                Connect Zerodha to see allocation policy, health chips, and live
                positions.
              </p>
            </section>
          ) : null}

          {overview?.allocation ? (
            <AllocationVsPolicy allocation={overview.allocation} />
          ) : null}

          {overview?.health?.length ? (
            <HoldingHealthList chips={overview.health} />
          ) : null}

          <ResearchHandoffLink symbol={overview?.research_symbol ?? null} />

          <TodayPortfolioHoldings
            holdings={displayHoldings}
            totalValue={displayValue}
            totalPnl={displayTotalPnl}
            stale={portfolio?.stale === true}
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
      </ApexCard>
    </ApexShell>
  );
}
