"use client";

import type { TodayExecutionKind } from "@/lib/dailyLoop/todaySurface";
import { resolveVerdictWord } from "@/lib/dailyLoop/todaySurface";
import type { ConnectionStatus } from "@/lib/broker/zerodha";

export type VerdictCanvasProps = {
  verdictWord: string;
  headline: string;
  subline: string;
  executionKind: TodayExecutionKind;
  trustScore: number;
  trustDelta: number;
  trustMessage?: string;
  evidenceTeaser?: string;
  confidence?: number;
  portfolioStale?: boolean;
  pollError?: string | null;
  connectionStatus?: ConnectionStatus;
  brokerStepCompleted?: boolean;
};

function resolveVerdictTone(kind: TodayExecutionKind): string {
  switch (kind) {
    case "BUY":
      return "text-emerald-200";
    case "SELL":
      return "text-amber-200";
    case "OBSERVE":
      return "text-blue-200";
    default:
      return "text-apex-text";
  }
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

export default function VerdictCanvas({
  verdictWord,
  headline,
  subline,
  executionKind,
  trustScore,
  trustDelta,
  trustMessage,
  evidenceTeaser,
  confidence,
  portfolioStale = false,
  pollError = null,
  connectionStatus = "NOT_CONNECTED",
  brokerStepCompleted = false,
}: VerdictCanvasProps) {
  const showStaleRibbon =
    portfolioStale ||
    Boolean(pollError) ||
    connectionStatus === "TOKEN_EXPIRED";
  const staleDetail =
    connectionStatus === "TOKEN_EXPIRED"
      ? "Reconnect Zerodha to refresh live data."
      : pollError ?? "Portfolio data may be stale.";

  return (
    <section
      aria-label="Today's verdict"
      className="relative overflow-hidden rounded-2xl border border-apex-border/20 bg-gradient-to-b from-white/[0.04] to-transparent px-5 py-5"
    >
      {showStaleRibbon ? (
        <div className="mb-3 rounded-lg border border-amber-500/25 bg-amber-500/10 px-3 py-2">
          <p className="text-xs font-medium text-amber-100/90">Live data stale</p>
          <p className="text-xs text-amber-100/70">{staleDetail}</p>
        </div>
      ) : null}

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-apex-muted/70">
            Morning brief
          </p>
          <p
            className={`text-4xl font-bold tracking-tight ${resolveVerdictTone(executionKind)}`}
          >
            {verdictWord}
          </p>
        </div>

        <div className="rounded-xl border border-apex-border/15 bg-white/[0.03] px-3 py-2 text-right">
          <p className="text-[11px] uppercase tracking-wide text-apex-muted/70">
            Trust
          </p>
          <p className="text-lg font-semibold text-apex-text">
            {trustScore}{" "}
            <span className="text-sm font-normal text-apex-muted/80">
              <TrustDelta delta={trustDelta} />
            </span>
          </p>
          {trustMessage ? (
            <p className="mt-1 max-w-[12rem] text-[11px] text-apex-muted/75">
              {trustMessage}
            </p>
          ) : null}
        </div>
      </div>

      <div className="mt-4 space-y-2">
        <h2 className="text-xl font-semibold leading-snug text-apex-text">
          {headline}
        </h2>
        <p className="text-sm text-apex-muted/85">{subline}</p>
        {evidenceTeaser ? (
          <p className="text-xs text-apex-muted/70">
            <span className="font-medium text-apex-muted/85">Evidence · </span>
            {evidenceTeaser}
          </p>
        ) : null}
        {typeof confidence === "number" ? (
          <p className="text-xs text-apex-muted/60">
            Confidence {Math.round(confidence)}%
          </p>
        ) : null}
        {brokerStepCompleted ? (
          <p className="text-xs font-medium text-emerald-200/85">
            Broker step logged for today.
          </p>
        ) : null}
      </div>
    </section>
  );
}

export { resolveVerdictWord };
