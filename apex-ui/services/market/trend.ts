import axios from "axios";
import type { MarketTrendKind } from "@/types/dailyInsight";

export type MarketTrendResult = {
  trend: MarketTrendKind;
  label: string;
  change_pct: number;
};

const NIFTY_CHART_URL =
  "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?range=5d&interval=1d";

let cachedTrend: { result: MarketTrendResult; at: number } | null = null;
const CACHE_MS = 5 * 60 * 1000;

export function marketTrendFromChangePct(changePct: number): MarketTrendResult {
  let trend: MarketTrendKind = "neutral";

  if (changePct >= 1) {
    trend = "bullish";
  } else if (changePct >= 0.3) {
    trend = "slightly_bullish";
  } else if (changePct <= -1) {
    trend = "bearish";
  } else if (changePct <= -0.3) {
    trend = "slightly_bearish";
  }

  return {
    trend,
    label: marketTrendLabel(trend),
    change_pct: changePct,
  };
}

export function marketTrendLabel(trend: MarketTrendKind): string {
  switch (trend) {
    case "bullish":
      return "Market bullish";
    case "slightly_bullish":
      return "Market slightly bullish";
    case "bearish":
      return "Market bearish";
    case "slightly_bearish":
      return "Market slightly bearish";
    default:
      return "Market is flat";
  }
}

export async function fetchMarketTrend(): Promise<MarketTrendResult> {
  if (cachedTrend && Date.now() - cachedTrend.at < CACHE_MS) {
    return cachedTrend.result;
  }

  try {
    const res = await axios.get(NIFTY_CHART_URL, {
      timeout: 8000,
      headers: { "User-Agent": "APEX/1.0" },
    });

    const result = res.data?.chart?.result?.[0];
    const closes: number[] = result?.indicators?.quote?.[0]?.close ?? [];
    const validCloses = closes.filter(
      (value): value is number => typeof value === "number" && !Number.isNaN(value),
    );

    if (validCloses.length >= 2) {
      const previousClose = validCloses[validCloses.length - 2];
      const latestClose = validCloses[validCloses.length - 1];
      const changePct =
        previousClose > 0
          ? ((latestClose - previousClose) / previousClose) * 100
          : 0;
      const trend = marketTrendFromChangePct(changePct);
      cachedTrend = { result: trend, at: Date.now() };
      return trend;
    }

    const meta = result?.meta;
    const price = meta?.regularMarketPrice;
    const prev = meta?.chartPreviousClose ?? meta?.previousClose;
    if (typeof price === "number" && typeof prev === "number" && prev > 0) {
      const changePct = ((price - prev) / prev) * 100;
      const trend = marketTrendFromChangePct(changePct);
      cachedTrend = { result: trend, at: Date.now() };
      return trend;
    }
  } catch {
    // Fall through to neutral default.
  }

  const fallback: MarketTrendResult = {
    trend: "neutral",
    label: marketTrendLabel("neutral"),
    change_pct: 0,
  };
  cachedTrend = { result: fallback, at: Date.now() };
  return fallback;
}
