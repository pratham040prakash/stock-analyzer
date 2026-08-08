import type { ReactNode } from "react";
import LandingSection from "./LandingSection";

function MockBadge({
  children,
  tone,
}: {
  children: ReactNode;
  tone: "waiting" | "success";
}) {
  const toneClass =
    tone === "success"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
      : "border-amber-500/30 bg-amber-500/10 text-amber-200";

  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${toneClass}`}
    >
      {children}
    </span>
  );
}

function MockDecisionScreen() {
  return (
    <div className="rounded-2xl border border-apex-border bg-apex-card p-5 shadow-[0_24px_80px_rgba(0,0,0,0.32)] sm:p-6">
      <MockBadge tone="waiting">Waiting</MockBadge>

      <p className="mt-5 text-[20px] font-bold leading-snug tracking-tight text-apex-text">
        Prepare to invest ₹25,000 in RELIANCE
      </p>
      <p className="mt-2 text-[13px] leading-relaxed text-apex-muted">
        Conditions are not ready yet — wait for confirmation
      </p>

      <div className="mt-5 rounded-xl border border-blue-500/20 bg-blue-500/[0.06] px-4 py-3.5">
        <p className="text-[13px] font-semibold text-blue-200">
          Why this decision?
        </p>
        <ul className="mt-2 space-y-1.5 text-[12px] text-blue-100/75">
          <li>• Strong trend</li>
          <li>• Good market structure</li>
        </ul>
      </div>

      <div className="mt-5 space-y-2 rounded-xl border border-apex-border px-4 py-1">
        <div className="flex justify-between py-2.5 text-[12px]">
          <span className="text-apex-muted">Portfolio</span>
          <span className="font-medium text-apex-text">₹8,42,000</span>
        </div>
        <div className="flex justify-between border-t border-apex-border py-2.5 text-[12px]">
          <span className="text-apex-muted">Cash</span>
          <span className="font-medium text-apex-text">₹1,20,000</span>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-apex-border bg-apex-bg px-4 py-3.5 text-center text-[13px] font-semibold text-apex-text">
        View Execution Plan
      </div>
    </div>
  );
}

function MockExecutionPlan() {
  return (
    <div className="rounded-2xl border border-apex-border bg-apex-card p-5 shadow-[0_24px_80px_rgba(0,0,0,0.32)] sm:p-6">
      <p className="text-[13px] font-medium text-apex-muted">Execution Plan</p>
      <p className="mt-1 text-[18px] font-bold text-apex-text">
        Invest ₹25,000 in RELIANCE
      </p>

      <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
        <p className="text-[13px] font-medium text-amber-200">
          Waiting for confirmation
        </p>
        <p className="mt-1 text-[12px] text-apex-muted">
          Enter only when conditions align
        </p>
      </div>

      <div className="mt-4 space-y-2">
        {["Wait for breakout", "Confirm volume", "Enter position"].map(
          (step, index) => (
            <div key={step} className="flex items-center gap-3 text-[12px]">
              <span className="flex h-5 w-5 items-center justify-center rounded-md border border-apex-border bg-apex-bg text-apex-muted">
                {index + 1}
              </span>
              <span className="text-apex-text/90">{step}</span>
            </div>
          ),
        )}
      </div>

      <div className="mt-4 rounded-xl border border-apex-border bg-apex-bg/60 px-4 py-3">
        <p className="text-[12px] font-semibold text-apex-text">
          Risk Protection
        </p>
        <p className="mt-1 text-[11px] text-apex-muted">
          Stop loss · Position caps · Daily limits
        </p>
      </div>
    </div>
  );
}

export default function LandingProductPreview() {
  return (
    <LandingSection className="py-16 sm:py-20">
      <div className="max-w-[640px]">
        <h2 className="text-[24px] font-bold tracking-tight text-apex-text sm:text-[28px]">
          One screen. One decision.
        </h2>
        <p className="mt-3 text-[15px] leading-relaxed text-apex-muted">
          Your daily guidance — calm, clear, and actionable.
        </p>
      </div>

      <div className="mt-10 grid gap-6 lg:grid-cols-2 lg:gap-8">
        <div>
          <p className="mb-3 text-[12px] font-medium uppercase tracking-wider text-apex-muted">
            Today&apos;s decision
          </p>
          <MockDecisionScreen />
        </div>
        <div>
          <p className="mb-3 text-[12px] font-medium uppercase tracking-wider text-apex-muted">
            Execution plan
          </p>
          <MockExecutionPlan />
        </div>
      </div>
    </LandingSection>
  );
}
