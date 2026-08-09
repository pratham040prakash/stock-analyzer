"use client";

import type { OutcomeEvaluationOutput } from "@/services/learning/outcomeEngine";

type Props = {
  lastOutcome: OutcomeEvaluationOutput;
  lastOutcomeStock?: string | null;
  compact?: boolean;
  className?: string;
};

function formatOutcome(outcome: OutcomeEvaluationOutput["outcome"]): string {
  if (outcome === "win") {
    return "Win";
  }

  if (outcome === "loss") {
    return "Loss";
  }

  return "Breakeven";
}

export default function LastClosedTrustBlock({
  lastOutcome,
  lastOutcomeStock,
  compact = false,
  className = "",
}: Props) {
  return (
    <section
      className={[
        compact
          ? "mt-4 space-y-2 rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3"
          : "mt-6 space-y-3 animate-apex-fade-in opacity-90",
        className,
      ].join(" ")}
      aria-label="Last closed trade trust outcome"
    >
      {lastOutcomeStock ? (
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          Last closed · {lastOutcomeStock}
        </p>
      ) : null}

      <div
        className={
          compact
            ? "flex flex-wrap gap-x-4 gap-y-1 text-xs text-apex-muted"
            : "grid grid-cols-3 gap-3 text-xs text-apex-muted"
        }
      >
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

      <p
        className={
          compact
            ? "text-sm leading-snug text-apex-text/75"
            : "text-sm leading-relaxed text-apex-text/75"
        }
      >
        {lastOutcome.summary}
      </p>
    </section>
  );
}
