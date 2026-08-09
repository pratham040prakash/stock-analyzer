"use client";

import {
  MARGIN_LEVERAGE_WARNING,
  type CapitalFundingMode,
  writeStoredCapitalMode,
} from "@/lib/dailyLoop/capitalMargin";

type Props = {
  mode: CapitalFundingMode;
  onModeChange: (mode: CapitalFundingMode) => void;
  collateral?: number;
};

export default function CapitalModeToggle({
  mode,
  onModeChange,
  collateral = 0,
}: Props) {
  const setMode = (next: CapitalFundingMode) => {
    writeStoredCapitalMode(next);
    onModeChange(next);
  };

  return (
    <div className="rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-apex-muted">
            Capital mode
          </p>
          <p className="mt-1 text-sm text-apex-text/80">
            {mode === "MARGIN"
              ? "Cash + collateral deployable with strict limits"
              : "Cash only — no leverage"}
          </p>
        </div>
        <div
          className="inline-flex rounded-lg border border-apex-border/25 p-0.5"
          role="group"
          aria-label="Capital funding mode"
        >
          <button
            type="button"
            onClick={() => setMode("CASH")}
            className={[
              "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
              mode === "CASH"
                ? "bg-white/10 text-apex-text"
                : "text-apex-muted hover:text-apex-text/80",
            ].join(" ")}
          >
            Cash
          </button>
          <button
            type="button"
            onClick={() => setMode("MARGIN")}
            className={[
              "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
              mode === "MARGIN"
                ? "bg-amber-500/15 text-amber-100"
                : "text-apex-muted hover:text-apex-text/80",
            ].join(" ")}
          >
            Margin
          </button>
        </div>
      </div>
      {mode === "MARGIN" ? (
        <p className="mt-2 text-xs text-amber-200/85">
          {MARGIN_LEVERAGE_WARNING}
          {collateral > 0
            ? ` Collateral available: ₹${Math.round(collateral).toLocaleString("en-IN")}.`
            : null}
        </p>
      ) : null}
    </div>
  );
}
