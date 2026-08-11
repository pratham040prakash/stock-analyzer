"use client";

import {
  isDailyLossLimitBreached,
  PAUSE_LOSS_STREAK_THRESHOLD,
} from "@/lib/dailyLoop/dailyVerdict";
import { MAX_DAILY_LOSS_PCT } from "@/services/risk/riskControl";

export type CapitalDamsStripProps = {
  portfolioValue?: number | null;
  portfolioDayPnl?: number | null;
  consecutiveLossDays?: number;
  maxLossPct?: number;
  className?: string;
};

function formatInr(value: number): string {
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export default function CapitalDamsStrip({
  portfolioValue,
  portfolioDayPnl,
  consecutiveLossDays = 0,
  maxLossPct = MAX_DAILY_LOSS_PCT,
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

  return (
    <div
      className={`rounded-xl border border-apex-border/15 bg-white/[0.02] px-4 py-3 text-xs text-apex-muted/80 ${className}`.trim()}
      aria-label="Capital protection limits"
    >
      <p className="font-medium text-apex-text/85">Capital dams</p>
      <ul className="mt-1.5 space-y-1">
        <li>
          Daily loss limit ·{" "}
          {limitInr !== null ? `${formatInr(limitInr)} (${lossPctLabel} portfolio)` : "Connect broker for limit"}
          {dailyLossBreached
            ? " · hit — Pause active"
            : lossUsed > 0 && limitInr !== null
              ? ` · ${formatInr(lossUsed)} used of ${formatInr(limitInr)}`
              : " · within limit"}
        </li>
        <li>
          Loss-day pause · after {PAUSE_LOSS_STREAK_THRESHOLD} consecutive loss days
          {lossStreakActive
            ? ` · active (${consecutiveLossDays} days)`
            : consecutiveLossDays > 0
              ? ` · ${consecutiveLossDays} day${consecutiveLossDays === 1 ? "" : "s"}`
              : " · clear"}
        </li>
        <li>Sacred core · long-term holdings are not bought on Today</li>
      </ul>
    </div>
  );
}
