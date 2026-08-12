"use client";

import type { DailyVerdict } from "@/lib/dailyLoop/dailyVerdict";
import { OPERATING_MANUAL } from "@/lib/dailyLoop/operatingManualCopy";
import type { TodayExecutionKind } from "@/lib/dailyLoop/todaySurface";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { ApexButton } from "@/components/ui/apex";

export type VerdictCanvasProps = {
  verdictWord: string;
  dailyVerdict: DailyVerdict;
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
  brokerStepSkipped?: boolean;
  doneForToday?: boolean;
  ctaLabel?: string;
  tradingLocked?: boolean;
  hideStaleRibbon?: boolean;
  suppressTrustScore?: boolean;
  trustFootnote?: string;
};

function resolveVerdictTone(
  dailyVerdict: DailyVerdict,
  executionKind: TodayExecutionKind,
): string {
  if (dailyVerdict === "pause") {
    return "text-amber-200";
  }

  if (dailyVerdict === "wait") {
    return "text-apex-text";
  }

  switch (executionKind) {
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
  dailyVerdict,
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
  brokerStepSkipped = false,
  doneForToday = false,
  ctaLabel = "You're done for today",
  tradingLocked = false,
  hideStaleRibbon = false,
  suppressTrustScore = false,
  trustFootnote,
}: VerdictCanvasProps) {
  const showStaleRibbon =
    !hideStaleRibbon &&
    (portfolioStale ||
      Boolean(pollError) ||
      connectionStatus === "TOKEN_EXPIRED");
  const staleDetail =
    connectionStatus === "TOKEN_EXPIRED"
      ? "Reconnect Zerodha to refresh live data."
      : pollError ?? "Portfolio data may be stale.";

  return (
    <section
      aria-label="Today's verdict"
      className="relative overflow-hidden rounded-2xl border border-apex-border/20 bg-gradient-to-b from-white/[0.04] to-transparent px-4 py-4 sm:px-5 sm:py-5"
    >
      {showStaleRibbon ? (
        <div className="mb-3 rounded-lg border border-amber-500/25 bg-amber-500/10 px-3 py-2">
          <p className="text-xs font-medium text-amber-100/90">Live data stale</p>
          <p className="text-xs text-amber-100/70">{staleDetail}</p>
        </div>
      ) : null}

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <p className="text-xs font-medium tracking-[0.04em] text-apex-muted/70">
            Today&apos;s decision
          </p>
          <p
            className={`text-3xl font-semibold tracking-tight sm:text-4xl ${resolveVerdictTone(dailyVerdict, executionKind)}`}
          >
            {verdictWord}
          </p>
        </div>

        <div className="rounded-xl border border-apex-border/15 bg-white/[0.03] px-3 py-2 text-right">
          <p className="text-[11px] uppercase tracking-wide text-apex-muted/70">
            {suppressTrustScore ? "Discipline" : "Trust"}
          </p>
          {suppressTrustScore ? (
            <p className="text-sm font-medium text-apex-text/85">Following plan</p>
          ) : (
            <p className="text-lg font-semibold text-apex-text">
              {trustScore}{" "}
              <span className="text-sm font-normal text-apex-muted/80">
                <TrustDelta delta={trustDelta} />
              </span>
            </p>
          )}
          {trustFootnote ? (
            <p className="mt-1 max-w-[12rem] text-[11px] text-apex-muted/75">
              {trustFootnote}
            </p>
          ) : trustMessage ? (
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
            <span className="font-medium text-apex-muted/85">Why · </span>
            {evidenceTeaser}
          </p>
        ) : null}
        {typeof confidence === "number" ? (
          <p className="text-xs text-apex-muted/60">
            Setup confidence {Math.round(confidence)}%
          </p>
        ) : null}
        {brokerStepCompleted ? (
          <p className="text-xs font-medium text-emerald-200/85">
            Broker step logged for today.
          </p>
        ) : null}
        {brokerStepSkipped ? (
          <p className="text-xs font-medium text-apex-text/75">
            Trim skipped — holding position today.
          </p>
        ) : null}
        {dailyVerdict === "pause" ? (
          <p className="text-xs text-amber-100/80">
            Capital protection mode — tactical trades are locked.
          </p>
        ) : null}
        {tradingLocked && dailyVerdict === "wait" ? (
          <p className="text-xs text-apex-muted/70">
            Long-term holdings do not need action today.
          </p>
        ) : null}
      </div>

      {doneForToday ? (
        <div className="mt-5">
          <ApexButton variant="secondary" className="w-full" disabled>
            {ctaLabel}
          </ApexButton>
          <p className="mt-2 text-center text-[11px] text-apex-muted/60">
            {OPERATING_MANUAL.verdictDone}
          </p>
        </div>
      ) : null}
    </section>
  );
}
