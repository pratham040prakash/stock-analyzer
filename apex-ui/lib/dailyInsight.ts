import type { DailyInsight, MarketTrendKind } from "@/types/dailyInsight";
import type { MarketTrendResult } from "@/services/market/trend";

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

export function insightGuidance(
  trend: MarketTrendKind,
  dayPnl: number | null,
): string {
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
): DailyInsight {
  return {
    day_pnl: dayPnl,
    market_trend: market.trend,
    market_label: market.label,
    guidance: insightGuidance(market.trend, dayPnl),
    pnl_line:
      dayPnl === null ? "Today's move unavailable" : formatDayPnlLine(dayPnl),
  };
}
