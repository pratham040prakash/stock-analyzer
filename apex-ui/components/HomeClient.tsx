"use client";

import { useCallback, useEffect, useState } from "react";
import ConnectZerodhaCard from "./ConnectZerodhaCard";
import DailyDecisionCard from "./DailyDecisionCard";
import FinancialProfileSetup from "./FinancialProfileSetup";
import LoginCTA from "./LoginCTA";
import { useAuth } from "@/components/AuthProvider";
import { authDebug } from "@/lib/auth/log";
import type { Portfolio } from "@/types/portfolio";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import type { FinancialProfile } from "@/lib/financialProfile";
import { isProfileComplete } from "@/lib/financialProfile";
import type { DailyDecisionOutput } from "@/types/decision";
import { recordVisit, saveCachedPortfolio } from "@/lib/portfolioCache";
import { useGreeting } from "@/lib/useGreeting";
import { useZerodhaOAuth } from "@/lib/useZerodhaOAuth";

const VALUE_STATEMENT =
  "Calm, personal guidance for your portfolio — one clear action each day.";

type Props = {
  initialPortfolio: Portfolio;
  connectionStatus: ConnectionStatus;
  userName: string;
  initialFinancialProfile: FinancialProfile | null;
};

type HoldingsResponse = {
  status: ConnectionStatus | "OK" | "ERROR";
  portfolio?: Portfolio;
};

type DecisionResponse = {
  decision: DailyDecisionOutput | null;
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

function ErrorBanner({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/5">
      <p className="text-sm text-red-200/90">
        Something went wrong. Please try again.
      </p>
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
  connectionStatus: initialConnectionStatus,
  userName,
  initialFinancialProfile,
}: Props) {
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
  const [loadError, setLoadError] = useState(false);
  const greeting = useGreeting(userName);
  const { isCompletingOAuth, oauthError } = useZerodhaOAuth();

  useEffect(() => {
    if (!supabase) return;

    supabase.auth.getSession().then(({ data }) => {
      authDebug("SESSION", {
        hasSession: Boolean(data.session),
        userId: data.session?.user?.id ?? null,
      });
    });
  }, [supabase]);

  const updatePortfolio = useCallback((next: Portfolio) => {
    saveCachedPortfolio(next);
  }, []);

  const loadDailyDecision = useCallback(async () => {
    if (!configured || !user) return;

    try {
      const res = await fetch("/api/decision/today");
      if (!res.ok) {
        setLoadError(true);
        return;
      }
      const data = (await res.json()) as DecisionResponse;
      setDailyDecision(data.decision);
      setLoadError(false);
    } catch {
      setLoadError(true);
    }
  }, [configured, user]);

  const refreshPortfolio = useCallback(() => {
    if (!configured || !user || authLoading || isCompletingOAuth) return;

    setLoadError(false);
    setCompletedFetchKey(null);

    fetch("/api/zerodha/holdings")
      .then((res) => res.json())
      .then((data: HoldingsResponse) => {
        if (data.status === "OK" && data.portfolio) {
          updatePortfolio(data.portfolio);
          setConnectionStatus("CONNECTED");
        } else if (data.status === "TOKEN_EXPIRED") {
          setConnectionStatus("TOKEN_EXPIRED");
          if (data.portfolio) {
            updatePortfolio(data.portfolio);
          }
        } else {
          setConnectionStatus("NOT_CONNECTED");
        }
      })
      .catch(() => {
        setLoadError(true);
      })
      .finally(() => {
        setCompletedFetchKey(user.id);
        void loadDailyDecision();
      });
  }, [
    configured,
    user,
    authLoading,
    isCompletingOAuth,
    updatePortfolio,
    loadDailyDecision,
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

    fetch("/api/zerodha/holdings")
      .then((res) => res.json())
      .then((data: HoldingsResponse) => {
        if (cancelled) return;

        if (data.status === "OK" && data.portfolio) {
          updatePortfolio(data.portfolio);
          setConnectionStatus("CONNECTED");
        } else if (data.status === "TOKEN_EXPIRED") {
          setConnectionStatus("TOKEN_EXPIRED");
          if (data.portfolio) {
            updatePortfolio(data.portfolio);
          }
        } else {
          setConnectionStatus("NOT_CONNECTED");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setLoadError(true);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setCompletedFetchKey(portfolioFetchKey);
          void loadDailyDecision();
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    shouldFetchPortfolio,
    portfolioFetchKey,
    updatePortfolio,
    loadDailyDecision,
  ]);

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
  const showError = Boolean(oauthError) || loadError;

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
                  ? `Today: ${dailyDecision.decision.replaceAll("_", " ").toLowerCase()} (${dailyDecision.confidence}% confidence)`
                  : "Setting things up for you…"}
            </p>
          </div>

          {!isOnboarding && !isCompletingOAuth && (
            <div className="text-sm text-gray-500 italic">
              Take your time — this is guidance, not a command.
            </div>
          )}
        </div>

        {showError && (
          <ErrorBanner onRetry={refreshPortfolio} />
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
          <div className="text-xs text-teal-400/80">
            Your portfolio is synced and ready.
          </div>
        )}

        {showGuidance && !showError && (
          <>
            {!profileComplete && (
              <FinancialProfileSetup
                onComplete={(profile) => {
                  setFinancialProfile(profile);
                  void loadDailyDecision();
                }}
              />
            )}
            {dailyDecision ? (
              <DailyDecisionCard decision={dailyDecision} />
            ) : (
              <div className="p-6 rounded-2xl border border-white/10 bg-slate-900/50 space-y-3">
                <div className="h-2 w-24 rounded-full bg-white/10 animate-pulse" />
                <p className="text-sm text-gray-400 italic">
                  Setting things up for you…
                </p>
              </div>
            )}
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
