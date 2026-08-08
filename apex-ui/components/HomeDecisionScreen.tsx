"use client";

import { useMemo } from "react";
import { formatInr } from "@/lib/funds";
import { buildDecisionDepth } from "@/lib/dailyLoop/decisionDepth";
import { getDisciplineInterpretation } from "@/lib/dailyLoop/disciplineCopy";
import { getHeroTone } from "@/lib/dailyLoop/heroTone";
import {
  EXPLORE_EMPTY_BODY,
  EXPLORE_EMPTY_HEADLINE,
  formatJudgment,
  getApexHeroSignature,
} from "@/lib/dailyLoop/apexVoice";
import { getIntentExperience } from "@/lib/dailyLoop/intentExperience";
import { useDailyLoop } from "@/lib/useDailyLoop";
import { useDisciplineStreak } from "@/lib/useDisciplineStreak";
import { useIntentTransition } from "@/lib/useIntentTransition";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  BackgroundNote,
  ExplorePrimaryBlock,
  PrimaryEmphasis,
  ProtectPrimaryBlock,
  SystemContextLine,
  WatchSection,
  WhySection,
} from "@/components/dailyLoop/DecisionDepthSections";
import { ApexCard } from "@/components/ui/apex";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { StockPick } from "@/types/decision";
import type { UserIntent } from "@/types/intent";

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

function formatEntryType(entryType: "aggressive" | "confirmed"): string {
  return entryType === "aggressive" ? "Aggressive" : "Confirmed";
}

function formatOutcome(outcome: "win" | "loss" | "breakeven"): string {
  if (outcome === "win") {
    return "Win";
  }

  if (outcome === "loss") {
    return "Loss";
  }

  return "Breakeven";
}

function ExecutionPrimaryBlock({
  planLoading,
  hasPlan,
  plan,
  delayMs,
}: {
  planLoading: boolean;
  hasPlan: boolean;
  plan: ReturnType<typeof useDailyLoop>["plan"];
  delayMs: number;
}) {
  return (
    <section
      className="mb-5 animate-apex-fade-in"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <PrimaryEmphasis>
        {planLoading ? (
          <p className="text-lg font-medium text-apex-text/80">Building your plan…</p>
        ) : hasPlan && plan ? (
          <>
            <ol className="space-y-3">
              {plan.steps.map((step, index) => (
                <li
                  key={step}
                  className="flex gap-3 text-lg font-medium leading-snug text-apex-text"
                >
                  <span className="mt-1 text-sm tabular-nums text-apex-muted">
                    {index + 1}.
                  </span>
                  {step}
                </li>
              ))}
            </ol>
            <p className="text-sm text-apex-muted">
              Stop {plan.stopLoss !== null ? formatInr(plan.stopLoss) : "—"} · Entry{" "}
              {formatEntryType(plan.entryType)}
            </p>
          </>
        ) : (
          <p className="text-lg font-medium text-apex-text/80">
            Plan unavailable — check back shortly.
          </p>
        )}
      </PrimaryEmphasis>
    </section>
  );
}

export default function HomeDecisionScreen({
  decision,
  entryTiming,
  intent,
  topSymbol,
  topAllocationPct,
  className = "",
}: HomeDecisionScreenProps) {
  const { renderIntent, contentClassName } = useIntentTransition(intent);
  const experience = getIntentExperience(renderIntent);
  const {
    actionText,
    plan,
    planLoading,
    trustScore,
    trustDelta,
    trustMessage,
    lastOutcome,
  } = useDailyLoop(decision, entryTiming, intent);
  const retention = useDisciplineStreak({
    intent: renderIntent,
    action: decision.action,
    stock: decision.stock,
  });

  const resolvedDepth = useMemo(
    () =>
      buildDecisionDepth({
        ...decision,
        intent: renderIntent,
        entryTiming,
        planConviction: plan?.conviction,
        topSymbol,
        topAllocationPct,
      }),
    [
      decision,
      entryTiming,
      plan?.conviction,
      renderIntent,
      topAllocationPct,
      topSymbol,
    ],
  );

  const isBuy = decision.action === "buy";
  const isExplore = renderIntent === "explore";
  const isProtect = renderIntent === "protect";
  const isGrow = renderIntent === "grow";
  const isSell =
    isSellAction(decision.action as DecisionActionType) ||
    decision.action === "sell" ||
    decision.action === "reduce";
  const hasPicks = (decision.picks?.length ?? 0) > 0;
  const isExploreEmpty = isExplore && !hasPicks;
  const isNoTradeHero =
    (decision.action === "wait" || decision.action === "hold") && !hasPicks;
  const hasPlan = Boolean(plan && plan.steps.length > 0);
  let sectionDelay = 80;

  const nextDelay = () => {
    const value = sectionDelay;
    sectionDelay += 80;
    return value;
  };

  const heroTitle = isExploreEmpty
    ? EXPLORE_EMPTY_HEADLINE
    : isExplore
      ? "What is interesting today"
      : isNoTradeHero
        ? EXPLORE_EMPTY_HEADLINE
        : actionText;
  const heroTone = isExploreEmpty || isNoTradeHero
    ? EXPLORE_EMPTY_BODY
    : getHeroTone({
        intent: renderIntent,
        action: decision.action,
      });
  const heroSignature = getApexHeroSignature({
    intent: renderIntent,
    action: decision.action,
    seed: `${renderIntent}:${decision.action}:${decision.stock ?? "none"}`,
  });
  const disciplineLine = getDisciplineInterpretation(trustScore);
  const protectReason =
    decision.message ??
    decision.reason ??
    formatJudgment("Nothing is clean enough to risk capital", "patience matters");

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
          <header className="mb-6 space-y-2">
            <p className="text-xs text-apex-muted/60">
              {retention.dailyContextLabel}
            </p>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-apex-muted">
              {experience.tagline}
            </p>
            <h1 className="text-3xl font-semibold leading-tight tracking-tight text-apex-text sm:text-4xl">
              {heroTitle}
            </h1>
            <p className="mt-2 text-sm text-apex-muted">{heroTone}</p>
            {heroSignature ? (
              <p className="text-xs text-apex-muted/80">{heroSignature}</p>
            ) : null}
          </header>

          {isExplore && !isExploreEmpty ? (
            <ExplorePrimaryBlock
              setupItems={resolvedDepth.exploreSetupItems}
              delayMs={nextDelay()}
            />
          ) : null}

          {isGrow && isBuy ? (
            <ExecutionPrimaryBlock
              planLoading={planLoading}
              hasPlan={hasPlan}
              plan={plan}
              delayMs={nextDelay()}
            />
          ) : null}

          {isProtect ? (
            <ProtectPrimaryBlock
              reason={protectReason}
              riskElevated={decision.validation?.risk_ok === false}
              insight={resolvedDepth.protectAllocation}
              delayMs={nextDelay()}
            />
          ) : null}

          {isGrow && !isBuy ? (
            <section
              className="mb-5 animate-apex-fade-in"
              style={{ animationDelay: `${nextDelay()}ms` }}
            >
              <PrimaryEmphasis>
                <p className="text-lg font-medium leading-snug text-apex-text">
                  {decision.reason ?? decision.message ?? actionText}
                </p>
              </PrimaryEmphasis>
            </section>
          ) : null}

          {!isExplore ? (
            <>
              <WhySection bullets={resolvedDepth.whyBullets} delayMs={nextDelay()} />
              <WatchSection items={resolvedDepth.watchNext} delayMs={nextDelay()} />
            </>
          ) : null}

          {!isExploreEmpty ? (
            <SystemContextLine depth={resolvedDepth} delayMs={nextDelay()} />
          ) : null}

          {hasPlan && plan?.behaviorNote && isGrow ? (
            <BackgroundNote text={plan.behaviorNote} delayMs={nextDelay()} />
          ) : null}

          {isExplore && !isExploreEmpty ? (
            <BackgroundNote
              text={formatJudgment(
                "Observation builds judgment",
                "patience matters",
              )}
              delayMs={nextDelay()}
            />
          ) : null}

          {isProtect && isSell ? (
            <BackgroundNote
              text="Trim first, then wait for a cleaner setup before adding back."
              delayMs={nextDelay()}
            />
          ) : null}

          {!isExploreEmpty ? (
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

          <section
            className="mt-5 space-y-2 animate-apex-fade-in"
            style={{ animationDelay: `${nextDelay()}ms` }}
          >
            <p className="text-sm text-apex-text/80">{retention.streakMessage}</p>
            {retention.pressureLine && !retention.committedToday ? (
              <p className="text-xs text-apex-muted/80">{retention.pressureLine}</p>
            ) : null}
            <button
              type="button"
              onClick={retention.commitFollowed}
              disabled={retention.committedToday}
              className={[
                "text-left text-sm text-apex-text/85 transition-transform duration-150",
                retention.committedToday
                  ? "cursor-default opacity-70"
                  : "hover:text-apex-text active:scale-[0.98]",
              ].join(" ")}
            >
              {retention.committedToday
                ? "✓ Followed today"
                : "✓ I followed APEX today"}
            </button>
            {retention.rewardHook && retention.isWaitMode ? (
              <p className="text-xs text-apex-muted/50">{retention.rewardHook}</p>
            ) : null}
          </section>

          {lastOutcome && !isExploreEmpty ? (
            <section
              className="mt-6 space-y-3 animate-apex-fade-in opacity-90"
              style={{ animationDelay: `${nextDelay()}ms` }}
            >
              <div className="grid grid-cols-3 gap-3 text-xs text-apex-muted">
                <div>
                  <p>Discipline</p>
                  <p className="mt-1 text-sm font-medium text-apex-text">
                    {lastOutcome.disciplineScore}
                  </p>
                </div>
                <div>
                  <p>Execution</p>
                  <p className="mt-1 text-sm font-medium text-apex-text">
                    {lastOutcome.executionQuality}
                  </p>
                </div>
                <div>
                  <p>Outcome</p>
                  <p className="mt-1 text-sm font-medium text-apex-text">
                    {formatOutcome(lastOutcome.outcome)}
                  </p>
                </div>
              </div>
              <p className="text-sm leading-relaxed text-apex-text/75">
                {lastOutcome.summary}
              </p>
            </section>
          ) : null}
        </div>
      </ApexCard>
    </div>
  );
}
