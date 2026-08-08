"use client";

import type { ReactNode } from "react";
import { formatInr } from "@/lib/funds";
import { useDailyLoop } from "@/lib/useDailyLoop";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import { ApexBody, ApexCard } from "@/components/ui/apex";

export type HomeDecision = {
  action: string;
  stock?: string;
  amount?: number;
  confidence?: number;
  structureScore?: number;
  confidenceMetrics?: {
    expectedReturn?: number;
    probability?: number;
    edgeScore?: number;
    expectedDrawdown?: number;
  };
  validation?: {
    risk_ok?: boolean;
  };
};

export type HomeDecisionScreenProps = {
  decision: HomeDecision;
  entryTiming: EntryTimingState;
  className?: string;
};

function LoopSection({
  title,
  delayMs,
  children,
}: {
  title: string;
  delayMs: number;
  children: ReactNode;
}) {
  return (
    <section
      className="animate-apex-fade-in space-y-3 border-t border-apex-border/20 pt-5"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <h2 className="text-[13px] font-medium tracking-wide text-apex-muted">
        {title}
      </h2>
      {children}
    </section>
  );
}

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

export default function HomeDecisionScreen({
  decision,
  entryTiming,
  className = "",
}: HomeDecisionScreenProps) {
  const {
    actionText,
    plan,
    planLoading,
    trustScore,
    trustDelta,
    trustMessage,
    lastOutcome,
  } = useDailyLoop(decision, entryTiming);

  const isBuy = decision.action === "buy";
  const hasPlan = Boolean(plan && plan.steps.length > 0);
  let sectionIndex = 1;

  return (
    <div className={`mx-auto w-full max-w-[600px] ${className}`.trim()}>
      <ApexCard
        hover={false}
        padding="none"
        className="relative overflow-hidden border-apex-border/30 shadow-none animate-apex-rise-in"
      >
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-white/[0.03] to-transparent" />

        <div className="relative flex flex-col gap-5 p-6">
          <h1
            className="animate-apex-fade-in text-[28px] font-semibold leading-tight tracking-tight text-apex-text sm:text-[30px]"
            style={{ animationDelay: "0ms" }}
          >
            {actionText}
          </h1>

          {isBuy ? (
            <LoopSection
              title="How to act today"
              delayMs={sectionIndex++ * 100}
            >
              {planLoading ? (
                <ApexBody>Building your plan…</ApexBody>
              ) : hasPlan && plan ? (
                <div className="space-y-4">
                  <ol className="space-y-3">
                    {plan.steps.map((step, index) => (
                      <li
                        key={step}
                        className="flex gap-3 text-[14px] leading-snug text-apex-text/90"
                      >
                        <span className="mt-0.5 text-[12px] tabular-nums text-apex-muted">
                          {index + 1}.
                        </span>
                        {step}
                      </li>
                    ))}
                  </ol>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-apex-muted">
                    <span>
                      Stop{" "}
                      {plan.stopLoss !== null
                        ? formatInr(plan.stopLoss)
                        : "—"}
                    </span>
                    <span>Entry {formatEntryType(plan.entryType)}</span>
                  </div>
                </div>
              ) : (
                <ApexBody>Plan unavailable — check back shortly.</ApexBody>
              )}
            </LoopSection>
          ) : null}

          {hasPlan && plan?.behaviorNote ? (
            <LoopSection title="Mindset" delayMs={sectionIndex++ * 100}>
              <p className="text-[15px] leading-relaxed text-apex-text/85">
                {plan.behaviorNote}
              </p>
            </LoopSection>
          ) : null}

          <LoopSection title="Your discipline" delayMs={sectionIndex++ * 100}>
            <div className="flex items-baseline justify-between gap-4">
              <p className="text-[32px] font-semibold tabular-nums tracking-tight text-apex-text">
                {trustScore}
              </p>
              <p className="text-[14px]">
                <TrustDelta delta={trustDelta} />
              </p>
            </div>
            <p className="text-[14px] leading-relaxed text-apex-muted">
              {trustMessage}
            </p>
          </LoopSection>

          {lastOutcome ? (
            <LoopSection title="Your evolution" delayMs={sectionIndex * 100}>
              <div className="grid grid-cols-3 gap-3 text-[13px]">
                <div>
                  <p className="text-apex-muted">Discipline</p>
                  <p className="mt-1 font-medium text-apex-text">
                    {lastOutcome.disciplineScore}
                  </p>
                </div>
                <div>
                  <p className="text-apex-muted">Execution</p>
                  <p className="mt-1 font-medium text-apex-text">
                    {lastOutcome.executionQuality}
                  </p>
                </div>
                <div>
                  <p className="text-apex-muted">Outcome</p>
                  <p className="mt-1 font-medium text-apex-text">
                    {formatOutcome(lastOutcome.outcome)}
                  </p>
                </div>
              </div>
              <p className="text-[14px] leading-relaxed text-apex-text/85">
                {lastOutcome.summary}
              </p>
            </LoopSection>
          ) : null}
        </div>
      </ApexCard>
    </div>
  );
}
