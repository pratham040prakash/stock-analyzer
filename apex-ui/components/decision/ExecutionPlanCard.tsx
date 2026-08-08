"use client";

import { formatInr } from "@/lib/funds";
import {
  ApexBody,
  ApexCard,
  ApexEyebrow,
  ApexInsight,
  ApexRow,
  ApexSection,
  ApexTitle,
} from "@/components/ui/apex";

export type EntryTimingState = {
  enter: boolean;
  reason: string;
};

export type ExecutionPlanDecision = {
  action: string;
  stock?: string;
  confidence?: number;
  structureScore?: number;
  amount?: number;
  allocationPercent?: number;
  allocationReason?: string;
  confidenceMetrics?: {
    probability?: number;
    expectedReturn?: number;
    expectedDrawdown?: number;
    edgeScore?: number;
  };
};

export type ExecutionPlanCardProps = {
  decision: ExecutionPlanDecision;
  entryTiming: EntryTimingState;
  className?: string;
};

const EXECUTION_STEPS = [
  "Wait for breakout above recent high",
  "Confirm strong volume",
  "Enter position",
] as const;

function formatAllocationPercent(value?: number): string {
  if (value === undefined || !Number.isFinite(value)) {
    return "—";
  }

  const pct = value <= 1 ? value * 100 : value;
  return `${Math.round(pct)}%`;
}

function buildEdgeInsights(decision: ExecutionPlanDecision): string[] {
  const insights: string[] = [];
  const metrics = decision.confidenceMetrics;

  if ((decision.confidence ?? 0) >= 70 || (metrics?.probability ?? 0) >= 0.65) {
    insights.push("Strong trend alignment");
  }

  if ((metrics?.expectedReturn ?? 0) > 0) {
    insights.push("Positive expected return");
  }

  if ((decision.structureScore ?? 0) >= 55) {
    insights.push("Favorable market structure");
  }

  if (insights.length === 0) {
    return ["Worth watching as conditions develop"];
  }

  return insights.slice(0, 3);
}

function StepIndicator({ done }: { done: boolean }) {
  return (
    <span
      className={[
        "flex h-5 w-5 shrink-0 items-center justify-center rounded-md border text-[11px] font-semibold transition-colors duration-200",
        done
          ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
          : "border-apex-border bg-apex-bg text-apex-muted",
      ].join(" ")}
      aria-hidden
    >
      {done ? "✓" : ""}
    </span>
  );
}

export default function ExecutionPlanCard({
  decision,
  entryTiming,
  className = "",
}: ExecutionPlanCardProps) {
  if (decision.action !== "buy" || !decision.stock) {
    return null;
  }

  const amount = decision.amount ?? 0;
  const stock = decision.stock;
  const amountLabel = amount > 0 ? formatInr(amount) : "your planned amount";
  const heroPrefix = entryTiming.enter ? "Invest" : "Prepare to invest";
  const heroText = `${heroPrefix} ${amountLabel} in ${stock}`;
  const insights = buildEdgeInsights(decision);

  return (
    <div className={`mx-auto w-full max-w-[520px] ${className}`.trim()}>
      <ApexCard>
        <header className="mb-6">
          <ApexTitle className="text-lg">Execution Plan</ApexTitle>
          <ApexEyebrow className="mt-1">
            Apex recommendation for today
          </ApexEyebrow>
        </header>

        <section className="mb-5">
          <h2 className="text-[22px] font-bold leading-snug tracking-tight text-apex-text">
            {heroText}
          </h2>
          <ApexBody className="mt-2">
            Only enter when conditions are confirmed
          </ApexBody>
        </section>

        <section
          className={[
            "mb-5 rounded-xl border px-4 py-3.5",
            entryTiming.enter
              ? "border-emerald-500/25 bg-emerald-500/10"
              : "border-amber-500/20 bg-amber-500/5",
          ].join(" ")}
        >
          {entryTiming.enter ? (
            <>
              <p className="text-[14px] font-medium text-emerald-300">
                Entry conditions confirmed
              </p>
              <ApexBody className="mt-1 text-emerald-200/80">
                You can proceed
              </ApexBody>
            </>
          ) : (
            <>
              <p className="text-[14px] font-medium text-amber-200">
                Waiting for confirmation
              </p>
              <ApexBody className="mt-1 text-amber-100/70">
                Breakout + volume + momentum not aligned yet
              </ApexBody>
              {entryTiming.reason ? (
                <p className="mt-2 text-[12px] text-apex-muted">
                  {entryTiming.reason}
                </p>
              ) : null}
            </>
          )}
        </section>

        <ApexSection className="mb-5">
          <ApexEyebrow className="mb-3 uppercase tracking-wider">
            Your steps
          </ApexEyebrow>
          <ul className="space-y-2.5">
            {EXECUTION_STEPS.map((step, index) => (
              <li key={step} className="flex items-start gap-3">
                <StepIndicator done={entryTiming.enter} />
                <span className="pt-0.5 text-[13px] leading-snug text-apex-text/90">
                  <span className="mr-1.5 text-apex-muted">{index + 1}.</span>
                  {step}
                </span>
              </li>
            ))}
          </ul>
        </ApexSection>

        <ApexSection className="mb-5 divide-y rounded-xl border border-apex-border px-4">
          <ApexRow
            label="Investment"
            value={amount > 0 ? formatInr(amount) : "—"}
          />
          <ApexRow
            label="Portfolio Allocation"
            value={formatAllocationPercent(decision.allocationPercent)}
          />
          <ApexRow
            label="Strategy"
            value={decision.allocationReason ?? "Guided allocation"}
          />
        </ApexSection>

        <section className="mb-5 rounded-xl border border-apex-border bg-apex-bg/60 px-4 py-3.5">
          <p className="text-[13px] font-semibold text-apex-text">
            Risk Protection
          </p>
          <ul className="mt-2.5 space-y-2 text-[13px] leading-relaxed text-apex-muted">
            <li>Stop loss: ~5% below entry</li>
            <li>Position capped to protect capital</li>
            <li>Daily loss limits enforced</li>
          </ul>
        </section>

        <ApexInsight title="Why this opportunity?">
          <ul className="space-y-2">
            {insights.map((insight) => (
              <li
                key={insight}
                className="flex gap-2 text-[13px] text-blue-100/75"
              >
                <span className="text-blue-400/90">•</span>
                {insight}
              </li>
            ))}
          </ul>
        </ApexInsight>
      </ApexCard>
    </div>
  );
}
