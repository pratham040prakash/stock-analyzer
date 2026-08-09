"use client";

import { useMemo } from "react";
import { formatInr } from "@/lib/funds";
import { buildCapitalDecision } from "@/lib/dailyLoop/capitalDecision";
import { getDisciplineInterpretation } from "@/lib/dailyLoop/disciplineCopy";
import { getApexHeroSignature } from "@/lib/dailyLoop/apexVoice";
import { getIntentExperience } from "@/lib/dailyLoop/intentExperience";
import { useDailyLoop } from "@/lib/useDailyLoop";
import { useDisciplineStreak } from "@/lib/useDisciplineStreak";
import { useIntentTransition } from "@/lib/useIntentTransition";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  CapitalActionsBlock,
  PrimaryEmphasis,
} from "@/components/dailyLoop/DecisionDepthSections";
import { ApexCard } from "@/components/ui/apex";
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
        entryTiming,
        confidence: decision.confidence,
      }),
    [
      decision.action,
      decision.allocationPercent,
      decision.confidence,
      decision.picks,
      decision.stock,
      decision.suggested_sell_percent,
      entryTiming,
      renderIntent,
      topAllocationPct,
      topSymbol,
    ],
  );

  const isBuy = decision.action === "buy";
  const isExplore = renderIntent === "explore";
  const isGrow = renderIntent === "grow";
  const hasPicks = (decision.picks?.length ?? 0) > 0;
  const isExploreEmpty = isExplore && !hasPicks && capitalDecision.actions.length === 0;
  const hasPlan = Boolean(plan && plan.steps.length > 0);
  let sectionDelay = 80;

  const nextDelay = () => {
    const value = sectionDelay;
    sectionDelay += 80;
    return value;
  };

  const heroTitle = capitalDecision.heroHeadline;
  const heroTone = capitalDecision.heroSubline;
  const heroSignature = getApexHeroSignature({
    intent: renderIntent,
    action: decision.action,
    seed: `${renderIntent}:${decision.action}:${decision.stock ?? "none"}`,
  });
  const disciplineLine = getDisciplineInterpretation(trustScore);

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

          <CapitalActionsBlock
            decision={capitalDecision}
            delayMs={nextDelay()}
          />

          {isGrow && isBuy ? (
            <ExecutionPrimaryBlock
              planLoading={planLoading}
              hasPlan={hasPlan}
              plan={plan}
              delayMs={nextDelay()}
            />
          ) : null}

          {hasPlan && plan?.behaviorNote && isGrow && isBuy ? (
            <p
              className="mt-4 text-sm leading-relaxed text-apex-text/60 animate-apex-fade-in"
              style={{ animationDelay: `${nextDelay()}ms` }}
            >
              {plan.behaviorNote}
            </p>
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
