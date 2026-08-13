"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import JourneyPatienceCallout from "@/components/journey/JourneyPatienceCallout";
import JourneyTargetTrack from "@/components/journey/JourneyTargetTrack";
import JourneyTimeTargetPicker from "@/components/journey/JourneyTimeTargetPicker";
import { apiFetchJson } from "@/lib/api/clientFetch";
import { buildJourneyProgress } from "@/lib/journey/buildJourneyProgress";
import { isValidJourneyPlan } from "@/lib/journey/journeyPlanSanitize";
import type { ChartBackedJourneyPlan } from "@/lib/journey/buildChartBackedJourneyPlan";
import { JOURNEY_COPY } from "@/lib/journey/journeyCopy";
import { formatTimeTargetLabel, suggestTimeTarget } from "@/lib/journey/journeyTimeTarget";
import {
  createJourney,
  getActiveJourneyForSymbol,
} from "@/lib/journey/journeyStore";
import {
  persistJourneyToServer,
  syncJourneyForSymbol,
  updateJourneyStatusOnServer,
} from "@/lib/journey/journeySync";
import { fetchJourneySymbolLivePrice } from "@/lib/journey/journeyWatchLtp";
import type { DailyVerdict } from "@/lib/dailyLoop/dailyVerdict";
import type {
  JourneyHorizon,
  JourneyProgressViewModel,
  JourneyTimeUnit,
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
  /** Hide chart path when portfolio sync is stale — targets need fresh context. */
  portfolioDataStale?: boolean;
  /** When true, panel loads chart backtrace and offers APEX path — not manual guesswork. */
  apexSuggested?: boolean;
  preferSwing?: boolean;
  activationLevelInr?: number;
  onTakeProfit?: (symbol: string) => void;
};

const INFOGRAPHIC_CARD =
  "rounded-xl border border-apex-border/25 bg-[#0a0d12]/90 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]";

function previewProgressPct(
  entry: number,
  target: number,
  current: number | null | undefined,
): number {
  if (current === null || current === undefined || !Number.isFinite(current)) {
    return 0;
  }

  if (target === entry) {
    return 0;
  }

  const raw = ((current - entry) / (target - entry)) * 100;
  return Math.max(0, Math.min(100, Math.round(raw)));
}

type PlanResponse =
  | { status: "ok"; plan: ChartBackedJourneyPlan }
  | { status: "insufficient_data"; message?: string };

export default function InvestmentJourneyPanel({
  symbol,
  currentPriceInr,
  quantity,
  dailyVerdict,
  brokerStepCompleted = false,
  compact = false,
  className = "",
  portfolioDataStale = false,
  apexSuggested = false,
  preferSwing = false,
  activationLevelInr,
  onTakeProfit,
}: InvestmentJourneyPanelProps) {
  const [journey, setJourney] = useState<StoredInvestmentJourney | null>(null);
  const [chartPlan, setChartPlan] = useState<ChartBackedJourneyPlan | null>(null);
  const [planState, setPlanState] = useState<
    "idle" | "loading" | "ready" | "insufficient"
  >("idle");
  const [showStartForm, setShowStartForm] = useState(false);
  const [horizon, setHorizon] = useState<JourneyHorizon>("swing");
  const [targetPrice, setTargetPrice] = useState("");
  const [entryPrice, setEntryPrice] = useState("");
  const [investedAmount, setInvestedAmount] = useState("");
  const [timeAmount, setTimeAmount] = useState(4);
  const [timeUnit, setTimeUnit] = useState<JourneyTimeUnit>("weeks");
  const [formError, setFormError] = useState<string | null>(null);
  const [fetchedLivePrice, setFetchedLivePrice] = useState<number | null>(null);

  const effectiveLivePrice = useMemo(() => {
    if (
      currentPriceInr !== null &&
      currentPriceInr !== undefined &&
      Number.isFinite(currentPriceInr) &&
      currentPriceInr > 0
    ) {
      return currentPriceInr;
    }

    return fetchedLivePrice;
  }, [currentPriceInr, fetchedLivePrice]);

  const planStartIso = useMemo(
    () => new Date().toISOString().slice(0, 10),
    [],
  );

  const reload = useCallback(async () => {
    const synced = await syncJourneyForSymbol(symbol);
    setJourney(synced ?? getActiveJourneyForSymbol(symbol));
  }, [symbol]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (
      currentPriceInr !== null &&
      currentPriceInr !== undefined &&
      Number.isFinite(currentPriceInr) &&
      currentPriceInr > 0
    ) {
      setFetchedLivePrice(null);
      return;
    }

    if (!symbol.trim()) {
      return;
    }

    let cancelled = false;
    const entryHint =
      chartPlan?.entryPriceInr ??
      journey?.entryPriceInr ??
      (entryPrice.trim() ? Number(entryPrice) : undefined);

    void fetchJourneySymbolLivePrice(
      symbol,
      Number.isFinite(entryHint) ? entryHint : undefined,
    ).then((price) => {
      if (!cancelled) {
        setFetchedLivePrice(price);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [
    chartPlan?.entryPriceInr,
    currentPriceInr,
    entryPrice,
    journey?.entryPriceInr,
    symbol,
  ]);

  useEffect(() => {
    if (journey || !apexSuggested || !symbol.trim()) {
      return;
    }

    let cancelled = false;

    async function loadPlan() {
      setPlanState("loading");
      const params = new URLSearchParams({ symbol: symbol.trim().toUpperCase() });
      if (preferSwing) {
        params.set("preferSwing", "1");
      }
      if (activationLevelInr && activationLevelInr > 0) {
        params.set("activationLevel", String(Math.round(activationLevelInr)));
      }

      try {
        const { data } = await apiFetchJson<PlanResponse>(
          `/api/journey/plan?${params.toString()}`,
          { cache: "no-store" },
        );

        if (cancelled || !data) {
          if (!cancelled && !data) {
            setChartPlan(null);
            setPlanState("insufficient");
          }
          return;
        }

        if (data.status === "ok" && "plan" in data && data.plan) {
          setChartPlan(data.plan);
          setPlanState("ready");
          setHorizon(data.plan.horizon);
          setTargetPrice(String(data.plan.targetPriceInr));
          setEntryPrice(String(data.plan.entryPriceInr));
          setTimeAmount(data.plan.suggestedTime.amount);
          setTimeUnit(data.plan.suggestedTime.unit);
          return;
        }

        setChartPlan(null);
        setPlanState("insufficient");
      } catch {
        if (!cancelled) {
          setChartPlan(null);
          setPlanState("insufficient");
        }
      }
    }

    void loadPlan();

    return () => {
      cancelled = true;
    };
  }, [activationLevelInr, apexSuggested, journey, preferSwing, symbol]);

  const progress: JourneyProgressViewModel | null = useMemo(() => {
    if (!journey) {
      return null;
    }

    return buildJourneyProgress({
      journey,
      currentPriceInr: effectiveLivePrice,
      quantity,
      waitingForEntry: dailyVerdict === "wait" && !brokerStepCompleted,
      entryConfirmed: brokerStepCompleted || (quantity ?? 0) > 0,
    });
  }, [
    brokerStepCompleted,
    dailyVerdict,
    effectiveLivePrice,
    journey,
    quantity,
  ]);

  const commitChartPlan = async () => {
    if (!chartPlan) {
      return;
    }

    const created = createJourney({
      symbol: chartPlan.symbol,
      horizon: chartPlan.horizon,
      targetPriceInr: chartPlan.targetPriceInr,
      entryPriceInr: chartPlan.entryPriceInr,
      targetDurationAmount: timeAmount,
      targetDurationUnit: timeUnit,
      suggestedByApex: true,
      chartBasis: {
        lookbackDays: chartPlan.lookbackDays,
        supportLevelInr: chartPlan.supportLevelInr ?? undefined,
        resistanceLevelInr: chartPlan.resistanceLevelInr ?? undefined,
        backtraceSummary: chartPlan.backtraceSummary,
        structureScore: chartPlan.structureScore,
        suggestedAt: new Date().toISOString().slice(0, 10),
        suggestedWaitDays: chartPlan.suggestedTime.totalDays,
        timeSuggestionRationale: chartPlan.suggestedTime.rationale,
        timeWaitLabel: chartPlan.suggestedTime.waitLabel,
      },
    });

    const saved = await persistJourneyToServer(created);
    setJourney(saved ?? created);
    setShowStartForm(false);
  };

  const handleStartJourney = async () => {
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

    if (timeAmount < 1) {
      setFormError("Time target must be at least 1.");
      return;
    }

    setFormError(null);
    const created = createJourney({
      symbol,
      horizon,
      targetPriceInr: Math.round(target),
      entryPriceInr: entry ? Math.round(entry) : undefined,
      investedAmountInr: amount ? Math.round(amount) : undefined,
      targetDurationAmount: timeAmount,
      targetDurationUnit: timeUnit,
    });

    const saved = await persistJourneyToServer(created);
    setJourney(saved ?? created);
    setShowStartForm(false);
  };

  if (!symbol.trim()) {
    return null;
  }

  const stalePlanBanner =
    portfolioDataStale && !journey ? (
      <p className="mb-3 rounded-lg border border-amber-500/20 bg-amber-500/[0.06] px-3 py-2 text-xs leading-relaxed text-amber-100/90">
        {JOURNEY_COPY.stalePlanWarning}
      </p>
    ) : null;

  if (!journey && !apexSuggested) {
    return null;
  }

  if (!journey && !showStartForm && planState === "loading") {
    return (
      <section
        className={`rounded-xl border border-apex-border/20 bg-white/[0.02] px-4 py-4 ${className}`.trim()}
        aria-label="Loading investment journey"
      >
        {stalePlanBanner}
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-apex-muted">
          {JOURNEY_COPY.panelTitle}
        </p>
        <p className="mt-2 text-sm text-apex-muted/80">{JOURNEY_COPY.loadingPlan}</p>
      </section>
    );
  }

  if (!journey && !showStartForm && planState === "insufficient") {
    return (
      <section
        className={`rounded-xl border border-amber-500/15 bg-amber-500/[0.04] px-4 py-4 ${className}`.trim()}
        aria-label="Investment journey unavailable"
      >
        {stalePlanBanner}
        <p className="text-sm text-apex-text/90">{JOURNEY_COPY.insufficientData}</p>
      </section>
    );
  }

  if (!journey && !showStartForm && chartPlan && planState === "ready") {
    if (!isValidJourneyPlan(chartPlan)) {
      return (
        <section
          className={`rounded-xl border border-amber-500/15 bg-amber-500/[0.04] px-4 py-4 ${className}`.trim()}
          aria-label="Investment journey unavailable"
        >
          {stalePlanBanner}
          <p className="text-sm text-apex-text/90">{JOURNEY_COPY.insufficientData}</p>
        </section>
      );
    }

    const previewPct = previewProgressPct(
      chartPlan.entryPriceInr,
      chartPlan.targetPriceInr,
      effectiveLivePrice,
    );

    return (
      <section
        className={`${INFOGRAPHIC_CARD} ${className}`.trim()}
        aria-label="Chart-backed investment journey"
      >
        {stalePlanBanner}
        <JourneyPatienceCallout
          patienceUntil={chartPlan.suggestedTime.patienceUntil}
          trustLine={JOURNEY_COPY.trustIndicatorsLine}
          compact={compact}
        />

        {dailyVerdict === "wait" && !brokerStepCompleted ? (
          <p className="mt-2 text-xs leading-relaxed text-apex-muted/75">
            {JOURNEY_COPY.waitPreviewLead}
          </p>
        ) : null}

        <JourneyTargetTrack
          className="mt-3"
          symbol={chartPlan.symbol}
          entryPriceInr={chartPlan.entryPriceInr}
          targetPriceInr={chartPlan.targetPriceInr}
          currentPriceInr={effectiveLivePrice}
          progressPct={previewPct}
          waitingForEntry={(quantity ?? 0) === 0 && !brokerStepCompleted}
          timeTargetLabel={formatTimeTargetLabel(
            chartPlan.suggestedTime.amount,
            chartPlan.suggestedTime.unit,
          )}
          timeProgressPct={0}
          timeRemainingLabel={chartPlan.suggestedTime.waitLabel.replace(/^Wait ~/, "")}
          compact={compact}
        />

        {!compact ? (
          <>
            <p className="mt-3 text-xs leading-relaxed text-apex-muted/75">
              {chartPlan.suggestedTime.rationale}
            </p>
            <JourneyTimeTargetPicker
              className="mt-4 border-t border-apex-border/10 pt-4"
              amount={timeAmount}
              unit={timeUnit}
              startedAt={planStartIso}
              suggestion={chartPlan.suggestedTime}
              onChange={({ amount, unit }) => {
                setTimeAmount(amount);
                setTimeUnit(unit);
              }}
              compact={compact}
            />
          </>
        ) : null}

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={commitChartPlan}
            className="rounded-lg bg-violet-600/85 px-4 py-2 text-sm font-medium text-white hover:bg-violet-600"
          >
            {JOURNEY_COPY.stayOnPath}
          </button>
          <button
            type="button"
            onClick={() => setShowStartForm(true)}
            className="text-sm text-apex-muted/75 underline underline-offset-2 hover:text-apex-text"
          >
            {JOURNEY_COPY.adjustManually}
          </button>
        </div>

        <p className="mt-3 text-[11px] text-apex-muted/60">{JOURNEY_COPY.disclaimer}</p>
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
              onClick={() => {
                setHorizon(value);
                const suggested = suggestTimeTarget(value);
                setTimeAmount(suggested.amount);
                setTimeUnit(suggested.unit);
              }}
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
        </div>

        <JourneyTimeTargetPicker
          className="mt-4"
          amount={timeAmount}
          unit={timeUnit}
          startedAt={planStartIso}
          onChange={({ amount, unit }) => {
            setTimeAmount(amount);
            setTimeUnit(unit);
          }}
        />

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

  const entryForTrack = progress.entryPriceInr ?? progress.targetPriceInr * 0.92;

  return (
    <section
      className={`${INFOGRAPHIC_CARD} ${className}`.trim()}
      aria-label="Investment journey progress"
    >
      {portfolioDataStale ? (
        <p className="mb-3 rounded-lg border border-amber-500/20 bg-amber-500/[0.06] px-3 py-2 text-xs leading-relaxed text-amber-100/90">
          {JOURNEY_COPY.stalePlanWarning}
        </p>
      ) : null}
      {progress.patienceUntilLabel ? (
        <JourneyPatienceCallout
          patienceUntil={progress.patienceUntilLabel}
          trustLine={JOURNEY_COPY.trustIndicatorsLine}
          compact={compact}
        />
      ) : null}

      <JourneyTargetTrack
        className={progress.patienceUntilLabel ? "mt-3" : undefined}
        symbol={progress.symbol}
        entryPriceInr={entryForTrack}
        targetPriceInr={progress.targetPriceInr}
        currentPriceInr={progress.currentPriceInr}
        progressPct={progress.progressPct}
        waitingForEntry={
          progress.milestone === "waiting_entry" || progress.milestone === "planning"
        }
        targetReached={progress.targetReached}
        thesisBroken={progress.thesisBroken}
        timeTargetLabel={progress.timeTargetLabel}
        timeProgressPct={progress.timeProgressPct}
        timeRemainingLabel={progress.timeRemainingLabel}
        timeOverdue={progress.timeOverdue}
        patienceUntilLabel={compact ? progress.patienceUntilLabel : null}
        compact={compact}
      />

      {progress.targetReached ? (
        <div className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-3">
          <p className="text-sm font-medium text-emerald-100">{JOURNEY_COPY.takeProfitTitle}</p>
          <p className="mt-1 text-xs leading-relaxed text-emerald-50/85">
            {JOURNEY_COPY.takeProfitBody}
          </p>
          <div className="mt-3 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => {
                onTakeProfit?.(progress.symbol);
              }}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
            >
              {JOURNEY_COPY.takeProfitAction}
            </button>
            <button
              type="button"
              onClick={() => {
                void updateJourneyStatusOnServer(
                  progress.journey.id,
                  "completed",
                ).then(() => reload());
              }}
              className="text-sm text-emerald-100/80 underline underline-offset-2 hover:text-white"
            >
              {JOURNEY_COPY.completeJourney}
            </button>
          </div>
        </div>
      ) : (
        <>
          <p className="mt-3 text-sm leading-snug text-apex-text/90">{progress.guidance}</p>
          {progress.timeSuggestionRationale ? (
            <p className="mt-2 text-[11px] leading-relaxed text-apex-muted/65">
              {progress.timeSuggestionRationale}
            </p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-3 text-xs">
            <button
              type="button"
              onClick={() => {
                void updateJourneyStatusOnServer(progress.journey.id, "paused").then(
                  () => reload(),
                );
              }}
              className="text-apex-muted/70 underline underline-offset-2 hover:text-apex-text"
            >
              {progress.thesisBroken ? JOURNEY_COPY.pauseJourney : "Pause path"}
            </button>
          </div>
        </>
      )}

      <p className="mt-3 text-[11px] text-apex-muted/60">{progress.disclaimer}</p>
    </section>
  );
}
