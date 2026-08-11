"use client";

import Link from "next/link";
import type { ResearchVerdict } from "@/types/researchSummary";

type Props = {
  symbol: string;
  verdict: ResearchVerdict;
  headline?: string;
  onDismiss: () => void;
};

function verdictLabel(verdict: ResearchVerdict): string {
  switch (verdict) {
    case "YES":
      return "Buy context";
    case "NO":
      return "Pass context";
    default:
      return "Wait context";
  }
}

export default function ResearchTodayHandoff({
  symbol,
  verdict,
  headline,
  onDismiss,
}: Props) {
  return (
    <section
      aria-label="Research handoff"
      className="rounded-xl border border-blue-500/20 bg-blue-500/5 px-4 py-4 space-y-2"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-blue-100/70">
            Research → Today
          </p>
          <p className="text-sm font-semibold text-apex-text/95">
            {verdictLabel(verdict)} · {symbol}
          </p>
          {headline ? (
            <p className="mt-1 text-sm text-apex-muted/85">{headline}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="text-xs text-apex-muted transition-colors hover:text-apex-text"
        >
          Dismiss
        </button>
      </div>
      <div className="flex flex-wrap gap-3 text-xs">
        <Link
          href={`/app/research?symbol=${encodeURIComponent(symbol)}`}
          className="text-blue-200/90 transition-colors hover:text-blue-100"
        >
          Back to research →
        </Link>
      </div>
    </section>
  );
}
