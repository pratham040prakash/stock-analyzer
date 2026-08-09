"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  deployableFundsForIntent,
  getAllocation,
  instrumentPlanWithoutFunds,
  recommendationsToPlanItems,
} from "@/lib/allocation";
import { buildCapitalDecision } from "@/lib/dailyLoop/capitalDecision";
import {
  CapitalActionsBlock,
} from "@/components/dailyLoop/DecisionDepthSections";
import {
  getAllRecommendations,
  type RecommendationPortfolio,
} from "@/lib/recommendations";
import ExecutionPlan from "@/components/decision/ExecutionPlan";
import OpportunitiesList from "@/components/decision/OpportunitiesList";
import type { PortfolioRiskLevel } from "@/lib/portfolioRisk";
import type { DailyDecisionOutput } from "@/types/decision";
import type { Intent } from "@/types/intent";
import { resolveIntent } from "@/types/intent";
import {
  buildSellPercentOptions,
  decisionHeroActionText,
  decisionRiskMicrocopy,
  isSellAction,
} from "@/types/decision";
import { computeSellImpact } from "@/lib/sellImpact";
import {
  ApexBody,
  ApexButton,
  ApexCard,
  ApexDivider,
  ApexTitle,
} from "@/components/ui/apex";
import ActionToast from "./ActionToast";
import DailyDisciplineLoop from "./decision/DailyDisciplineLoop";
import SellConfirmModal from "./SellConfirmModal";

type CardView = "summary" | "execution" | "opportunities";

type Props = {
  decision: DailyDecisionOutput;
  totalValue?: number;
  isRefreshing?: boolean;
  intent?: Intent;
  availableCash?: number;
  riskLevel?: PortfolioRiskLevel;
  portfolioContext?: RecommendationPortfolio;
  onIntentChange?: (intent: Intent) => void;
  updatedAt?: string | null;
};

function scrollToExecutionSection() {
  document.getElementById("execution-section")?.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
  });
}

export default function DailyDecisionCard({
  decision,
  totalValue = 0,
  isRefreshing = false,
  intent,
  availableCash,
  riskLevel = "Low",
  portfolioContext = {},
  onIntentChange,
  updatedAt,
}: Props) {
  const [view, setView] = useState<CardView>("summary");
  const [selectedSellPercent, setSelectedSellPercent] = useState<
    number | null
  >(null);
  const [pendingSellPercent, setPendingSellPercent] = useState<number | null>(
    null,
  );
  const [showAdjust, setShowAdjust] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const canTrim = isSellAction(decision.action) && Boolean(decision.stock);
  const isBuy = decision.action === "buy";
  const isExplore = decision.action === "explore";
  const suggestedSellPercent = decision.suggested_sell_percent ?? 20;
  const sellOptions = buildSellPercentOptions(decision.suggested_sell_percent);
  const activeSellPercent = selectedSellPercent ?? suggestedSellPercent;
  const heroAction = decisionHeroActionText(decision, activeSellPercent);
  const riskMicrocopy =
    canTrim && decision.allocation !== undefined
      ? decisionRiskMicrocopy(decision.allocation, activeSellPercent)
      : null;

  const capitalDecision = useMemo(
    () =>
      buildCapitalDecision({
        action: decision.action,
        stock: decision.stock,
        confidence: decision.confidence,
        picks: decision.picks,
        suggested_sell_percent: decision.suggested_sell_percent,
        allocationPercent: decision.allocationPercent,
        intent: resolveIntent(intent),
        topAllocationPct: portfolioContext.top_allocation_pct,
        availableCash,
        portfolioValue: totalValue,
        holdings: portfolioContext.holdings?.map((holding) => ({
          symbol: holding.symbol,
          weight: holding.allocation_pct ?? 0,
        })),
        entryTiming: { enter: isBuy },
      }),
    [
      availableCash,
      decision.action,
      decision.allocationPercent,
      decision.confidence,
      decision.picks,
      decision.stock,
      decision.suggested_sell_percent,
      intent,
      isBuy,
      portfolioContext.holdings,
      portfolioContext.top_allocation_pct,
      totalValue,
    ],
  );

  const opportunities = decision.opportunities ?? [];

  const recommendedPlan = useMemo(() => {
    if (!isBuy && !isExplore) {
      return [];
    }

    if (decision.recommended_allocation?.length) {
      return decision.recommended_allocation;
    }

    if (intent && availableCash !== undefined && availableCash > 0) {
      const deployable = deployableFundsForIntent(availableCash, intent);
      const plan = getAllocation(deployable, intent, riskLevel, portfolioContext);
      if (plan.length > 0) {
        return plan;
      }
    }

    if (opportunities.length > 0) {
      return opportunities.map((opportunity) => ({
        name: opportunity.name,
        amount: 0,
        reason: opportunity.type,
      }));
    }

    if (intent) {
      return instrumentPlanWithoutFunds(intent, riskLevel, portfolioContext);
    }

    return [];
  }, [
    availableCash,
    decision.recommended_allocation,
    intent,
    isBuy,
    isExplore,
    opportunities,
    portfolioContext,
    riskLevel,
  ]);

  const allRecommendations = useMemo(() => {
    if (!intent || (!isBuy && !isExplore)) {
      return [];
    }

    const amounts = new Map(
      recommendedPlan.map((item) => [item.name, item.amount]),
    );

    return recommendationsToPlanItems(
      getAllRecommendations(intent, riskLevel, portfolioContext),
      amounts,
    );
  }, [intent, isBuy, isExplore, portfolioContext, recommendedPlan, riskLevel]);

  const allOpportunities = useMemo(() => {
    if (!intent || (!isBuy && !isExplore)) {
      return opportunities;
    }

    return getAllRecommendations(intent, riskLevel, portfolioContext).map(
      (recommendation) => ({
        name: recommendation.name,
        type: recommendation.type,
      }),
    );
  }, [intent, isBuy, isExplore, opportunities, portfolioContext, riskLevel]);

  const sellImpact =
    pendingSellPercent !== null &&
    decision.stock &&
    decision.allocation !== undefined
      ? computeSellImpact(
          decision.allocation,
          pendingSellPercent,
          totalValue,
        )
      : null;

  useEffect(() => {
    setView("summary");
    setSelectedSellPercent(null);
    setShowAdjust(false);
    setShowReasoning(false);
  }, [
    decision.suggested_sell_percent,
    decision.stock,
    decision.action,
    intent,
  ]);

  useEffect(() => {
    if (!toastMessage) return;

    const timer = window.setTimeout(() => {
      setToastMessage(null);
    }, 3500);

    return () => window.clearTimeout(timer);
  }, [toastMessage]);

  const openConfirm = useCallback((percent: number) => {
    setSelectedSellPercent(percent);
    setPendingSellPercent(percent);
  }, []);

  const handleCancel = useCallback(() => {
    if (processing) return;
    setPendingSellPercent(null);
  }, [processing]);

  const handleConfirm = useCallback(async () => {
    if (processing || pendingSellPercent === null) return;

    setProcessing(true);
    try {
      await new Promise((resolve) => window.setTimeout(resolve, 1400));
      setToastMessage("Order placed successfully");
      setPendingSellPercent(null);
      setShowAdjust(false);
    } finally {
      setProcessing(false);
    }
  }, [pendingSellPercent, processing]);

  const onStartInvesting = useCallback(() => {
    setView("execution");
    requestAnimationFrame(scrollToExecutionSection);
  }, []);

  const onReviewIdeas = useCallback(() => {
    onIntentChange?.("explore");
    setView("opportunities");
    requestAnimationFrame(scrollToExecutionSection);
  }, [onIntentChange]);

  const primaryLabel = canTrim
    ? `Sell ${activeSellPercent}% Now`
    : isBuy
      ? "View Allocation Plan"
      : isExplore
        ? "Review Ideas"
        : "Got It";

  return (
    <>
      <div className="space-y-4">
        <ApexCard className="relative">
        {isRefreshing ? (
          <div
            className="pointer-events-none absolute inset-0 z-10 rounded-2xl bg-white/[0.02] animate-pulse"
            aria-hidden
          />
        ) : null}

        {view === "summary" ? (
          <>
            <header className="mb-6 space-y-2">
              <ApexTitle className="text-3xl sm:text-4xl">
                {capitalDecision.heroHeadline}
              </ApexTitle>
              <ApexBody className="text-sm text-apex-muted">
                {capitalDecision.heroSubline}
              </ApexBody>
              {capitalDecision.heroDecisionCue ? (
                <p className="text-xs text-apex-muted/60">
                  {capitalDecision.heroDecisionCue}
                </p>
              ) : null}
              {capitalDecision.behaviorLock ? (
                <p className="text-xs font-medium text-apex-text/75">
                  {capitalDecision.behaviorLock}
                </p>
              ) : null}
              <p className="text-xs text-apex-muted/70">
                {capitalDecision.heroAccountability}
              </p>
            </header>

            <CapitalActionsBlock decision={capitalDecision} delayMs={0} />
          </>
        ) : null}

        <div id="execution-section" className="mt-5 min-h-[6rem] space-y-3">
          {view === "execution" ? (
            <ExecutionPlan
              items={recommendedPlan}
              allItems={allRecommendations}
              onBack={() => setView("summary")}
            />
          ) : null}

          {view === "opportunities" ? (
            <OpportunitiesList
              opportunities={opportunities}
              allOpportunities={allOpportunities}
              plan={recommendedPlan}
              onBack={() => setView("summary")}
            />
          ) : null}

          {view === "summary" ? (
            <>
              {isBuy || isExplore ? (
                <ApexButton
                  variant={isExplore ? "secondary" : "primary"}
                  onClick={isBuy ? onStartInvesting : onReviewIdeas}
                >
                  {primaryLabel}
                </ApexButton>
              ) : (
                <>
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <ApexButton
                      variant={canTrim ? "primary" : "secondary"}
                      disabled={processing}
                      onClick={() => {
                        if (canTrim) {
                          openConfirm(activeSellPercent);
                        }
                      }}
                      className={
                        canTrim
                          ? "!bg-red-500 hover:!bg-red-400 !text-white"
                          : undefined
                      }
                    >
                      {primaryLabel}
                    </ApexButton>

                    {canTrim ? (
                      <ApexButton
                        variant="secondary"
                        disabled={processing}
                        fullWidth
                        onClick={() => setShowAdjust((open) => !open)}
                      >
                        Adjust Amount
                      </ApexButton>
                    ) : null}
                  </div>

                  {riskMicrocopy ? (
                    <ApexBody>{riskMicrocopy}</ApexBody>
                  ) : null}

                  {canTrim && showAdjust ? (
                    <div className="flex flex-wrap gap-2">
                      {sellOptions.map((percent) => {
                        const isActive = activeSellPercent === percent;
                        return (
                          <button
                            key={percent}
                            type="button"
                            disabled={processing}
                            onClick={() => {
                              setSelectedSellPercent(percent);
                              openConfirm(percent);
                            }}
                            className={[
                              "rounded-lg border px-3 py-2 text-[13px] font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]",
                              isActive
                                ? "border-red-500/40 bg-red-500/15 text-red-100"
                                : "border-apex-border bg-apex-bg text-apex-muted hover:bg-white/[0.03]",
                            ].join(" ")}
                          >
                            Sell {percent}%
                          </button>
                        );
                      })}
                    </div>
                  ) : null}
                </>
              )}

              <button
                type="button"
                onClick={() => setShowReasoning((open) => !open)}
                className="text-[13px] text-apex-muted transition-colors hover:text-apex-text"
              >
                {showReasoning ? "Hide reasoning" : "See reasoning"}
              </button>
            </>
          ) : null}
        </div>

        {view === "summary" && showReasoning ? (
          <>
            <ApexDivider className="my-4" />
            <div className="space-y-4">
              {decision.confidence_factors.length > 0 ? (
                <ul className="space-y-2">
                  {decision.confidence_factors.map((factor) => (
                    <li
                      key={factor}
                      className="flex gap-2 text-[13px] text-apex-text/90"
                    >
                      <span className="text-apex-muted">•</span>
                      {factor}
                    </li>
                  ))}
                </ul>
              ) : (
                <ApexBody>{decision.reason}</ApexBody>
              )}

              {decision.actions.length > 0 ? (
                <ul className="space-y-2">
                  {decision.actions.map((action) => (
                    <li key={action} className="text-[13px] text-apex-muted">
                      • {action}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          </>
        ) : null}
        </ApexCard>

        {view === "summary" ? (
          <DailyDisciplineLoop updatedAt={updatedAt} />
        ) : null}
      </div>

      {decision.stock && sellImpact ? (
        <SellConfirmModal
          open={pendingSellPercent !== null}
          stock={decision.stock}
          impact={sellImpact}
          processing={processing}
          onConfirm={() => void handleConfirm()}
          onCancel={handleCancel}
        />
      ) : null}

      <ActionToast message={toastMessage} />
    </>
  );
}
