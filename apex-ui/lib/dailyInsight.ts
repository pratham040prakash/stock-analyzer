import type { DailyInsight, MarketTrendKind } from "@/types/dailyInsight";
import type { TapeRegime } from "@/lib/market/tapeRegime";
import type { MarketTrendResult } from "@/services/market/trend";
import type { DailyDecisionArtifact } from "@/types/decision";

function formatDayPnlLine(dayPnl: number): string {
  const abs = Math.abs(dayPnl);
  const formatted = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(abs);

  if (dayPnl > 0) {
    return `+${formatted} gain`;
  }
  if (dayPnl < 0) {
    return `-${formatted} loss`;
  }
  return "Flat today";
}

export type InsightArtifactContext = Pick<
  DailyDecisionArtifact,
  "daily_verdict" | "tradingLocked" | "blockers"
> | null;

export function insightGuidance(
  trend: MarketTrendKind,
  dayPnl: number | null,
  tape?: Pick<TapeRegime, "hardWait" | "oversoldBounce" | "briefLine">,
  artifact?: InsightArtifactContext,
): string {
  // Wave 2 non-contradiction: supportive market copy must never invite
  // action when Today's frozen decision is locked or WAIT/PAUSE.
  if (artifact && (artifact.tradingLocked || artifact.daily_verdict !== "trade")) {
    const primary = artifact.blockers[0];
    return primary
      ? `Today is Wait — ${primary}`
      : "Today is Wait — hold new positions.";
  }

  if (tape?.hardWait || tape?.oversoldBounce) {
    return tape.briefLine;
  }

  if (trend === "bearish" || trend === "slightly_bearish") {
    return "Avoid adding new positions";
  }

  if (trend === "bullish" || trend === "slightly_bullish") {
    return "Markets look supportive — stick to your plan if investing";
  }

  if (dayPnl !== null && dayPnl < 0) {
    return "Stay patient — no need to react to a red day";
  }

  return "Stay steady — no rush to act today";
}

export function buildDailyInsight(
  dayPnl: number | null,
  market: MarketTrendResult,
  tape?: TapeRegime,
  artifact?: InsightArtifactContext,
): DailyInsight {
  return {
    day_pnl: dayPnl,
    market_trend: market.trend,
    market_label: market.label,
    guidance: insightGuidance(market.trend, dayPnl, tape, artifact),
    pnl_line:
      dayPnl === null ? "Today's move unavailable" : formatDayPnlLine(dayPnl),
    tape_label: tape?.label,
    tape_hard_wait: tape?.hardWait === true,
  };
}

export function runDailyInsightSelfCheck(): void {
  const bullishMarket: MarketTrendResult = {
    trend: "bullish",
    label: "Nifty up",
    change_pct: 1.2,
  };
  const supportive = insightGuidance("bullish", 0, undefined, null);
  if (!supportive.toLowerCase().includes("supportive")) {
    throw new Error(
      "Daily insight self-check failed: bullish trend must remain supportive without artifact",
    );
  }

  const locked = insightGuidance("bullish", 0, undefined, {
    daily_verdict: "wait",
    tradingLocked: true,
    blockers: ["Broker not connected"],
  });
  if (!locked.startsWith("Today is Wait")) {
    throw new Error(
      "Daily insight self-check failed: locked artifact must force Wait copy",
    );
  }

  const insight = buildDailyInsight(0, bullishMarket, undefined, {
    daily_verdict: "wait",
    tradingLocked: true,
    blockers: [],
  });
  if (!insight.guidance.startsWith("Today is Wait")) {
    throw new Error(
      "Daily insight self-check failed: buildDailyInsight must apply artifact guard",
    );
  }
}
