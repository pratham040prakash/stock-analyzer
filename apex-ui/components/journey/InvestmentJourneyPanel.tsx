"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { buildJourneyProgress } from "@/lib/journey/buildJourneyProgress";
import { JOURNEY_COPY } from "@/lib/journey/journeyCopy";
import {
  completeJourney,
  createJourney,
  getActiveJourneyForSymbol,
  pauseJourney,
} from "@/lib/journey/journeyStore";
import { formatInr } from "@/lib/funds";
import type { DailyVerdict } from "@/lib/dailyLoop/dailyVerdict";
import type {
  JourneyHorizon,
  JourneyProgressViewModel,
  StoredInvestmentJourney,
} from "@/types/investmentJourney";

export type InvestmentJourneyPanelProps = {
  symbol: string;
  currentPriceInr?: number | null;
  quantity?: number;
  dailyVerdict?: DailyVerdict;
  brokerStepCompleted?: boolean;
  compact?: boolean;
  className?: string;
};

function formatPrice(value: number): string {
  return formatInr(Math.round(value));
}

function addWeeks(from: Date, weeks: number): string {
  const next = new Date(from);
  next.setDate(next.getDate() + weeks * 7);
  return next.toISOString().slice(0, 10);
}

export default function InvestmentJourneyPanel({
  symbol,
  currentPriceInr,
  quantity,
  dailyVerdict,
  brokerStepCompleted = false,
  compact = false,
  className = "",
}: InvestmentJourneyPanelProps) {
  const [journey, setJourney] = useState<StoredInvestmentJourney | null>(null);
  const [showStartForm, setShowStartForm] = useState(false);
  const [horizon, setHorizon] = useState<JourneyHorizon>("swing");
  const [targetPrice, setTargetPrice] = useState("");
  const [entryPrice, setEntryPrice] = useState("");
  const [investedAmount, setInvestedAmount] = useState("");
  const [swingWeeks, setSwingWeeks] = useState("3");
  const [formError, setFormError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setJourney(getActiveJourneyForSymbol(symbol));
  }, [symbol]);

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    if (currentPriceInr && !entryPrice && showStartForm) {
      setEntryPrice(String(Math.round(currentPriceInr)));
    }
  }, [currentPriceInr, entryPrice, showStartForm]);

  const progress: JourneyProgressViewModel | null = useMemo(() => {
    if (!journey) {
      return null;
    }

    return buildJourneyProgress({
      journey,
      currentPriceInr,
      quantity,
      waitingForEntry: dailyVerdict === "wait" && !brokerStepCompleted,
      entryConfirmed: brokerStepCompleted || (quantity ?? 0) > 0,
    });
  }, [
    brokerStepCompleted,
    currentPriceInr,
    dailyVerdict,
    journey,
    quantity,
  ]);

  const handleStartJourney = () => {
    const target = Number(targetPrice);
    if (!Number.isFinite(target) || target <= 0) {
      setFormError("Enter a valid target price.");
      return;
    }

    const entry = entryPrice.trim() ? Number(entryPrice) : undefined;
    if (entry !== undefined && (!Number.isFinite(entry) || entry <= 0)) {
      setFormError("Entry price must be a positive number.");
      return;
    }

    const amount = investedAmount.trim() ? Number(investedAmount) : undefined;
    if (amount !== undefined && (!Number.isFinite(amount) || amount <= 0)) {
      setFormError("Amount must be a positive number.");
      return;
    }

    const weeks = horizon === "swing" ? Number(swingWeeks) : undefined;
    if (horizon === "swing" && (!weeks || weeks < 1 || weeks > 12)) {
      setFormError("Swing window should be 1–12 weeks.");
      return;
    }

    setFormError(null);
    const created = createJourney({
      symbol,
      horizon,
      targetPriceInr: Math.round(target),
      entryPriceInr: entry ? Math.round(entry) : undefined,
      investedAmountInr: amount ? Math.round(amount) : undefined,
      targetBy: horizon === "swing" ? addWeeks(new Date(), weeks ?? 3) : undefined,
    });

    setJourney(created);
    setShowStartForm(false);
  };

  if (!symbol.trim()) {
    return null;
  }

  if (!journey && !showStartForm) {
    return (
      <section
        className={`rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-4 ${className}`.trim()}
        aria-label="Investment journey"
      >
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-apex-muted">
          {JOURNEY_COPY.panelTitle}
        </p>
        <p className="mt-2 text-sm text-apex-text/85">{JOURNEY_COPY.startDescription}</p>
        <button
          type="button"
          onClick={() => setShowStartForm(true)}
          className="mt-3 text-sm font-medium text-blue-200/90 underline underline-offset-2 hover:text-blue-100"
        >
          {JOURNEY_COPY.startTitle} for {symbol}
        </button>
      </section>
    );
  }

  if (!journey && showStartForm) {
    return (
      <section
        className={`rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-4 ${className}`.trim()}
        aria-label="Start investment journey"
      >
        <p className="text-sm font-medium text-apex-text">{JOURNEY_COPY.startTitle}</p>
        <p className="mt-1 text-xs text-apex-muted/80">
          {symbol} · {JOURNEY_COPY.startDescription}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {(["swing", "long_term"] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setHorizon(value)}
              className={[
                "rounded-lg border px-3 py-2 text-left text-xs",
                horizon === value
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-100"
                  : "border-apex-border/20 text-apex-muted/80",
              ].join(" ")}
            >
              <span className="font-medium">
                {value === "swing"
                  ? JOURNEY_COPY.horizonSwing
                  : JOURNEY_COPY.horizonLongTerm}
              </span>
              <span className="mt-0.5 block text-[11px] opacity-80">
                {value === "swing"
                  ? JOURNEY_COPY.horizonSwingHint
                  : JOURNEY_COPY.horizonLongTermHint}
              </span>
            </button>
          ))}
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="text-xs text-apex-muted/80">
            {JOURNEY_COPY.targetLabel}
            <input
              type="number"
              inputMode="decimal"
              value={targetPrice}
              onChange={(event) => setTargetPrice(event.target.value)}
              className="mt-1 w-full rounded-lg border border-apex-border/25 bg-black/20 px-3 py-2 text-sm text-apex-text"
            />
          </label>
          <label className="text-xs text-apex-muted/80">
            {JOURNEY_COPY.entryLabel}
            <input
              type="number"
              inputMode="decimal"
              value={entryPrice}
              onChange={(event) => setEntryPrice(event.target.value)}
              className="mt-1 w-full rounded-lg border border-apex-border/25 bg-black/20 px-3 py-2 text-sm text-apex-text"
            />
          </label>
          <label className="text-xs text-apex-muted/80">
            {JOURNEY_COPY.amountLabel}
            <input
              type="number"
              inputMode="numeric"
              value={investedAmount}
              onChange={(event) => setInvestedAmount(event.target.value)}
              className="mt-1 w-full rounded-lg border border-apex-border/25 bg-black/20 px-3 py-2 text-sm text-apex-text"
            />
          </label>
          {horizon === "swing" ? (
            <label className="text-xs text-apex-muted/80">
              {JOURNEY_COPY.swingWeeksLabel}
              <input
                type="number"
                min={1}
                max={12}
                value={swingWeeks}
                onChange={(event) => setSwingWeeks(event.target.value)}
                className="mt-1 w-full rounded-lg border border-apex-border/25 bg-black/20 px-3 py-2 text-sm text-apex-text"
              />
            </label>
          ) : null}
        </div>

        {formError ? (
          <p className="mt-2 text-xs text-amber-200/90">{formError}</p>
        ) : null}

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleStartJourney}
            className="rounded-lg bg-emerald-600/80 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"
          >
            {JOURNEY_COPY.saveJourney}
          </button>
          <button
            type="button"
            onClick={() => setShowStartForm(false)}
            className="text-sm text-apex-muted/75 hover:text-apex-text"
          >
            Cancel
          </button>
        </div>
      </section>
    );
  }

  if (!progress) {
    return null;
  }

  return (
    <section
      className={`rounded-xl border border-violet-500/20 bg-violet-500/[0.06] px-4 py-4 ${className}`.trim()}
      aria-label="Investment journey progress"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.12em] text-violet-200/80">
            {JOURNEY_COPY.panelTitle}
          </p>
          <p className="mt-1 text-lg font-semibold tracking-tight text-apex-text">
            {progress.symbol}
            <span className="ml-2 text-sm font-normal text-apex-muted/75">
              · {progress.horizonLabel}
            </span>
          </p>
          <p className="mt-1 text-xs text-violet-100/75">{progress.milestoneLabel}</p>
        </div>
        <div className="text-right text-sm tabular-nums">
          <p className="text-2xl font-semibold text-apex-text">{progress.progressPct}%</p>
          <p className="text-xs text-apex-muted/75">{JOURNEY_COPY.progressLabel}</p>
        </div>
      </div>

      <div
        className="mt-3 h-2 overflow-hidden rounded-full bg-black/25"
        role="progressbar"
        aria-valuenow={progress.progressPct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-violet-400/80 to-emerald-400/80 transition-all"
          style={{ width: `${progress.progressPct}%` }}
        />
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-apex-text/80">
        <span>Target {formatPrice(progress.targetPriceInr)}</span>
        {progress.currentPriceInr !== null ? (
          <span>Now {formatPrice(progress.currentPriceInr)}</span>
        ) : null}
        {progress.priceRemainingInr !== null ? (
          <span>{formatPrice(progress.priceRemainingInr)} to go</span>
        ) : null}
        {progress.investedAmountInr !== null ? (
          <span>
            {JOURNEY_COPY.investedLabel} {formatPrice(progress.investedAmountInr)}
            {progress.currentValueInr !== null
              ? ` → ${formatPrice(progress.currentValueInr)}`
              : ""}
            {progress.gainPct !== null
              ? ` (${progress.gainPct >= 0 ? "+" : ""}${progress.gainPct}%)`
              : ""}
          </span>
        ) : null}
        <span>
          {JOURNEY_COPY.daysLabel} {progress.daysElapsed}
          {progress.daysRemaining !== null ? ` · ${progress.daysRemaining}d left` : ""}
        </span>
      </div>

      <p className="mt-3 text-sm leading-snug text-apex-text/90">{progress.guidance}</p>

      {!compact ? (
        <ol className="mt-4 space-y-2 border-t border-apex-border/10 pt-3">
          {progress.pathSteps.map((step) => (
            <li
              key={step.id}
              className={[
                "flex gap-3 text-xs",
                step.status === "current"
                  ? "text-apex-text"
                  : step.status === "done"
                    ? "text-emerald-200/80"
                    : "text-apex-muted/55",
              ].join(" ")}
            >
              <span className="mt-0.5 w-4 shrink-0 text-center">
                {step.status === "done" ? "✓" : step.status === "current" ? "→" : "·"}
              </span>
              <span>
                <span className="font-medium">{step.label}</span>
                <span className="mt-0.5 block text-[11px] opacity-85">{step.detail}</span>
              </span>
            </li>
          ))}
        </ol>
      ) : null}

      <p className="mt-3 text-[11px] text-apex-muted/60">{progress.disclaimer}</p>

      <div className="mt-3 flex flex-wrap gap-3 text-xs">
        {progress.targetReached ? (
          <button
            type="button"
            onClick={() => {
              completeJourney(progress.journey.id);
              reload();
            }}
            className="font-medium text-emerald-200/90 underline underline-offset-2"
          >
            {JOURNEY_COPY.completeJourney}
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => {
            pauseJourney(progress.journey.id);
            reload();
          }}
          className="text-apex-muted/70 underline underline-offset-2 hover:text-apex-text"
        >
          {JOURNEY_COPY.pauseJourney}
        </button>
      </div>
    </section>
  );
}
