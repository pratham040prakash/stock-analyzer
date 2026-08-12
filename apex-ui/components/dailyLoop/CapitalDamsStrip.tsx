"use client";

import {
  isDailyLossLimitBreached,
  PAUSE_LOSS_STREAK_THRESHOLD,
} from "@/lib/dailyLoop/dailyVerdict";
import { OPERATING_MANUAL } from "@/lib/dailyLoop/operatingManualCopy";
import { MAX_DAILY_LOSS_PCT } from "@/services/risk/riskControl";

export type CapitalDamsStripProps = {
  portfolioValue?: number | null;
  portfolioDayPnl?: number | null;
  consecutiveLossDays?: number;
  maxLossPct?: number;
  compact?: boolean;
  className?: string;
};

function formatInr(value: number): string {
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export function isRiskLimitsActive(input: {
  portfolioValue?: number | null;
  portfolioDayPnl?: number | null;
  consecutiveLossDays?: number;
  maxLossPct?: number;
}): boolean {
  const dailyLossBreached = isDailyLossLimitBreached(
    input.portfolioDayPnl,
    input.portfolioValue,
    input.maxLossPct ?? MAX_DAILY_LOSS_PCT,
  );
  const lossStreakActive =
    (input.consecutiveLossDays ?? 0) >= PAUSE_LOSS_STREAK_THRESHOLD;

  return dailyLossBreached || lossStreakActive;
}

export default function CapitalDamsStrip({
  portfolioValue,
  portfolioDayPnl,
  consecutiveLossDays = 0,
  maxLossPct = MAX_DAILY_LOSS_PCT,
  compact = false,
  className = "",
}: CapitalDamsStripProps) {
  const limitInr =
    portfolioValue !== null &&
    portfolioValue !== undefined &&
    Number.isFinite(portfolioValue) &&
    portfolioValue > 0
      ? Math.round(portfolioValue * maxLossPct)
      : null;
  const lossUsed =
    portfolioDayPnl !== null &&
    portfolioDayPnl !== undefined &&
    Number.isFinite(portfolioDayPnl) &&
    portfolioDayPnl < 0
      ? Math.abs(portfolioDayPnl)
      : 0;
  const dailyLossBreached = isDailyLossLimitBreached(
    portfolioDayPnl,
    portfolioValue,
    maxLossPct,
  );
  const lossStreakActive =
    consecutiveLossDays >= PAUSE_LOSS_STREAK_THRESHOLD;
  const lossPctLabel = `${Math.round(maxLossPct * 100)}%`;
  const active = dailyLossBreached || lossStreakActive;

  if (compact && !active) {
    return (
      <p
        className={`text-xs text-apex-muted/75 ${className}`.trim()}
        aria-label="Risk limits status"
      >
        {OPERATING_MANUAL.damsTitle} · daily loss within limit · loss streak clear
      </p>
    );
  }

  if (compact && active) {
    return (
      <div
        className={`rounded-xl border border-amber-500/20 bg-amber-500/[0.06] px-4 py-3 text-xs text-amber-100/85 ${className}`.trim()}
        aria-label="Risk limits active"
      >
        <p className="font-medium text-amber-100/95">{OPERATING_MANUAL.damsTitle} active</p>
        {dailyLossBreached ? (
          <p className="mt-1">Daily loss limit hit — Pause trading today.</p>
        ) : null}
        {lossStreakActive ? (
          <p className="mt-1">
            Loss streak pause · {consecutiveLossDays} consecutive loss days
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div
      className={`rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 text-xs text-apex-muted/80 ${className}`.trim()}
      aria-label="Risk limits"
    >
      <p className="font-medium text-apex-text/85">{OPERATING_MANUAL.damsTitle}</p>
      <ul className="mt-1.5 space-y-1">
        <li>
          {OPERATING_MANUAL.damsDailyLoss} ·{" "}
          {limitInr !== null ? `${formatInr(limitInr)} (${lossPctLabel} portfolio)` : "Connect broker for limit"}
          {dailyLossBreached
            ? " · hit — Pause active"
            : lossUsed > 0 && limitInr !== null
              ? ` · ${formatInr(lossUsed)} used of ${formatInr(limitInr)}`
              : " · within limit"}
        </li>
        <li>
          {OPERATING_MANUAL.damsLossStreak} · after {PAUSE_LOSS_STREAK_THRESHOLD} consecutive loss days
          {lossStreakActive
            ? ` · active (${consecutiveLossDays} days)`
            : consecutiveLossDays > 0
              ? ` · ${consecutiveLossDays} day${consecutiveLossDays === 1 ? "" : "s"}`
              : " · clear"}
        </li>
        <li>{OPERATING_MANUAL.damsSacredCore}</li>
      </ul>
    </div>
  );
}
