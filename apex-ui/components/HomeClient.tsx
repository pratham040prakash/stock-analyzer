"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ConnectZerodhaCard from "./ConnectZerodhaCard";
import DailyDecisionCard from "./DailyDecisionCard";
import DecisionHistoryPanel from "./DecisionHistoryPanel";
import HomeDecisionScreen from "./HomeDecisionScreen";
import FinancialProfileSetup from "./FinancialProfileSetup";
import IntentSelector from "./IntentSelector";
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
import type { DailyDecisionOutput } from "@/types/decision";
import { isSellAction } from "@/types/decision";
import type { DailyInsight } from "@/types/dailyInsight";
import type { DecisionHistoryEntry } from "@/types/decisionHistory";
import type { PortfolioApiResponse } from "@/types/portfolioApi";
import { recordVisit, saveCachedPortfolio } from "@/lib/portfolioCache";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
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

type DecisionHistoryResponse = {
  history: DecisionHistoryEntry[];
};

type ZerodhaSessionResponse = {
  status?: string;
  connected?: boolean;
};

type FundsResponse = {
  available_cash: number;
  status?: string;
};

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
  const [portfolioData, setPortfolioData] = useState<PortfolioApiResponse | null>(
    null,
  );
  const [portfolioError, setPortfolioError] = useState<string | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(
    () => initialPortfolio.holdings.length === 0,
  );
  const [availableCash, setAvailableCash] = useState<number | null>(null);
  const [fundsLoading, setFundsLoading] = useState(false);
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
      setPortfolioData(data);

      if (data.holdings.length > 0) {
        setPortfolioError(null);
        updatePortfolio({
          holdings: data.holdings.map((h) => ({
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
      const res = await apiFetch("/api/decision/history?days=3", {
        method: "GET",
      });
      const data = await parseApiJson<DecisionHistoryResponse>(
        res,
        "Decision history",
      );
      if (!data?.history) return;
      setDecisionHistory(data.history);
    } catch {
      // History is optional on first visit.
    }
  }, [configured, user]);

  const loadFunds = useCallback(async () => {
    if (!configured || !user) return;

    setFundsLoading(true);
    try {
      const res = await apiFetch("/api/funds", { method: "GET" });
      const data = await parseApiJson<FundsResponse>(res, "Funds");
      if (!data) return;
      setAvailableCash(Math.max(0, Math.round(data.available_cash ?? 0)));
    } catch {
      setAvailableCash(null);
    } finally {
      setFundsLoading(false);
    }
  }, [configured, user]);

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
  const hasPortfolioData = Boolean(
    portfolioData && portfolioData.holdings.length > 0,
  );
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

  const needsActionCard =
    Boolean(dailyDecision) &&
    userIntent !== "explore" &&
    (isSellAction(dailyDecision.action) || dailyDecision.action === "sell");

  const showHomeDecision =
    Boolean(dailyDecision) &&
    connectionStatus === "CONNECTED" &&
    !needsActionCard;

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

        {isOnboarding ? (
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
            />
          ) : null}

          {needsActionCard && dailyDecision ? (
            <DailyDecisionCard
              decision={dailyDecision}
              totalValue={portfolioData?.total_value ?? 0}
              isRefreshing={decisionRefreshing}
              intent={userIntent}
              availableCash={availableCash ?? undefined}
              riskLevel={portfolioData?.risk_level}
              portfolioContext={recommendationPortfolio}
              onIntentChange={setUserIntent}
              updatedAt={decisionUpdatedAt}
            />
          ) : null}

          {!showHomeDecision ? (
            <DecisionHistoryPanel history={decisionHistory} />
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
