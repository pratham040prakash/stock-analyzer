"use client";

import { useEffect, useState } from "react";
import { formatInr } from "@/lib/funds";
import {
  ApexBody,
  ApexButton,
} from "@/components/ui/apex";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import type { ExecutionPlanDecision } from "@/components/decision/ExecutionPlanCard";
import { buildExecutionPlanInput } from "@/services/execution/buildExecutionPlanInput";
import {
  generateExecutionPlanSafe,
  type ExecutionPlanConviction,
  type ExecutionPlanSafeOutput,
} from "@/services/execution/executionPlanEngine";

export type ExecutionPlanModalProps = {
  open: boolean;
  onClose: () => void;
  decision: ExecutionPlanDecision;
  entryTiming: EntryTimingState;
};

function convictionLabel(conviction: ExecutionPlanConviction): string {
  if (conviction === "strong") {
    return "Strong";
  }

  if (conviction === "moderate") {
    return "Moderate";
  }

  return "Weak";
}

function StepRow({ index, text }: { index: number; text: string }) {
  return (
    <li className="flex items-start gap-3">
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-apex-border bg-apex-bg text-[11px] font-semibold text-apex-muted">
        {index}
      </span>
      <span className="pt-0.5 text-[14px] leading-snug text-apex-text/90">
        {text}
      </span>
    </li>
  );
}

export default function ExecutionPlanModal({
  open,
  onClose,
  decision,
  entryTiming,
}: ExecutionPlanModalProps) {
  const [plan, setPlan] = useState<ExecutionPlanSafeOutput | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || decision.action !== "buy" || !decision.stock) {
      setPlan(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setPlan(null);

    void (async () => {
      const input = await buildExecutionPlanInput(decision, { entryTiming });

      if (cancelled) {
        return;
      }

      if (input) {
        setPlan(generateExecutionPlanSafe(input));
      }

      setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [open, decision, entryTiming]);

  if (!open || decision.action !== "buy" || !decision.stock) {
    return null;
  }

  const amount = decision.amount ?? 0;
  const amountLabel = amount > 0 ? formatInr(amount) : "your planned amount";
  const headline = entryTiming.enter
    ? `Invest ${amountLabel} in ${decision.stock}`
    : `Prepare to invest ${amountLabel} in ${decision.stock}`;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
      <button
        type="button"
        aria-label="Close execution plan"
        onClick={onClose}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="execution-plan-title"
        className="relative max-h-[85vh] w-full max-w-md overflow-y-auto rounded-2xl border border-apex-border/50 bg-apex-card p-6 shadow-2xl animate-apex-rise-in"
      >
        <h2
          id="execution-plan-title"
          className="text-lg font-semibold tracking-tight text-apex-text"
        >
          How to act today
        </h2>
        <p className="mt-1 text-[13px] text-apex-muted">{decision.stock}</p>
        <p className="mt-2 text-[15px] font-medium leading-snug text-apex-text">
          {headline}
        </p>

        <div
          className={[
            "mt-4 rounded-xl border px-4 py-3",
            entryTiming.enter
              ? "border-emerald-500/25 bg-emerald-500/10"
              : "border-amber-500/20 bg-amber-500/5",
          ].join(" ")}
        >
          <p
            className={[
              "text-[13px] font-medium",
              entryTiming.enter ? "text-emerald-300" : "text-amber-200",
            ].join(" ")}
          >
            {entryTiming.enter
              ? "Entry conditions confirmed — proceed with the plan"
              : "Waiting for confirmation before entry"}
          </p>
        </div>

        {plan?.behaviorNote ? (
          <section className="mt-6 rounded-xl border border-apex-border/40 bg-apex-bg/40 px-4 py-3.5">
            <p className="text-[12px] font-semibold uppercase tracking-wider text-apex-muted">
              Mindset for this trade
            </p>
            <p className="mt-2 text-[14px] leading-relaxed text-apex-text/90">
              {plan.behaviorNote}
            </p>
          </section>
        ) : null}

        <section className="mt-6">
          <p className="text-[13px] font-semibold text-apex-text">Your steps</p>
          {loading ? (
            <ApexBody className="mt-3">Building your plan…</ApexBody>
          ) : plan && plan.steps.length > 0 ? (
            <>
              <p className="mt-3 text-[12px] uppercase tracking-wider text-apex-muted">
                Entry:{" "}
                {plan.entryType === "aggressive" ? "Aggressive" : "Confirmed"}
                {" · "}
                Conviction: {convictionLabel(plan.conviction)}
                {plan.stopLoss !== null
                  ? ` · Stop ${formatInr(plan.stopLoss)}`
                  : null}
              </p>
              <ol className="mt-4 space-y-3">
                {plan.steps.map((step, index) => (
                  <StepRow key={step} index={index + 1} text={step} />
                ))}
              </ol>
            </>
          ) : (
            <ApexBody className="mt-3">
              Plan unavailable — check back after market data loads.
            </ApexBody>
          )}
        </section>

        {plan && plan.steps.length > 0 ? (
          <>
            <section className="mt-6 rounded-xl border border-apex-border/40 bg-apex-bg/40 px-4 py-3.5">
              <p className="text-[12px] font-semibold uppercase tracking-wider text-apex-muted">
                Risk
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-apex-text/85">
                {plan.riskNote}
              </p>
            </section>

            <section className="mt-3 rounded-xl border border-apex-border/40 bg-apex-bg/40 px-4 py-3.5">
              <p className="text-[12px] font-semibold uppercase tracking-wider text-apex-muted">
                Conviction
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-apex-text/85">
                {plan.confidenceNote}
              </p>
            </section>
          </>
        ) : null}

        <ApexButton className="mt-6 w-full" variant="secondary" onClick={onClose}>
          Done
        </ApexButton>
      </div>
    </div>
  );
}
