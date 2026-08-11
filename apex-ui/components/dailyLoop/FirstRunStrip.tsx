"use client";

import type { FirstRunProgress } from "@/lib/onboarding/firstRun";

type Props = {
  progress: FirstRunProgress;
  userName?: string;
};

function StepIndicator({ status }: { status: FirstRunProgress["steps"][number]["status"] }) {
  if (status === "done") {
    return (
      <span
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-[11px] font-semibold text-emerald-200/95"
        aria-hidden
      >
        ✓
      </span>
    );
  }

  if (status === "current") {
    return (
      <span
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-apex-border/40 bg-white/[0.06] text-[11px] font-semibold text-apex-text"
        aria-hidden
      >
        •
      </span>
    );
  }

  return (
    <span
      className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-apex-border/20 text-[11px] text-apex-muted/50"
      aria-hidden
    >
      ·
    </span>
  );
}

export default function FirstRunStrip({ progress, userName }: Props) {
  if (progress.complete) {
    return null;
  }

  const greeting = userName ? `Hi ${userName}` : "Welcome";

  return (
    <section
      className="rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-4"
      aria-label="First-run setup progress"
    >
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
          {progress.headline}
        </p>
        <p className="text-sm text-apex-text/85">
          {greeting} — {progress.steps.length} quick steps before your first capital decision.
        </p>
      </div>

      <ol className="mt-4 space-y-3">
        {progress.steps.map((step) => (
          <li key={step.id} className="flex gap-3">
            <StepIndicator status={step.status} />
            <div className="min-w-0">
              <p
                className={[
                  "text-sm font-medium",
                  step.status === "pending"
                    ? "text-apex-muted/70"
                    : "text-apex-text/90",
                ].join(" ")}
              >
                {step.label}
              </p>
              <p className="mt-0.5 text-xs leading-snug text-apex-muted/75">
                {step.detail}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
