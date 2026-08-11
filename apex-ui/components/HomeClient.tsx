"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ConnectZerodhaCard from "./ConnectZerodhaCard";
import DecisionHistoryPanel from "./DecisionHistoryPanel";
import HomeDecisionScreen from "./HomeDecisionScreen";
import FinancialProfileSetup from "./FinancialProfileSetup";
import IntentSelector from "./IntentSelector";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import LoginCTA from "./LoginCTA";
import PortfolioSummary, {
  PortfolioSummarySkeleton,
} from "./PortfolioSummary";
import { useAuth } from "@/components/AuthProvider";
import { ApexBody, ApexCard, ApexShell, ApexTitle } from "@/components/ui/apex";
import { authDebug } from "@/lib/auth/log";
import type { Portfolio } from "@/types/portfolio";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import type { FinancialProfile } from "@/lib/financialProfile";
import { isProfileComplete } from "@/lib/financialProfile";
import type { DailyInsight } from "@/types/dailyInsight";
import type {
  DecisionHistoryEntry,
  DecisionHistoryResponse,
  DisciplineHistorySummary,
} from "@/types/decisionHistory";
import {
  readStoredCapitalMode,
  writeStoredCapitalMode,
  type CapitalFundingMode,
} from "@/lib/dailyLoop/capitalMargin";
import { usePremiumTier } from "@/lib/usePremiumTier";
import PremiumFeatureGate from "@/components/dailyLoop/PremiumFeatureGate";
import FirstRunStrip from "@/components/dailyLoop/FirstRunStrip";
import { buildFirstRunProgress } from "@/lib/onboarding/firstRun";
import type { PortfolioApiResponse } from "@/types/portfolioApi";
import { recordVisit, saveCachedPortfolio } from "@/lib/portfolioCache";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import {
  filterRealPortfolioHoldings,
  isDemoPortfolioHoldings,
  resolvePortfolioDisplayValue,
} from "@/lib/portfolio/displayValue";
import { useIntentDecision } from "@/lib/useIntentDecision";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";
import { useGreeting } from "@/lib/useGreeting";
import { useZerodhaOAuth } from "@/lib/useZerodhaOAuth";

const VALUE_STATEMENT =
  "Calm, personal guidance for your portfolio — one clear action each day.";

type Props = {
  initialPortfolio: Portfolio;
  connectionStatus: ConnectionStatus;
  userName: string;
  initialFinancialProfile: FinancialProfile | null;
  zerodhaNotice?: string;
  zerodhaError?: string;
};

type InsightResponse = {
  insight: DailyInsight;
};

const EMPTY_DISCIPLINE_SUMMARY: DisciplineHistorySummary = {
  wins: 0,
  losses: 0,
  open: 0,
  waitDays: 0,
  executedDays: 0,
  followedDays: 0,
};

type ZerodhaSessionResponse = {
  status?: string;
  connected?: boolean;
};

type FundsResponse = {
  ledger_cash: number;
  collateral: number;
  margin_available: number;
  live_balance?: number;
  portfolio_value?: number;
  total_capital?: number;
  available_cash: number;
  status?: "OK" | "PARTIAL" | "ERROR" | "NOT_CONNECTED" | "TOKEN_EXPIRED";
  message?: string;
};

function finiteFunds(value: unknown, fallback = 0): number {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return Math.max(0, Math.round(parsed));
}

function LoadingState() {
  return (
    <ApexShell>
      <div className="flex min-h-[50vh] items-center justify-center">
        <ApexBody className="text-center italic">Setting things up for you…</ApexBody>
      </div>
    </ApexShell>
  );
}

function ErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <ApexCard hover={false} padding="compact" className="border-red-500/20">
      <ApexBody className="text-red-200/90">{message}</ApexBody>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 text-[13px] text-emerald-300 transition-colors hover:text-emerald-200"
        >
          Try again
        </button>
      ) : null}
    </ApexCard>
  );
}

export default function HomeClient({
  initialPortfolio,
  connectionStatus: initialConnectionStatus,
  userName,
  initialFinancialProfile,
  zerodhaNotice,
  zerodhaError,
}: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading, configured, signOut, supabase } = useAuth();
  const { features: premiumFeatures, activationEnabled, refresh: refreshPremiumTier } =
    usePremiumTier(Boolean(user));

  const handlePremiumActivated = useCallback(async () => {
    if (supabase) {
      await supabase.auth.refreshSession();
    }
    await refreshPremiumTier();
  }, [refreshPremiumTier, supabase]);

  const [financialProfile, setFinancialProfile] = useState<FinancialProfile | null>(
    initialFinancialProfile,
  );
  const profileComplete = isProfileComplete(financialProfile);

  const [connectionStatus, setConnectionStatus] = useState(
    initialConnectionStatus,
  );
  const [completedFetchKey, setCompletedFetchKey] = useState<string | null>(
    null,
  );
  const [dailyInsight, setDailyInsight] = useState<DailyInsight | null>(null);
  const [decisionHistory, setDecisionHistory] = useState<DecisionHistoryEntry[]>(
    [],
  );
  const [disciplineSummary, setDisciplineSummary] =
    useState<DisciplineHistorySummary>(EMPTY_DISCIPLINE_SUMMARY);
  const [disciplineDays, setDisciplineDays] = useState<string[]>([]);
  const [portfolioData, setPortfolioData] = useState<PortfolioApiResponse | null>(
    null,
  );
  const [portfolioError, setPortfolioError] = useState<string | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(
    () => initialPortfolio.holdings.length === 0,
  );
  const [availableCash, setAvailableCash] = useState<number | null>(null);
  const [ledgerCash, setLedgerCash] = useState<number | null>(null);
  const [collateral, setCollateral] = useState<number>(0);
  const [brokerPortfolioValue, setBrokerPortfolioValue] = useState<number | null>(
    null,
  );
  const [totalCapital, setTotalCapital] = useState<number | null>(null);
  const [capitalMode, setCapitalMode] = useState<CapitalFundingMode>("CASH");
  const [fundsLoading, setFundsLoading] = useState(false);
  const [fundsSynced, setFundsSynced] = useState(false);
  const [fundsSyncError, setFundsSyncError] = useState<string | null>(null);
  const fundsRequestRef = useRef(0);
  const [brokerMessage, setBrokerMessage] = useState<string | null>(
    zerodhaNotice === "connected"
      ? "Zerodha connected — syncing your portfolio now."
      : zerodhaError ?? null,
  );
  const greeting = useGreeting(userName);
  const { isCompletingOAuth } = useZerodhaOAuth();

  useEffect(() => {
    const notice = searchParams.get("zerodha");
    const error = searchParams.get("zerodha_error");

    if (notice === "connected") {
      setConnectionStatus("CONNECTED");
      setBrokerMessage("Zerodha connected — syncing your portfolio now.");
      setPortfolioError(null);
    } else if (error) {
      setBrokerMessage(decodeURIComponent(error));
    }

    if (notice || error) {
      router.replace("/app", { scroll: false });
    }
  }, [router, searchParams]);

  useEffect(() => {
    const stored = readStoredCapitalMode();

    if (!premiumFeatures.marginMode && stored === "MARGIN") {
      writeStoredCapitalMode("CASH");
      setCapitalMode("CASH");
      return;
    }

    setCapitalMode(stored);
  }, [premiumFeatures.marginMode]);

  useEffect(() => {
    if (!supabase) return;

    supabase.auth.getSession().then(({ data }) => {
      authDebug("SESSION", {
        hasSession: Boolean(data.session),
        userId: data.session?.user?.id ?? null,
      });
    });
  }, [supabase]);

  useEffect(() => {
    if (!configured || !user || authLoading || isCompletingOAuth) return;

    apiFetch("/api/zerodha/session", { method: "GET" })
      .then((res) => parseApiJson<ZerodhaSessionResponse>(res, "Zerodha session"))
      .then((data) => {
        if (!data?.connected) return;
        setConnectionStatus("CONNECTED");
      })
      .catch(() => {
        // Portfolio fetch remains the fallback source of truth.
      });
  }, [configured, user, authLoading, isCompletingOAuth]);

  const updatePortfolio = useCallback((next: Portfolio) => {
    saveCachedPortfolio(next);
  }, []);

  const applyPortfolioResponse = useCallback(
    (data: PortfolioApiResponse) => {
      const incomingHoldings = filterRealPortfolioHoldings(data.holdings);
      const normalized: PortfolioApiResponse =
        incomingHoldings.length === data.holdings.length
          ? data
          : { ...data, holdings: incomingHoldings };

      setPortfolioData((previous) => {
        if (
          normalized.holdings.length === 0 &&
          previous &&
          previous.holdings.length > 0
        ) {
          const previousHoldings = filterRealPortfolioHoldings(previous.holdings);
          if (previousHoldings.length === 0) {
            return normalized;
          }

          return {
            ...normalized,
            holdings: previousHoldings,
            total_value: resolvePortfolioDisplayValue(
              normalized.total_value,
              previousHoldings,
            ),
            total_pnl: previous.total_pnl,
            top_symbol: previous.top_symbol,
            top_allocation_pct: previous.top_allocation_pct,
            stale: true,
          };
        }

        return normalized;
      });

      if (incomingHoldings.length > 0) {
        setPortfolioError(null);
        updatePortfolio({
          holdings: incomingHoldings.map((h) => ({
            symbol: h.tradingsymbol,
            quantity: h.quantity,
            avgPrice: h.average_price,
            currentPrice: h.last_price,
          })),
        });
      }
    },
    [updatePortfolio],
  );

  const handlePortfolioResult = useCallback(
    (data: PortfolioApiResponse) => {
      applyPortfolioResponse(data);

      if (data.status === "OK" && data.holdings.length > 0) {
        setConnectionStatus("CONNECTED");
        setBrokerMessage(null);
        setPortfolioError(null);
      } else if (data.status === "TOKEN_EXPIRED") {
        setConnectionStatus("TOKEN_EXPIRED");
        if (data.holdings.length > 0) {
          setPortfolioError(null);
        }
      } else if (data.status === "NOT_CONNECTED") {
        setConnectionStatus("NOT_CONNECTED");
      }
    },
    [applyPortfolioResponse],
  );

  const loadPortfolio = useCallback(
    async (options?: { isCancelled?: () => boolean; silent?: boolean }) => {
      if (!options?.silent) {
        setPortfolioLoading(true);
      }

      try {
        const res = await apiFetch("/api/portfolio", { method: "GET" });
        const data = await parseApiJson<PortfolioApiResponse>(res, "Portfolio");

        if (options?.isCancelled?.()) return;

        if (!data) {
          throw new Error("Could not load portfolio");
        }
        if (!res.ok && data.status !== "TOKEN_EXPIRED") {
          throw new Error(data.message ?? "Could not load portfolio");
        }

        handlePortfolioResult(data);
      } catch (err) {
        if (options?.isCancelled?.()) return;
        console.error("Portfolio load failed:", err);
        setPortfolioError(
          err instanceof Error ? err.message : "Could not load portfolio",
        );
      } finally {
        if (!options?.isCancelled?.() && !options?.silent) {
          setPortfolioLoading(false);
        }
      }
    },
    [handlePortfolioResult],
  );

  const loadDecisionHistory = useCallback(async () => {
    if (!configured || !user) return;

    try {
      const res = await apiFetch("/api/decision/history?days=7", {
        method: "GET",
      });
      const data = await parseApiJson<DecisionHistoryResponse>(
        res,
        "Decision history",
      );
      if (!res.ok || !data) {
        return;
      }

      setDecisionHistory(data.history ?? []);
      setDisciplineSummary(data.summary ?? EMPTY_DISCIPLINE_SUMMARY);
      setDisciplineDays(data.days ?? []);
    } catch {
      // History is optional on first visit.
    }
  }, [configured, user]);

  const loadFunds = useCallback(async () => {
    if (!configured || !user) return;

    const requestId = ++fundsRequestRef.current;
    setFundsLoading(true);

    const applyFunds = (patch: {
      availableCash: number;
      ledgerCash: number;
      collateral: number;
      brokerPortfolioValue: number | null;
      totalCapital: number | null;
    }) => {
      if (requestId !== fundsRequestRef.current) {
        return;
      }

      setAvailableCash(patch.availableCash);
      setLedgerCash(patch.ledgerCash);
      setCollateral(patch.collateral);
      setBrokerPortfolioValue(patch.brokerPortfolioValue);
      setTotalCapital(patch.totalCapital);
      setFundsSynced(true);
      setFundsSyncError(null);
    };

    try {
      const res = await apiFetch("/api/funds", { method: "GET" });
      const data = await parseApiJson<FundsResponse>(res, "Funds");

      if (requestId !== fundsRequestRef.current) {
        return;
      }

      if (!data) {
        setFundsSynced(false);
        setFundsSyncError("Could not load Zerodha funds. Refresh or reconnect.");
        return;
      }

      if (data.status === "NOT_CONNECTED") {
        setFundsSynced(false);
        setFundsSyncError("Connect Zerodha to sync available balance.");
        return;
      }

      if (data.status === "TOKEN_EXPIRED") {
        setConnectionStatus("TOKEN_EXPIRED");
        setFundsSynced(false);
        setFundsSyncError(
          data.message ?? "Zerodha session expired — reconnect to refresh funds.",
        );
        return;
      }

      const marginAvailable = finiteFunds(
        data.margin_available ?? data.available_cash,
      );
      const nextLedgerCash = finiteFunds(data.ledger_cash);
      const nextCollateral = finiteFunds(data.collateral);
      const nextPortfolioValue = Number.isFinite(data.portfolio_value)
        ? finiteFunds(data.portfolio_value)
        : null;
      const nextTotalCapital = Number.isFinite(data.total_capital)
        ? finiteFunds(data.total_capital)
        : nextPortfolioValue !== null
          ? nextPortfolioValue + nextLedgerCash
          : null;

      if (data.status === "ERROR" || data.status === "PARTIAL") {
        const rateLimited = /too many requests/i.test(data.message ?? "");
        setAvailableCash(null);
        setLedgerCash(null);
        setCollateral(0);
        setBrokerPortfolioValue(nextPortfolioValue);
        setTotalCapital(nextTotalCapital);
        setFundsSynced((previous) => (rateLimited ? previous : false));
        setFundsSyncError(
          rateLimited
            ? null
            : (data.message ??
                "Zerodha funds could not be loaded. Try reconnecting."),
        );
        return;
      }

      applyFunds({
        availableCash: marginAvailable,
        ledgerCash: nextLedgerCash,
        collateral: nextCollateral,
        brokerPortfolioValue: nextPortfolioValue,
        totalCapital: nextTotalCapital,
      });
    } catch {
      if (requestId !== fundsRequestRef.current) {
        return;
      }
      setFundsSynced(false);
      setFundsSyncError("Could not load Zerodha funds. Refresh or reconnect.");
    } finally {
      if (requestId === fundsRequestRef.current) {
        setFundsLoading(false);
      }
    }
  }, [configured, user]);

  useEffect(() => {
    if (
      connectionStatus !== "CONNECTED" ||
      !configured ||
      !user ||
      authLoading ||
      isCompletingOAuth
    ) {
      return;
    }

    void loadFunds();
  }, [
    connectionStatus,
    configured,
    user,
    authLoading,
    isCompletingOAuth,
    loadFunds,
  ]);

  const intentDecisionEnabled =
    configured &&
    Boolean(user) &&
    !authLoading &&
    !isCompletingOAuth &&
    connectionStatus !== "NOT_CONNECTED";

  const recommendationPortfolio = useMemo(
    () => ({
      top_symbol: portfolioData?.top_symbol,
      top_allocation_pct: portfolioData?.top_allocation_pct,
      holdings: portfolioData?.holdings?.map((holding) => ({
        symbol: holding.tradingsymbol,
        allocation_pct: holding.allocation_pct,
      })),
    }),
    [portfolioData],
  );

  const {
    intent: userIntent,
    setIntent: setUserIntent,
    decision: dailyDecision,
    entryTiming,
    decisionUpdatedAt,
    isRefreshing: decisionRefreshing,
    refreshDecision,
  } = useIntentDecision({
    enabled: intentDecisionEnabled,
    portfolioContext: {
      stock: portfolioData?.top_symbol,
      allocation: portfolioData?.top_allocation_pct,
      availableCash: availableCash ?? undefined,
      riskLevel: portfolioData?.risk_level,
      holdings: recommendationPortfolio.holdings,
    },
    onFetched: () => {
      void loadDecisionHistory();
    },
  });

  const loadDailyInsight = useCallback(async () => {
    if (!configured || !user) return;

    try {
      const res = await apiFetch("/api/insight/today", { method: "GET" });
      const data = await parseApiJson<InsightResponse>(res, "Daily insight");
      if (!data?.insight) return;
      setDailyInsight(data.insight);
    } catch {
      // Insight is optional — don't block the dashboard.
    }
  }, [configured, user]);

  const refreshDashboard = useCallback(async () => {
    if (!configured || !user || authLoading || isCompletingOAuth) return;

    try {
      console.log("Tab active → refreshing data");
      await loadPortfolio({ silent: true });
      refreshDecision();
      await loadDailyInsight();
      await loadFunds();
      await loadDecisionHistory();

      const res = await apiFetch("/api/zerodha/session", { method: "GET" });
      const data = await parseApiJson<ZerodhaSessionResponse>(res, "Zerodha session");
      if (data?.connected) {
        setConnectionStatus("CONNECTED");
      }
    } catch (err) {
      console.error("Refresh failed", err);
    }
  }, [
    configured,
    user,
    authLoading,
    isCompletingOAuth,
    loadPortfolio,
    refreshDecision,
    loadDailyInsight,
    loadFunds,
    loadDecisionHistory,
  ]);

  const refreshPortfolio = useCallback(() => {
    if (!configured || !user || authLoading || isCompletingOAuth) return;

    setPortfolioError(null);
    setBrokerMessage(null);
    setCompletedFetchKey(null);

    void loadPortfolio().finally(() => {
      setCompletedFetchKey(user.id);
      void refreshDecision();
      void loadDailyInsight();
      void loadFunds();
      void loadDecisionHistory();
    });
  }, [
    configured,
    user,
    authLoading,
    isCompletingOAuth,
    loadPortfolio,
    refreshDecision,
    loadDailyInsight,
    loadFunds,
    loadDecisionHistory,
  ]);

  const shouldFetchPortfolio =
    configured && Boolean(user) && !authLoading && !isCompletingOAuth;
  const portfolioFetchKey = user?.id ?? "anonymous";
  const isRefreshing =
    shouldFetchPortfolio && completedFetchKey !== portfolioFetchKey;

  useEffect(() => {
    if (!shouldFetchPortfolio) {
      return;
    }

    let cancelled = false;

    recordVisit();

    void loadPortfolio({ isCancelled: () => cancelled }).finally(() => {
      if (!cancelled) {
        setCompletedFetchKey(portfolioFetchKey);
        void loadDailyInsight();
        void loadFunds();
        void loadDecisionHistory();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [
    shouldFetchPortfolio,
    portfolioFetchKey,
    loadPortfolio,
    refreshDecision,
    loadDailyInsight,
    loadFunds,
    loadDecisionHistory,
  ]);

  useEffect(() => {
    if (initialPortfolio.holdings.length === 0) return;
    if (isDemoPortfolioHoldings(initialPortfolio.holdings)) return;

    setPortfolioData((current) => {
      if (current && current.holdings.length > 0) return current;

      const formatted = initialPortfolio.holdings.map((h) => {
        const value = h.quantity * h.currentPrice;
        const pnl = (h.currentPrice - h.avgPrice) * h.quantity;
        return {
          tradingsymbol: h.symbol,
          quantity: h.quantity,
          average_price: h.avgPrice,
          last_price: h.currentPrice,
          pnl,
          value,
          allocation_pct: 0,
        };
      });

      const total_value = formatted.reduce((sum, h) => sum + h.value, 0);
      const holdings = formatted
        .map((h) => ({
          ...h,
          allocation_pct: total_value > 0 ? (h.value / total_value) * 100 : 0,
        }))
        .sort((a, b) => b.value - a.value);

      const top = holdings[0];
      const top_allocation_pct = top?.allocation_pct ?? 0;
      const { risk_score, risk_level } =
        portfolioRiskFromAllocation(top_allocation_pct);

      return {
        status: "OK",
        holdings,
        total_value,
        total_pnl: holdings.reduce((sum, h) => sum + h.pnl, 0),
        concentrated: top_allocation_pct > 50,
        top_symbol: top?.tradingsymbol,
        top_allocation_pct,
        risk_score,
        risk_level,
      };
    });

    setPortfolioError(null);
    setPortfolioLoading(false);
  }, [initialPortfolio]);

  useEffect(() => {
    if (!configured || !user || authLoading) return;

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void refreshDashboard();
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [configured, user, authLoading, refreshDashboard]);

  const refreshAfterExecution = useCallback(() => {
    void loadPortfolio({ silent: true });
    refreshDecision();
    void loadFunds();
    void loadDecisionHistory();
  }, [loadPortfolio, refreshDecision, loadFunds, loadDecisionHistory]);

  const handleCapitalModeChange = useCallback(
    (mode: CapitalFundingMode) => {
      if (!premiumFeatures.marginMode && mode === "MARGIN") {
        return;
      }

      setCapitalMode(mode);
      refreshDecision();
    },
    [premiumFeatures.marginMode, refreshDecision],
  );

  const brokerSessionActive =
    connectionStatus === "CONNECTED" || connectionStatus === "TOKEN_EXPIRED";

  const showHomeDecision = Boolean(dailyDecision) && brokerSessionActive;

  const visiblePortfolioHoldings = useMemo(
    () => filterRealPortfolioHoldings(portfolioData?.holdings ?? []),
    [portfolioData?.holdings],
  );

  const resolvedPortfolioValue = useMemo(
    () =>
      resolvePortfolioDisplayValue(
        brokerPortfolioValue ?? portfolioData?.total_value,
        visiblePortfolioHoldings,
      ),
    [brokerPortfolioValue, portfolioData?.total_value, visiblePortfolioHoldings],
  );

  const firstRunProgress = useMemo(
    () =>
      buildFirstRunProgress({
        connectionStatus,
        profileComplete,
        todayReady: showHomeDecision,
        decisionLoading:
          connectionStatus === "CONNECTED" &&
          profileComplete &&
          !dailyDecision &&
          (decisionRefreshing || isRefreshing),
      }),
    [
      connectionStatus,
      dailyDecision,
      decisionRefreshing,
      isRefreshing,
      profileComplete,
      showHomeDecision,
    ],
  );

  const showFirstRunStrip =
    Boolean(user) &&
    !firstRunProgress.complete &&
    !isCompletingOAuth;

  if (authLoading) {
    return <LoadingState />;
  }

  if (!user) {
    return (
      <ApexShell>
        <header className="space-y-2">
          <ApexBody>APEX · Your Investment Mentor</ApexBody>
          <ApexTitle>{greeting}</ApexTitle>
          <ApexBody>{VALUE_STATEMENT}</ApexBody>
        </header>
        <LoginCTA />
      </ApexShell>
    );
  }

  const isOnboarding = connectionStatus === "NOT_CONNECTED";
  const showGuidance = !isOnboarding && !isCompletingOAuth;
  const hasPortfolioData = visiblePortfolioHoldings.length > 0;
  const showPortfolioError = Boolean(portfolioError) && !hasPortfolioData;
  const showBrokerError =
    Boolean(brokerMessage) &&
    !brokerMessage?.includes("synced") &&
    !brokerMessage?.includes("syncing");
  const showBrokerSuccess =
    Boolean(brokerMessage) &&
    (brokerMessage?.includes("synced") ||
      brokerMessage?.includes("syncing") ||
      brokerMessage?.includes("connected"));

  return (
    <ApexShell>
      <header className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <ApexBody>APEX</ApexBody>
          <div className="flex items-center gap-3">
            {!isOnboarding && isRefreshing && !isCompletingOAuth ? (
              <ApexBody className="italic">Updating…</ApexBody>
            ) : null}
            {isCompletingOAuth ? (
              <ApexBody className="italic text-blue-200/80">Connecting…</ApexBody>
            ) : null}
            <button
              type="button"
              onClick={() => void signOut()}
              className="text-[13px] text-apex-muted transition-colors hover:text-apex-text"
            >
              Sign out
            </button>
          </div>
        </div>

        {showGuidance ? <ApexSurfaceNav /> : null}

        {showFirstRunStrip ? (
          <FirstRunStrip progress={firstRunProgress} userName={userName} />
        ) : isOnboarding ? (
          <ApexBody>{VALUE_STATEMENT}</ApexBody>
        ) : null}

        {showGuidance ? (
          <>
            <IntentSelector intent={userIntent} onIntentChange={setUserIntent} />
            {portfolioLoading && !hasPortfolioData ? (
              <PortfolioSummarySkeleton />
            ) : null}
            {hasPortfolioData &&
            portfolioData &&
            portfolioData.total_value !== undefined &&
            !showHomeDecision ? (
              <PortfolioSummary
                totalValue={portfolioData.total_value}
                dayPnl={portfolioData.day_pnl ?? dailyInsight?.day_pnl ?? null}
                riskScore={portfolioData.risk_score ?? 4}
                riskLevel={portfolioData.risk_level ?? "Low"}
              />
            ) : null}
          </>
        ) : null}
      </header>

      {showPortfolioError ? (
        <ErrorBanner
          message={portfolioError ?? "Could not load portfolio. Please try again."}
          onRetry={refreshPortfolio}
        />
      ) : null}

      {showBrokerError ? (
        <ErrorBanner message={brokerMessage ?? "Broker connection failed."} />
      ) : null}

      {showBrokerSuccess ? (
        <ApexCard hover={false} padding="compact" className="border-emerald-500/20">
          <ApexBody className="text-emerald-200/90">{brokerMessage}</ApexBody>
        </ApexCard>
      ) : null}

      {isCompletingOAuth ? (
        <ApexCard hover={false} padding="compact">
          <ApexBody className="text-center italic">
            Setting things up for you…
          </ApexBody>
        </ApexCard>
      ) : null}

      {isOnboarding && !isCompletingOAuth ? <ConnectZerodhaCard /> : null}

      {connectionStatus === "TOKEN_EXPIRED" && !isCompletingOAuth ? (
        <ConnectZerodhaCard
          title="Refresh your connection"
          description="A quick sign-in brings your portfolio back."
          buttonLabel="Refresh connection"
          subtext="Takes less than 10 seconds"
        />
      ) : null}

      {showGuidance && !showPortfolioError ? (
        <>
          {!profileComplete ? (
            <FinancialProfileSetup
              stepHint={
                showFirstRunStrip ? "Step 2 of 3 · Set capital context" : undefined
              }
              onComplete={(profile) => {
                setFinancialProfile(profile);
                refreshDecision();
                void loadDecisionHistory();
              }}
            />
          ) : null}

          {showHomeDecision && dailyDecision ? (
            <HomeDecisionScreen
              decision={dailyDecision}
              entryTiming={entryTiming}
              intent={userIntent}
              availableCash={availableCash ?? (fundsSynced ? 0 : undefined)}
              ledgerCash={ledgerCash ?? (fundsSynced ? 0 : undefined)}
              topSymbol={portfolioData?.top_symbol}
              topAllocationPct={portfolioData?.top_allocation_pct}
              portfolioValue={resolvedPortfolioValue}
              totalCapital={totalCapital ?? undefined}
              collateral={collateral}
              capitalMode={capitalMode}
              onCapitalModeChange={handleCapitalModeChange}
              dayPnl={portfolioData?.day_pnl ?? dailyInsight?.day_pnl ?? null}
              openPnlFromPortfolio={portfolioData?.positions_pnl ?? null}
              holdings={visiblePortfolioHoldings.map((holding) => ({
                symbol: holding.tradingsymbol,
                weight: holding.allocation_pct,
              }))}
              portfolioHoldings={visiblePortfolioHoldings}
              portfolioTotalPnl={portfolioData?.total_pnl ?? null}
              portfolioLoading={portfolioLoading}
              connectionStatus={connectionStatus}
              decisionUpdatedAt={decisionUpdatedAt}
              fundsLoading={fundsLoading}
              fundsSynced={fundsSynced}
              fundsSyncError={fundsSyncError}
              isRefreshing={decisionRefreshing}
              onCapitalRefresh={refreshAfterExecution}
              onDisciplineCommitted={() => {
                void loadDecisionHistory();
              }}
              disciplineHistory={decisionHistory}
              disciplineSummary={disciplineSummary}
              disciplineDays={
                disciplineDays.length > 0
                  ? disciplineDays
                  : decisionHistory.map((entry) => entry.date)
              }
              premiumFeatures={premiumFeatures}
              premiumActivationEnabled={activationEnabled}
              onPremiumActivated={() => {
                void handlePremiumActivated();
              }}
            />
          ) : null}

          {showHomeDecision ? (
            <DecisionHistoryPanel
              history={decisionHistory}
              summary={disciplineSummary}
              days={
                disciplineDays.length > 0
                  ? disciplineDays
                  : decisionHistory.map((entry) => entry.date)
              }
              showDetailRows={premiumFeatures.decisionHistory}
              activationEnabled={activationEnabled}
              onPremiumActivated={() => {
                void handlePremiumActivated();
              }}
            />
          ) : null}
        </>
      ) : null}

      <footer className="border-t border-apex-border pt-6">
        <ApexBody>
          APEX supports your decisions — you own the final call. Not financial
          advice.
        </ApexBody>
      </footer>
    </ApexShell>
  );
}
