"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import ConnectZerodhaCard from "./ConnectZerodhaCard";
import DailyDecisionCard from "./DailyDecisionCard";
import DecisionHistoryPanel from "./DecisionHistoryPanel";
import DailyInsightBanner from "./DailyInsightBanner";
import FinancialProfileSetup from "./FinancialProfileSetup";
import LoginCTA from "./LoginCTA";
import PortfolioCard from "./PortfolioCard";
import PortfolioSummary, {
  PortfolioSummarySkeleton,
} from "./PortfolioSummary";
import { useAuth } from "@/components/AuthProvider";
import { authDebug } from "@/lib/auth/log";
import type { Portfolio } from "@/types/portfolio";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import type { FinancialProfile } from "@/lib/financialProfile";
import { isProfileComplete } from "@/lib/financialProfile";
import type { DailyDecisionOutput } from "@/types/decision";
import { decisionHeadline } from "@/types/decision";
import type { PortfolioApiResponse } from "@/types/portfolioApi";
import type { DailyInsight } from "@/types/dailyInsight";
import type { DecisionHistoryEntry } from "@/types/decisionHistory";
import { recordVisit, saveCachedPortfolio } from "@/lib/portfolioCache";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
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

type DecisionResponse = {
  decision: DailyDecisionOutput | null;
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

function LoadingState() {
  return (
    <main className="min-h-screen bg-slate-950 text-gray-200 flex items-center justify-center px-6">
      <div className="space-y-3 text-center">
        <div className="h-2 w-32 mx-auto rounded-full bg-white/10 animate-pulse" />
        <p className="text-sm text-gray-400 italic">
          Setting things up for you…
        </p>
      </div>
    </main>
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
    <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5">
      <p className="text-sm text-red-200/90">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 text-xs text-teal-400 hover:text-teal-300"
        >
          Try again
        </button>
      )}
    </div>
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
  const [dailyDecision, setDailyDecision] = useState<DailyDecisionOutput | null>(
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
      router.replace("/", { scroll: false });
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
        setBrokerMessage("Your portfolio is synced and ready.");
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

  const loadDailyDecision = useCallback(async () => {
    if (!configured || !user) return;

    try {
      const res = await apiFetch("/api/decision/today", { method: "GET" });
      const data = await parseApiJson<DecisionResponse>(res, "Daily decision");
      if (!data) return;
      setDailyDecision(data.decision);
      void loadDecisionHistory();
    } catch {
      // Decision is optional on first connect — don't block the flow.
    }
  }, [configured, user, loadDecisionHistory]);

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
      await loadDailyDecision();
      await loadDailyInsight();
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
    loadDailyDecision,
    loadDailyInsight,
    loadDecisionHistory,
  ]);

  const refreshPortfolio = useCallback(() => {
    if (!configured || !user || authLoading || isCompletingOAuth) return;

    setPortfolioError(null);
    setBrokerMessage(null);
    setCompletedFetchKey(null);

    void loadPortfolio().finally(() => {
      setCompletedFetchKey(user.id);
      void loadDailyDecision();
      void loadDailyInsight();
      void loadDecisionHistory();
    });
  }, [
    configured,
    user,
    authLoading,
    isCompletingOAuth,
    loadPortfolio,
    loadDailyDecision,
    loadDailyInsight,
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
        void loadDailyDecision();
        void loadDailyInsight();
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
    loadDailyDecision,
    loadDailyInsight,
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
      <main className="relative min-h-screen bg-slate-950 text-gray-200 px-6 py-10">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/20 pointer-events-none" />
        <div className="relative max-w-3xl mx-auto space-y-8">
          <div className="space-y-4">
            <div className="text-sm text-teal-400 tracking-wide">
              APEX · Your Investment Mentor
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold leading-tight">
                {greeting}
              </h1>
              <p className="text-gray-400 max-w-xl">{VALUE_STATEMENT}</p>
            </div>
          </div>
          <LoginCTA />
        </div>
      </main>
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

  return (
    <main className="relative min-h-screen bg-slate-950 text-gray-200 px-6 py-10">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/20 pointer-events-none" />

      <div className="relative max-w-3xl mx-auto space-y-8">
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="text-sm text-teal-400 tracking-wide">
              APEX · Your Investment Mentor
            </div>
            <div className="flex items-center gap-4">
              {!isOnboarding && isRefreshing && !isCompletingOAuth && (
                <div className="text-xs text-gray-500 italic">
                  Updating your portfolio…
                </div>
              )}
              {isCompletingOAuth && (
                <div className="text-xs text-teal-400/80 italic">
                  Connecting your portfolio…
                </div>
              )}
              <button
                type="button"
                onClick={() => void signOut()}
                className="text-xs text-gray-500 hover:text-gray-300"
              >
                Sign out
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <h1 className="text-3xl font-semibold leading-tight">
              {greeting}
            </h1>
            <p className="text-gray-400 max-w-xl">
              {isOnboarding
                ? VALUE_STATEMENT
                : dailyDecision
                  ? decisionHeadline(dailyDecision)
                  : "Setting things up for you…"}
            </p>
          </div>

          {showGuidance && (
            <>
              {portfolioLoading && !hasPortfolioData && (
                <PortfolioSummarySkeleton />
              )}
              {hasPortfolioData &&
                portfolioData &&
                portfolioData.total_value !== undefined && (
                  <PortfolioSummary
                    totalValue={portfolioData.total_value}
                    dayPnl={
                      portfolioData.day_pnl ?? dailyInsight?.day_pnl ?? null
                    }
                    riskScore={portfolioData.risk_score ?? 4}
                    riskLevel={portfolioData.risk_level ?? "Low"}
                    topSymbol={portfolioData.top_symbol}
                    topAllocationPct={portfolioData.top_allocation_pct}
                  />
                )}
            </>
          )}

          {!isOnboarding && !isCompletingOAuth && (
            <div className="text-sm text-gray-500 italic">
              Take your time — this is guidance, not a command.
            </div>
          )}
        </div>

        {showPortfolioError && (
          <ErrorBanner
            message={portfolioError ?? "Could not load portfolio. Please try again."}
            onRetry={refreshPortfolio}
          />
        )}

        {showBrokerError && (
          <ErrorBanner message={brokerMessage ?? "Broker connection failed."} />
        )}

        {showBrokerSuccess && (
          <div className="p-4 rounded-xl border border-teal-500/20 bg-teal-500/5">
            <p className="text-sm text-teal-200/90">{brokerMessage}</p>
          </div>
        )}

        {isCompletingOAuth && (
          <div className="p-6 rounded-2xl border border-teal-500/20 bg-teal-500/5 text-center">
            <p className="text-sm text-teal-200/90">
              Setting things up for you…
            </p>
          </div>
        )}

        {isOnboarding && !isCompletingOAuth && (
          <ConnectZerodhaCard />
        )}

        {connectionStatus === "TOKEN_EXPIRED" && !isCompletingOAuth && (
          <div className="space-y-3">
            <div className="p-4 rounded-xl border border-yellow-500/20 bg-yellow-500/5">
              <p className="text-sm text-yellow-200/90 mb-3">
                Your connection needs a quick refresh
              </p>
              <ConnectZerodhaCard
                title="Let's refresh your connection"
                description="A quick sign-in brings your portfolio back — same secure flow as before."
                buttonLabel="Refresh connection"
                subtext="Takes less than 10 seconds · No passwords stored"
              />
            </div>
          </div>
        )}

        {connectionStatus === "CONNECTED" && !isCompletingOAuth && (
          <div className="space-y-4">
            {dailyInsight && <DailyInsightBanner insight={dailyInsight} />}

            <div className="text-xs text-teal-400/80">
              Your portfolio is synced and ready.
            </div>

            {portfolioLoading && !hasPortfolioData && (
              <div className="p-6 rounded-2xl border border-white/10 bg-slate-900/50 space-y-3">
                <div className="h-2 w-24 rounded-full bg-white/10 animate-pulse" />
                <p className="text-sm text-gray-400 italic">
                  Loading your portfolio…
                </p>
              </div>
            )}

            {hasPortfolioData &&
              portfolioData &&
              portfolioData.total_value !== undefined &&
              portfolioData.total_pnl !== undefined && (
                <PortfolioCard
                  holdings={portfolioData.holdings}
                  totalValue={portfolioData.total_value}
                  totalPnl={portfolioData.total_pnl}
                  concentrated={portfolioData.concentrated}
                  topSymbol={portfolioData.top_symbol}
                  topAllocationPct={portfolioData.top_allocation_pct}
                />
              )}
          </div>
        )}

        {showGuidance && !showPortfolioError && (
          <>
            {!profileComplete && (
              <FinancialProfileSetup
                onComplete={(profile) => {
                  setFinancialProfile(profile);
                  void loadDailyDecision();
                  void loadDecisionHistory();
                }}
              />
            )}
            {dailyDecision ? (
              <DailyDecisionCard
                decision={dailyDecision}
                totalValue={portfolioData?.total_value ?? 0}
              />
            ) : (
              <div className="p-6 rounded-2xl border border-white/10 bg-slate-900/50 space-y-3">
                <div className="h-2 w-24 rounded-full bg-white/10 animate-pulse" />
                <p className="text-sm text-gray-400 italic">
                  Setting things up for you…
                </p>
              </div>
            )}
            <DecisionHistoryPanel history={decisionHistory} />
          </>
        )}

        <div className="pt-6 border-t border-white/10 text-sm text-gray-500">
          APEX supports your decisions — you own the final call. Not financial
          advice.
        </div>
      </div>
    </main>
  );
}
