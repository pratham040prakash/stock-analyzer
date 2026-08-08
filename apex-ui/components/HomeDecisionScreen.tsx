"use client";

import type { ReactNode } from "react";
import { formatInr } from "@/lib/funds";
import { getIntentExperience } from "@/lib/dailyLoop/intentExperience";
import { useDailyLoop } from "@/lib/useDailyLoop";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import { ApexBody, ApexCard } from "@/components/ui/apex";
import type { StockPick } from "@/types/decision";
import type { UserIntent } from "@/types/intent";

export type HomeDecision = {
  action: string;
  stock?: string;
  amount?: number;
  confidence?: number;
  structureScore?: number;
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
    risk_ok?: boolean;
  };
  picks?: StockPick[];
};

export type HomeDecisionScreenProps = {
  decision: HomeDecision;
  entryTiming: EntryTimingState;
  intent: UserIntent;
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

function ExploreInsightList({ picks }: { picks: StockPick[] }) {
  const visible = picks.slice(0, 3);

  if (visible.length === 0) {
    return <ApexBody>Nothing stands out sharply today — that is useful information too.</ApexBody>;
  }

  return (
    <ul className="space-y-3">
      {visible.map((pick) => (
        <li key={pick.stock} className="text-[14px] leading-snug text-apex-text/90">
          <span className="font-medium text-apex-text">{pick.stock}</span>
          <span className="text-apex-muted">
            {" "}
            — trend {pick.signals.trend}, momentum {pick.signals.momentum}
          </span>
        </li>
      ))}
    </ul>
  );
}

function SafetyBlock({ decision }: { decision: HomeDecision }) {
  const factors = decision.confidence_factors?.slice(0, 3) ?? [];
  const riskOk = decision.validation?.risk_ok;

  return (
    <div className="space-y-3">
      <p className="text-[15px] leading-relaxed text-apex-text/85">
        {decision.reason ??
          "Conditions are not strong enough to risk capital today."}
      </p>
      <ul className="space-y-2">
        {factors.map((factor) => (
          <li key={factor} className="text-[13px] text-apex-muted">
            • {factor}
          </li>
        ))}
      </ul>
      {riskOk === false ? (
        <p className="text-[13px] text-amber-200/80">
          Portfolio risk is elevated — protecting capital comes first.
        </p>
      ) : (
        <p className="text-[13px] text-apex-muted">
          No action is the right action when the setup is not clear.
        </p>
      )}
    </div>
  );
}

export default function HomeDecisionScreen({
  decision,
  entryTiming,
  intent,
  className = "",
}: HomeDecisionScreenProps) {
  const experience = getIntentExperience(intent);
  const {
    actionText,
    plan,
    planLoading,
    trustScore,
    trustDelta,
    trustMessage,
    lastOutcome,
  } = useDailyLoop(decision, entryTiming, intent);

  const isBuy = decision.action === "buy";
  const hasPlan = Boolean(plan && plan.steps.length > 0);
  let sectionIndex = 1;

  return (
    <div className={`mx-auto w-full max-w-[600px] ${className}`.trim()}>
      <ApexCard
        hover={false}
        padding="none"
        className={[
          "relative overflow-hidden border-apex-border/30 shadow-none animate-apex-rise-in",
        ].join(" ")}
      >
        <div
          className={[
            "pointer-events-none absolute inset-0 bg-gradient-to-b to-transparent",
            experience.cardGradient,
          ].join(" ")}
        />

        <div className="relative flex flex-col gap-5 p-6">
          <div
            className="animate-apex-fade-in space-y-2"
            style={{ animationDelay: "0ms" }}
          >
            <p className="text-[12px] font-medium uppercase tracking-[0.14em] text-apex-muted">
              {experience.tagline}
            </p>
            <h1 className="text-[28px] font-semibold leading-tight tracking-tight text-apex-text sm:text-[30px]">
              {actionText}
            </h1>
          </div>

          {experience.showExecution && isBuy ? (
            <LoopSection
              title={experience.executionTitle}
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

          {experience.showExploreInsights ? (
            <LoopSection
              title={experience.exploreTitle}
              delayMs={sectionIndex++ * 100}
            >
              {decision.reason ? (
                <p className="text-[14px] leading-relaxed text-apex-text/85">
                  {decision.reason}
                </p>
              ) : null}
              <ExploreInsightList picks={decision.picks ?? []} />
            </LoopSection>
          ) : null}

          {experience.showSafety ? (
            <LoopSection
              title={experience.safetyTitle}
              delayMs={sectionIndex++ * 100}
            >
              <SafetyBlock decision={decision} />
            </LoopSection>
          ) : null}

          {hasPlan && plan?.behaviorNote && intent === "grow" ? (
            <LoopSection
              title={experience.mindsetTitle}
              delayMs={sectionIndex++ * 100}
            >
              <p className="text-[15px] leading-relaxed text-apex-text/85">
                {plan.behaviorNote}
              </p>
            </LoopSection>
          ) : null}

          {intent === "explore" ? (
            <LoopSection
              title={experience.mindsetTitle}
              delayMs={sectionIndex++ * 100}
            >
              <p className="text-[15px] leading-relaxed text-apex-text/85">
                Observation builds judgment. You do not need to act on every idea.
              </p>
            </LoopSection>
          ) : null}

          {intent === "protect" && !experience.showSafety ? (
            <LoopSection
              title={experience.mindsetTitle}
              delayMs={sectionIndex++ * 100}
            >
              <p className="text-[15px] leading-relaxed text-apex-text/85">
                Patience protects capital. Wait for clarity before deploying.
              </p>
            </LoopSection>
          ) : null}

          <LoopSection
            title={experience.trustTitle}
            delayMs={sectionIndex++ * 100}
          >
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
