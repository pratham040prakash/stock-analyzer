"use client";

import type { DailyVerdict } from "@/lib/dailyLoop/dailyVerdict";
import { OPERATING_MANUAL } from "@/lib/dailyLoop/operatingManualCopy";
import type { TodayExecutionKind } from "@/lib/dailyLoop/todaySurface";
import type { ConnectionStatus } from "@/lib/broker/zerodha";

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
  hideSetupConfidence?: boolean;
  compactWaitCopy?: boolean;
  chipLabel?: string;
  hideChip?: boolean;
  desk?: boolean;
};

const VERDICT_THEME: Record<
  DailyVerdict,
  { word: string; glow: string; wash: string; chip: string }
> = {
  wait: {
    word: "text-white",
    glow: "bg-[radial-gradient(circle_at_50%_0%,rgba(148,163,184,0.22),transparent_58%)]",
    wash: "from-slate-400/[0.08]",
    chip: "border-white/10 bg-white/[0.06] text-slate-200",
  },
  trade: {
    word: "text-emerald-200",
    glow: "bg-[radial-gradient(circle_at_50%_0%,rgba(52,211,153,0.24),transparent_58%)]",
    wash: "from-emerald-400/[0.12]",
    chip: "border-emerald-400/20 bg-emerald-400/10 text-emerald-100",
  },
  pause: {
    word: "text-amber-200",
    glow: "bg-[radial-gradient(circle_at_50%_0%,rgba(251,191,36,0.22),transparent_58%)]",
    wash: "from-amber-400/[0.12]",
    chip: "border-amber-400/20 bg-amber-400/10 text-amber-100",
  },
};

export default function VerdictCanvas({
  verdictWord,
  dailyVerdict,
  headline,
  subline,
  portfolioStale = false,
  pollError = null,
  connectionStatus = "NOT_CONNECTED",
  brokerStepCompleted = false,
  brokerStepSkipped = false,
  doneForToday = false,
  hideStaleRibbon = false,
  compactWaitCopy = false,
  chipLabel,
  hideChip = false,
  desk = false,
}: VerdictCanvasProps) {
  const theme = VERDICT_THEME[dailyVerdict];
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
      className={`relative overflow-hidden rounded-[28px] border border-white/[0.08] bg-gradient-to-b ${theme.wash} to-transparent px-5 py-7 sm:px-8 sm:py-9`}
    >
      <div className={`pointer-events-none absolute inset-0 ${theme.glow}`} />

      {showStaleRibbon ? (
        <div className="relative mb-5 rounded-2xl border border-amber-500/25 bg-amber-500/10 px-3 py-2">
          <p className="text-xs font-medium text-amber-100/90">Live data stale</p>
          <p className="text-xs text-amber-100/70">{staleDetail}</p>
        </div>
      ) : null}

      <div className="relative text-center">
        <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-apex-muted/70">
          {desk ? "Today · live" : "Today"}
        </p>
        <p
          className={
            desk
              ? `mt-4 text-[13px] font-semibold uppercase tracking-[0.42em] ${theme.word}`
              : `mt-3 text-6xl font-semibold tracking-tight sm:text-7xl ${theme.word}`
          }
        >
          {verdictWord}
        </p>
        {hideChip ? null : (
          <p
            className={`mx-auto mt-3 inline-flex rounded-full border px-3 py-1 text-[11px] font-medium ${theme.chip}`}
          >
            {chipLabel ??
              (dailyVerdict === "wait"
                ? "Doing nothing is the plan"
                : dailyVerdict === "pause"
                  ? "Capital stays protected"
                  : "One action in Kite")}
          </p>
        )}
      </div>

      <div className="relative mx-auto mt-6 max-w-[28rem] space-y-2 text-center">
        <h2
          className={
            desk
              ? "text-3xl font-semibold leading-tight tracking-tight text-white sm:text-4xl"
              : "text-xl font-semibold leading-snug text-apex-text sm:text-2xl"
          }
        >
          {headline}
        </h2>
        {!compactWaitCopy && subline ? (
          <p className="text-[15px] leading-relaxed text-apex-muted/90">{subline}</p>
        ) : null}
        {brokerStepCompleted ? (
          <p className="text-xs font-medium text-emerald-200/85">
            Broker step logged for today.
          </p>
        ) : null}
        {brokerStepSkipped ? (
          <p className="text-xs font-medium text-apex-text/75">
            Trim skipped — holding the position today.
          </p>
        ) : null}
      </div>

      {doneForToday ? (
        <div className="relative mx-auto mt-7 max-w-[22rem] rounded-2xl border border-white/[0.08] bg-black/20 px-4 py-4 text-center">
          <p className="text-sm font-medium text-apex-text">You&apos;re done for today</p>
          <p className="mt-1 text-xs leading-relaxed text-apex-muted/70">
            {OPERATING_MANUAL.verdictDone}
          </p>
        </div>
      ) : null}
    </section>
  );
}
