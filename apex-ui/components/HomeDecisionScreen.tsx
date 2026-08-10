"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { buildCapitalDecision } from "@/lib/dailyLoop/capitalDecision";
import { resolveTodayHero, resolveTodayHeroDisplay } from "@/lib/dailyLoop/todaySurface";
import { getDisciplineInterpretation } from "@/lib/dailyLoop/disciplineCopy";
import {
  getBrokerStepLine,
  shouldAutoCommitDisciplineAfterBrokerFill,
} from "@/lib/dailyLoop/disciplineStreak";
import {
  markBrokerStepCompleted,
  readBrokerStepCompleted,
} from "@/lib/dailyLoop/brokerStepState";
import { getApexHeroSignature } from "@/lib/dailyLoop/apexVoice";
import { getIntentExperience } from "@/lib/dailyLoop/intentExperience";
import { useDailyLoop } from "@/lib/useDailyLoop";
import { useDisciplineStreak } from "@/lib/useDisciplineStreak";
import { useIntentTransition } from "@/lib/useIntentTransition";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  CapitalActionsBlock,
  ExecutionStatusBlock,
} from "@/components/dailyLoop/DecisionDepthSections";
import TodayExecutionPanel from "@/components/dailyLoop/TodayExecutionPanel";
import TodayMonitorStrip from "@/components/dailyLoop/TodayMonitorStrip";
import TodayTrustStrip from "@/components/dailyLoop/TodayTrustStrip";
import TodayProgressStrip from "@/components/dailyLoop/TodayProgressStrip";
import WeeklyReviewStrip from "@/components/dailyLoop/WeeklyReviewStrip";
import LastClosedTrustBlock from "@/components/dailyLoop/LastClosedTrustBlock";
import CapitalModeToggle from "@/components/dailyLoop/CapitalModeToggle";
import ExploreDecisionDepth from "@/components/dailyLoop/ExploreDecisionDepth";
import { ApexCard } from "@/components/ui/apex";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import type { StockPick } from "@/types/decision";
import type { UserIntent } from "@/types/intent";
import type { CapitalFundingMode } from "@/lib/dailyLoop/capitalMargin";
import type { BrokerFillSummary } from "@/services/trade/logTradeFill";
import type { TierFeatures } from "@/services/subscription/tier";
import type {
  DisciplineHistoryEntry,
  DisciplineHistorySummary,
} from "@/types/decisionHistory";
import PremiumFeatureGate from "@/components/dailyLoop/PremiumFeatureGate";
import { useExploreTriggers } from "@/lib/useExploreTriggers";
import { useDayPnlPoll } from "@/lib/useDayPnlPoll";
import { useMonitorDayPnlPoll } from "@/lib/useMonitorDayPnlPoll";
import { useOpenMonitor } from "@/lib/useOpenMonitor";
import { apiFetch, parseApiJson } from "@/lib/api/clientFetch";

export type HomeDecision = {
  action: string;
  stock?: string;
  amount?: number;
  confidence?: number;
  structureScore?: number;
  allocation?: number;
  suggested_sell_percent?: number;
  allocationPercent?: number;
  allocationReason?: string;
  reason?: string;
  message?: string;
  confidence_factors?: string[];
  confidenceMetrics?: {
    expectedReturn?: number;
    probability?: number;
    edgeScore?: number;
    expectedDrawdown?: number;
  };
  validation?: {
    signal_strength?: number;
    signal_agreement?: boolean;
    market_alignment?: boolean;
    risk_ok?: boolean;
  };
  picks?: StockPick[];
};

export type HomeDecisionScreenProps = {
  decision: HomeDecision;
  entryTiming: EntryTimingState;
  intent: UserIntent;
  topSymbol?: string;
  topAllocationPct?: number;
  availableCash?: number;
  ledgerCash?: number;
  portfolioValue?: number;
  totalCapital?: number;
  collateral?: number;
  capitalMode?: CapitalFundingMode;
  onCapitalModeChange?: (mode: CapitalFundingMode) => void;
  dayPnl?: number | null;
  holdings?: { symbol: string; weight: number }[];
  connectionStatus?: ConnectionStatus;
  decisionUpdatedAt?: string | null;
  fundsLoading?: boolean;
  fundsSynced?: boolean;
  fundsSyncError?: string | null;
  isRefreshing?: boolean;
  onCapitalRefresh?: () => void;
  onDisciplineCommitted?: () => void;
  disciplineHistory?: DisciplineHistoryEntry[];
  disciplineSummary?: DisciplineHistorySummary;
  disciplineDays?: string[];
  premiumFeatures?: TierFeatures;
  premiumActivationEnabled?: boolean;
  onPremiumActivated?: () => void;
  className?: string;
};

function TrustDelta({ delta }: { delta: number }) {
  if (delta > 0) {
    return <span className="text-emerald-300/90">↑ {delta}</span>;
  }

  if (delta < 0) {
    return <span className="text-amber-200/90">↓ {Math.abs(delta)}</span>;
  }

  return <span className="text-apex-muted/70">—</span>;
}

export default function HomeDecisionScreen({
  decision,
  entryTiming,
  intent,
  topSymbol,
  topAllocationPct,
  availableCash,
  ledgerCash,
  portfolioValue,
  totalCapital,
  collateral,
  capitalMode,
  onCapitalModeChange,
  dayPnl,
  holdings,
  connectionStatus = "NOT_CONNECTED",
  decisionUpdatedAt,
  fundsLoading = false,
  fundsSynced = false,
  fundsSyncError = null,
  isRefreshing = false,
  onCapitalRefresh,
  onDisciplineCommitted,
  disciplineHistory = [],
  disciplineSummary,
  disciplineDays = [],
  premiumFeatures,
  premiumActivationEnabled = false,
  onPremiumActivated,
  className = "",
}: HomeDecisionScreenProps) {
  const features = premiumFeatures ?? {
    marginMode: false,
    decisionDepth: false,
    decisionHistory: false,
  };
  const { renderIntent, contentClassName } = useIntentTransition(intent);
  const experience = getIntentExperience(renderIntent);
  const {
    trustScore,
    trustDelta,
    trustMessage,
    lastOutcome,
    lastOutcomeStock,
    refreshTrust,
    plan,
    planLoading,
  } = useDailyLoop(decision, entryTiming, intent);

  const capitalDecision = useMemo(
    () =>
      buildCapitalDecision({
        intent: renderIntent,
        action: decision.action,
        stock: decision.stock ?? topSymbol,
        picks: decision.picks,
        allocationPercent: decision.allocationPercent,
        suggested_sell_percent: decision.suggested_sell_percent,
        topAllocationPct,
        availableCash,
        ledgerCash,
        portfolioValue,
        collateral,
        capitalMode,
        holdings,
        entryTiming,
        confidence: decision.confidence,
      }),
    [
      availableCash,
      capitalMode,
      collateral,
      decision.action,
      decision.allocationPercent,
      decision.confidence,
      decision.picks,
      decision.stock,
      decision.suggested_sell_percent,
      entryTiming,
      holdings,
      ledgerCash,
      portfolioValue,
      renderIntent,
      topAllocationPct,
      topSymbol,
    ],
  );

  const retention = useDisciplineStreak({
    intent: renderIntent,
    action: decision.action,
    stock: decision.stock,
    deploymentPercentage: capitalDecision.deploymentPercentage,
    onCommitted: onDisciplineCommitted,
  });

  const todayHero = useMemo(
    () =>
      resolveTodayHero(capitalDecision, {
        suggestedSellPercent: decision.suggested_sell_percent,
      }),
    [capitalDecision, decision.suggested_sell_percent],
  );

  const [brokerStepCompleted, setBrokerStepCompleted] = useState(() => {
    const symbol = todayHero.symbol?.trim().toUpperCase();
    if (!symbol || typeof window === "undefined") {
      return false;
    }

    return readBrokerStepCompleted(symbol);
  });
  const [brokerFillSummary, setBrokerFillSummary] =
    useState<BrokerFillSummary | null>(null);
  const [brokerFillStatusLoading, setBrokerFillStatusLoading] = useState(() => {
    const symbol = todayHero.symbol?.trim().toUpperCase();
    if (!symbol || typeof window === "undefined") {
      return false;
    }

    return !readBrokerStepCompleted(symbol);
  });

  const actualSymbolWeight = useMemo(() => {
    if (!brokerStepCompleted || !todayHero.symbol || !holdings?.length) {
      return undefined;
    }

    const match = holdings.find(
      (holding) =>
        holding.symbol.trim().toUpperCase() ===
        todayHero.symbol?.trim().toUpperCase(),
    );

    return match?.weight;
  }, [brokerStepCompleted, holdings, todayHero.symbol]);

  const displayHero = useMemo(
    () =>
      resolveTodayHeroDisplay(todayHero, brokerStepCompleted, {
        actualPortfolioWeight: actualSymbolWeight,
        brokerFillSummary,
      }),
    [actualSymbolWeight, brokerFillSummary, brokerStepCompleted, todayHero],
  );

  useEffect(() => {
    if (!todayHero.symbol) {
      setBrokerStepCompleted(false);
      setBrokerFillSummary(null);
      setBrokerFillStatusLoading(false);
      return;
    }

    const sessionComplete = readBrokerStepCompleted(todayHero.symbol);
    if (sessionComplete) {
      setBrokerStepCompleted(true);
      setBrokerFillStatusLoading(false);
    } else {
      setBrokerFillStatusLoading(true);
    }

    let cancelled = false;

    void (async () => {
      try {
        const response = await apiFetch(
          `/api/trade/status?stock=${encodeURIComponent(todayHero.symbol ?? "")}`,
          { cache: "no-store" },
        );
        const payload = await parseApiJson<{
          filledToday?: boolean;
          orderId?: string;
          quantity?: number;
          side?: "buy" | "sell";
          price?: number;
        }>(response, "Trade status");

        if (cancelled) {
          return;
        }

        if (!response.ok) {
          return;
        }

        if (!payload?.filledToday) {
          if (!sessionComplete) {
            setBrokerStepCompleted(false);
            setBrokerFillSummary(null);
          }
          return;
        }

        if (
          payload.orderId &&
          typeof payload.quantity === "number" &&
          (payload.side === "buy" || payload.side === "sell")
        ) {
          setBrokerFillSummary({
            orderId: payload.orderId,
            quantity: payload.quantity,
            side: payload.side,
            price: payload.price,
          });
        }

        markBrokerStepCompleted(todayHero.symbol ?? "");
        setBrokerStepCompleted(true);

        if (!sessionComplete) {
          onCapitalRefresh?.();
        }
      } catch {
        // Session cache remains the fallback when the status API is unavailable.
      } finally {
        if (!cancelled) {
          setBrokerFillStatusLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [onCapitalRefresh, todayHero.symbol]);

  const holdingAllocationPct =
    todayHero.currentWeight ??
    topAllocationPct ??
    capitalDecision.actions.find((action) => action.symbol === todayHero.symbol)
      ?.portfolioWeight;

  const isExplore = renderIntent === "explore";
  const isGrow = renderIntent === "grow";
  const isProtect = renderIntent === "protect";
  const isCapitalDeployment = isGrow || isProtect;
  const monitorEnabled =
    isCapitalDeployment && connectionStatus === "CONNECTED";
  const {
    positions: monitorPositions,
    loading: monitorLoading,
    refresh: refreshMonitor,
  } = useOpenMonitor({ enabled: monitorEnabled });
  const { dayPnl: liveDayPnl, refresh: refreshLiveDayPnl } = useDayPnlPoll({
    enabled: monitorEnabled,
  });
  const { dayPnl: monitorLiveDayPnl, refresh: refreshMonitorDayPnl } =
    useMonitorDayPnlPoll({ enabled: monitorEnabled });
  const resolvedDayPnl = liveDayPnl ?? dayPnl;
  const monitorStripDayPnl = monitorLiveDayPnl;

  const handleExecuted = useCallback(
    (fill?: BrokerFillSummary) => {
      if (todayHero.symbol) {
        markBrokerStepCompleted(todayHero.symbol);
        setBrokerStepCompleted(true);
      }

      if (fill?.orderId) {
        setBrokerFillSummary(fill);
      }

      onCapitalRefresh?.();
      void refreshMonitor();
      void refreshLiveDayPnl();
      void refreshMonitorDayPnl();
      void refreshTrust();
    },
    [
      onCapitalRefresh,
      refreshLiveDayPnl,
      refreshMonitor,
      refreshMonitorDayPnl,
      refreshTrust,
      todayHero.symbol,
    ],
  );

  useEffect(() => {
    if (!brokerStepCompleted) {
      return;
    }

    onDisciplineCommitted?.();

    if (
      !shouldAutoCommitDisciplineAfterBrokerFill(
        brokerStepCompleted,
        retention.committedToday,
      )
    ) {
      return;
    }

    retention.commitFollowed();
  }, [
    brokerStepCompleted,
    onDisciplineCommitted,
    retention.commitFollowed,
    retention.committedToday,
  ]);

  const explorePicks = useMemo(() => {
    if (!isExplore || !decision.picks?.length) {
      return [];
    }

    const symbols = new Set(
      capitalDecision.exploreSetups.map((setup) => setup.symbol),
    );

    return decision.picks.filter((pick) => symbols.has(pick.stock));
  }, [capitalDecision.exploreSetups, decision.picks, isExplore]);

  const {
    triggerBySymbol: exploreTriggerBySymbol,
    loading: exploreTriggersLoading,
  } = useExploreTriggers({
    enabled: isExplore && explorePicks.length > 0,
    picks: explorePicks,
    refreshKey: decisionUpdatedAt,
  });
  const isExploreEmpty =
    isExplore &&
    capitalDecision.exploreSetups.length === 0 &&
    capitalDecision.actions.length === 0;
  let sectionDelay = 80;

  const nextDelay = () => {
    const value = sectionDelay;
    sectionDelay += 80;
    return value;
  };

  const heroTitle = isCapitalDeployment
    ? displayHero.headline
    : capitalDecision.heroHeadline;
  const heroTone = isCapitalDeployment
    ? displayHero.subline
    : capitalDecision.heroSubline;
  const heroSignature = isCapitalDeployment
    ? null
    : getApexHeroSignature({
        intent: renderIntent,
        action: decision.action,
        seed: `${renderIntent}:${decision.action}:${decision.stock ?? "none"}`,
      });
  const disciplineLine = getDisciplineInterpretation(trustScore);
  const brokerStepLine = isCapitalDeployment
    ? getBrokerStepLine(
        retention.committedToday,
        todayHero.executionKind,
        brokerStepCompleted,
      )
    : null;

  return (
    <div className={`mx-auto w-full max-w-[600px] ${className}`.trim()}>
      <ApexCard
        hover={false}
        padding="none"
        className="relative overflow-hidden border-apex-border/20 shadow-none animate-apex-rise-in"
      >
        <div
          className={[
            "pointer-events-none absolute inset-0 bg-gradient-to-b to-transparent",
            experience.cardGradient,
          ].join(" ")}
        />

        <div className={`relative p-6 ${contentClassName}`}>
          <div className="mb-6 space-y-4">
            <TodayTrustStrip
              connectionStatus={connectionStatus}
              marginAvailable={availableCash}
              ledgerCash={ledgerCash}
              collateral={collateral}
              portfolioValue={portfolioValue}
              totalCapital={
                totalCapital ??
                (portfolioValue !== undefined && ledgerCash !== undefined
                  ? portfolioValue + ledgerCash
                  : undefined)
              }
              dayPnl={resolvedDayPnl}
              updatedAt={decisionUpdatedAt}
              fundsLoading={fundsLoading}
              fundsSynced={fundsSynced}
              fundsSyncError={fundsSyncError}
            />

            {isCapitalDeployment ? (
              <TodayProgressStrip
                dayPnl={resolvedDayPnl}
                trustScore={trustScore}
                trustDelta={trustDelta}
                streakCount={retention.streakCount}
                streakMessage={retention.streakMessage}
              />
            ) : null}

            {isCapitalDeployment ? (
              <WeeklyReviewStrip
                history={disciplineHistory}
                summary={disciplineSummary}
                days={disciplineDays}
              />
            ) : null}

            {isCapitalDeployment && lastOutcome ? (
              <LastClosedTrustBlock
                lastOutcome={lastOutcome}
                lastOutcomeStock={lastOutcomeStock}
                compact
              />
            ) : null}

            {isCapitalDeployment && onCapitalModeChange ? (
              <CapitalModeToggle
                mode={capitalMode ?? "CASH"}
                onModeChange={onCapitalModeChange}
                collateral={collateral}
                premiumLocked={!features.marginMode}
                activationEnabled={premiumActivationEnabled}
                onPremiumActivated={onPremiumActivated}
              />
            ) : null}

            {isRefreshing ? (
              <p className="text-xs text-apex-muted/60">Refreshing decision…</p>
            ) : null}
          </div>

          <header className="mb-6 space-y-2">
            <p className="text-xs text-apex-muted/60">
              {retention.dailyContextLabel}
            </p>
            {retention.decisionTensionLine ? (
              <p className="text-xs text-apex-muted/55">
                {retention.decisionTensionLine}
              </p>
            ) : null}
            {brokerStepLine ? (
              <p className="text-xs text-apex-muted/55">{brokerStepLine}</p>
            ) : null}
            {isCapitalDeployment ? (
              <p className="text-xs text-apex-muted/50">
                {retention.sessionTimeContext}
              </p>
            ) : null}
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-apex-muted">
              {isCapitalDeployment ? "Today's capital decision" : experience.tagline}
            </p>
            <h1 className="text-3xl font-bold leading-tight tracking-tight text-apex-text">
              {heroTitle}
            </h1>
            <p className="mt-2 text-sm text-apex-muted">{heroTone}</p>
            {capitalDecision.behaviorLock ? (
              <p className="text-xs font-medium text-apex-text/75">
                {capitalDecision.behaviorLock}
              </p>
            ) : null}
            {heroSignature ? (
              <p className="text-xs text-apex-muted/80">{heroSignature}</p>
            ) : null}
          </header>

          {isCapitalDeployment ? (
            <div className="mb-6">
              <TodayExecutionPanel
                hero={todayHero}
                portfolioValue={portfolioValue ?? 0}
                holdingAllocationPct={holdingAllocationPct}
                entryTiming={entryTiming}
                plan={plan}
                planLoading={planLoading}
                brokerStepCompleted={brokerStepCompleted}
                brokerFillSummary={brokerFillSummary}
                postTrimPortfolioWeight={actualSymbolWeight}
                brokerFillStatusLoading={brokerFillStatusLoading}
                onExecuted={handleExecuted}
              />
              <div className="mt-4">
                <TodayMonitorStrip
                  positions={monitorPositions}
                  dayPnl={monitorStripDayPnl}
                  loading={monitorLoading}
                />
              </div>
            </div>
          ) : null}

          {isCapitalDeployment ? (
            <details className="mb-6 group rounded-xl border border-apex-border/15 bg-white/[0.02]">
              <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-apex-text/85 marker:content-none">
                Decision depth
              </summary>
              <div className="border-t border-apex-border/10 px-4 py-4">
                {features.decisionDepth ? (
                  <CapitalActionsBlock
                    decision={capitalDecision}
                    delayMs={nextDelay()}
                    depthOnly
                    brokerStepCompleted={brokerStepCompleted}
                    brokerSymbol={todayHero.symbol}
                    executionKind={todayHero.executionKind}
                    postTrimPortfolioWeight={actualSymbolWeight}
                    projectedWeightAfter={todayHero.targetWeightAfter}
                    brokerFillSummary={brokerFillSummary}
                  />
                ) : (
                  <PremiumFeatureGate
                    feature="decisionDepth"
                    activationEnabled={premiumActivationEnabled}
                    onActivated={onPremiumActivated}
                  />
                )}
              </div>
            </details>
          ) : (
            <>
              <CapitalActionsBlock
                decision={capitalDecision}
                delayMs={nextDelay()}
                liveTriggers={exploreTriggerBySymbol}
                liveTriggersLoading={exploreTriggersLoading}
              />
              <details className="mb-6 group rounded-xl border border-apex-border/15 bg-white/[0.02]">
                <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-apex-text/85 marker:content-none">
                  Why &amp; watch
                </summary>
                <div className="border-t border-apex-border/10 px-4 py-4">
                  {features.decisionDepth ? (
                    <ExploreDecisionDepth
                      decision={decision}
                      intent={renderIntent}
                      entryTiming={entryTiming}
                      topSymbol={topSymbol}
                      topAllocationPct={topAllocationPct}
                      planConviction={plan?.conviction}
                      delayMs={nextDelay()}
                    />
                  ) : (
                    <PremiumFeatureGate
                    feature="decisionDepth"
                    activationEnabled={premiumActivationEnabled}
                    onActivated={onPremiumActivated}
                  />
                  )}
                </div>
              </details>
            </>
          )}

          {!isExploreEmpty && !isCapitalDeployment ? (
            <section
              className="mt-6 space-y-1 animate-apex-fade-in"
              style={{ animationDelay: `${nextDelay()}ms` }}
            >
              <div className="flex items-baseline justify-between gap-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
                    Discipline
                  </p>
                  <p className="text-3xl font-semibold tabular-nums tracking-tight text-apex-text">
                    {trustScore}
                  </p>
                </div>
                <p className="text-sm">
                  <TrustDelta delta={trustDelta} />
                </p>
              </div>
              <p className="text-sm text-apex-text/80">{disciplineLine}</p>
              <p className="text-xs text-apex-muted">{trustMessage}</p>
            </section>
          ) : null}

          <ExecutionStatusBlock
            committedToday={retention.committedToday}
            onMarkFollowed={retention.commitFollowed}
            streakMessage={retention.streakMessage}
            pressureLine={retention.pressureLine}
            waitDisciplineReward={retention.waitDisciplineReward}
            rewardHook={retention.rewardHook}
            commitmentHeadline={retention.commitmentHeadline}
            commitmentMicroReward={retention.commitmentMicroReward}
            delayMs={nextDelay()}
            capitalDeployment={isCapitalDeployment}
            decision={capitalDecision}
            executionKind={todayHero.executionKind}
            brokerStepCompleted={brokerStepCompleted}
          />

          {lastOutcome && !isExploreEmpty && !isCapitalDeployment ? (
            <LastClosedTrustBlock
              lastOutcome={lastOutcome}
              lastOutcomeStock={lastOutcomeStock}
            />
          ) : null}
        </div>
      </ApexCard>
    </div>
  );
}
