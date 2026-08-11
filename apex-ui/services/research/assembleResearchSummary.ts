import { fetchStockData } from "@/services/market/stockData";
import { fetchAlphaAiSummary } from "@/services/research/alphaAiBridge";
import type {
  ResearchQuestion,
  ResearchSummaryViewModel,
  ResearchVerdict,
} from "@/types/researchSummary";

function normalizeVerdict(value: string | undefined): ResearchVerdict {
  const upper = (value ?? "WAIT").toUpperCase();

  if (upper.includes("BUY") || upper.includes("YES") || upper.includes("STRONG")) {
    return "YES";
  }

  if (
    upper.includes("SELL") ||
    upper.includes("AVOID") ||
    upper.includes("NO") ||
    upper.includes("REDUCE")
  ) {
    return "NO";
  }

  return "WAIT";
}

function trendFromPrices(prices: number[]): { label: string; confidence: "high" | "medium" | "low" } {
  if (prices.length < 10) {
    return { label: "Insufficient price history.", confidence: "low" };
  }

  const recent = prices.slice(-5);
  const prior = prices.slice(-15, -5);
  const recentAvg = recent.reduce((sum, value) => sum + value, 0) / recent.length;
  const priorAvg =
    prior.length > 0
      ? prior.reduce((sum, value) => sum + value, 0) / prior.length
      : recentAvg;
  const changePct = priorAvg > 0 ? ((recentAvg - priorAvg) / priorAvg) * 100 : 0;

  if (changePct >= 3) {
    return {
      label: `Price trend is improving (+${changePct.toFixed(1)}% vs prior window).`,
      confidence: "medium",
    };
  }

  if (changePct <= -3) {
    return {
      label: `Price trend is weakening (${changePct.toFixed(1)}% vs prior window).`,
      confidence: "medium",
    };
  }

  return {
    label: "Price trend is range-bound — patience may be warranted.",
    confidence: "medium",
  };
}

function buildQuestions(
  symbol: string,
  alpha: Awaited<ReturnType<typeof fetchAlphaAiSummary>>,
  trend: ReturnType<typeof trendFromPrices>,
): ResearchQuestion[] {
  return [
    {
      id: "business",
      prompt: "Is this a good business?",
      answer:
        alpha?.business_overview?.slice(0, 280) ||
        "Business quality requires Alpha AI or fundamentals — review manually.",
      confidence: alpha?.business_overview ? "medium" : "low",
    },
    {
      id: "health",
      prompt: "Is the company financially healthy?",
      answer:
        alpha?.valuation_verdict?.slice(0, 220) ||
        "Use Alpha AI report for scored financial metrics.",
      confidence: alpha ? "medium" : "low",
    },
    {
      id: "valuation",
      prompt: "Is it overvalued?",
      answer:
        alpha?.valuation_verdict ||
        "Valuation context unavailable without Alpha AI.",
      confidence: alpha?.valuation_verdict ? "medium" : "low",
    },
    {
      id: "timing",
      prompt: "Is now a good time to buy?",
      answer: alpha?.buy_decision_why || trend.label,
      confidence: alpha?.buy_decision_why ? "medium" : trend.confidence,
    },
    {
      id: "risk",
      prompt: "What are the key risks?",
      answer:
        alpha?.red_flags?.slice(0, 2).join(" · ") ||
        alpha?.risk_level ||
        "Risk framing unavailable.",
      confidence: alpha ? "medium" : "low",
    },
    {
      id: "technical",
      prompt: "What does price action suggest?",
      answer: alpha?.technical_summary || trend.label,
      confidence: alpha?.technical_summary ? "medium" : trend.confidence,
    },
    {
      id: "decision",
      prompt: `Should I invest in ${symbol}?`,
      answer:
        alpha?.buy_decision_why ||
        "Wait for clearer evidence before sizing a new position.",
      confidence: alpha ? "medium" : "low",
    },
  ];
}

export async function assembleResearchSummary(
  symbolInput: string,
): Promise<ResearchSummaryViewModel> {
  const symbol = symbolInput.trim().toUpperCase();
  const builtAt = new Date().toISOString();
  const [alpha, market] = await Promise.all([
    fetchAlphaAiSummary(symbol),
    fetchStockData(symbol),
  ]);

  const trend = trendFromPrices(market.prices);
  const questions = buildQuestions(symbol, alpha, trend);
  const verdict = normalizeVerdict(alpha?.buy_decision ?? alpha?.recommendation);
  const verdictLabel =
    verdict === "YES" ? "Buy" : verdict === "NO" ? "Avoid" : "Wait";

  return {
    symbol,
    built_at: builtAt,
    source: alpha ? "alpha_ai" : market.prices.length > 0 ? "market_data" : "partial",
    verdict,
    verdict_label: verdictLabel,
    headline: alpha?.name
      ? `${alpha.name} (${symbol})`
      : `Research · ${symbol}`,
    summary:
      alpha?.buy_decision_why ||
      `${symbol} — ${trend.label} Use this workspace before acting on Today.`,
    score: alpha?.overall_score ?? null,
    grade:
      alpha?.investment_grade_stars !== undefined
        ? `${alpha.investment_grade_stars}★`
        : null,
    recommendation: alpha?.recommendation ?? null,
    risk_level: alpha?.risk_level ?? null,
    questions,
    gaps: alpha?.data_gaps ?? [],
    alpha_available: Boolean(alpha),
  };
}

export function runResearchSummarySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Research summary self-check failed: ${message}`);
    }
  };

  assert(normalizeVerdict("Strong Buy") === "YES", "Strong Buy maps to YES");
  assert(normalizeVerdict("Avoid") === "NO", "Avoid maps to NO");
  assert(normalizeVerdict("Hold") === "WAIT", "Hold maps to WAIT");
}
