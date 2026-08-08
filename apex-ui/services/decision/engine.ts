import {
  getExpenseMidpoint,
  getIncomeMidpoint,
  getInvestableSurplus,
  type FinancialProfile,
} from "@/lib/financialProfile";
import {
  getOpportunities,
  portfolioContextFromHoldings,
  type RecommendationPortfolio,
} from "@/lib/recommendations";
import { portfolioRiskFromAllocation } from "@/lib/portfolioRisk";
import {
  getTopPicks,
  getMarketRegime,
  portfolioScoringContextFromRecommendation,
} from "@/services/decision/stockScoring";
import { computeConfidenceSafe } from "@/services/decision/confidenceEngine";
import { computeStructureScoreSafe } from "@/services/market/structureEngine";
import type {
  DailyDecisionOutput,
  DailyDecisionType,
  DecisionActionType,
  DecisionEngineInput,
  DecisionOpportunity,
  MarketTrend,
  Signals,
  StockPick,
  ValidationResult,
} from "@/types/decision";
import { dailyDecisionTypeToAction } from "@/types/decision";
import type { Intent } from "@/types/intent";
import type { MentorDecision } from "@/types/mentorDecision";
import type { Holding } from "@/types/portfolio";

const CONCENTRATION_REDUCE_THRESHOLD = 50;
const HIGH_CONCENTRATION_THRESHOLD = 80;
const BUY_MAX_ALLOCATION_THRESHOLD = 50;
const MIN_HOLDINGS_FOR_BUY = 2;

function isPortfolioConcentrated(topWeight: number): boolean {
  return topWeight > CONCENTRATION_REDUCE_THRESHOLD;
}

function isHighlyConcentrated(topWeight: number): boolean {
  return topWeight > HIGH_CONCENTRATION_THRESHOLD;
}

function isPortfolioDiversified(
  topWeight: number,
  holdingsCount: number,
): boolean {
  return (
    holdingsCount >= MIN_HOLDINGS_FOR_BUY &&
    topWeight < BUY_MAX_ALLOCATION_THRESHOLD
  );
}

function portfolioAllowsBuy(topWeight: number, holdingsCount: number): boolean {
  return (
    !isHighlyConcentrated(topWeight) &&
    !isPortfolioConcentrated(topWeight) &&
    isPortfolioDiversified(topWeight, holdingsCount)
  );
}

function applyReduceDecision(
  stock: string,
  allocation: number,
  topHoldingPnl: number,
): {
  suggestion: string;
  reason: string;
  reduceIntelligence: ReduceIntelligence;
} {
  const sellPercent = suggestedSellPercent(allocation, topHoldingPnl > 0);
  const reduceIntelligence = buildReduceIntelligence(
    stock,
    allocation,
    topHoldingPnl,
    sellPercent,
  );

  return {
    suggestion: reduceIntelligence.suggestion,
    reason: reduceIntelligence.reason,
    reduceIntelligence,
  };
}

function clampConfidence(value: number): number {
  return Math.min(100, Math.max(0, Math.round(value)));
}

function getTopHolding(holdings: Holding[]): {
  symbol: string;
  weight: number;
  pnl: number;
} | null {
  const totalValue = holdings.reduce(
    (sum, h) => sum + h.quantity * h.currentPrice,
    0,
  );

  if (totalValue <= 0 || holdings.length === 0) {
    return null;
  }

  let top: Holding = holdings[0];
  let topValue = holdings[0].quantity * holdings[0].currentPrice;

  for (const h of holdings) {
    const value = h.quantity * h.currentPrice;
    if (value > topValue) {
      topValue = value;
      top = h;
    }
  }

  return {
    symbol: top.symbol,
    weight: (topValue / totalValue) * 100,
    pnl: (top.currentPrice - top.avgPrice) * top.quantity,
  };
}

function expensesMeetOrExceedIncome(profile: FinancialProfile): boolean {
  return (
    getExpenseMidpoint(profile.expenseRange) >=
    getIncomeMidpoint(profile.incomeRange)
  );
}

function decisionToAction(decision: DailyDecisionType): DecisionActionType {
  return dailyDecisionTypeToAction(decision);
}

function suggestedSellPercent(allocation: number, inProfit: boolean): number {
  if (allocation > 90) {
    return inProfit ? 25 : 20;
  }
  if (allocation > 80) {
    return inProfit ? 20 : 20;
  }
  return 15;
}

type ReduceIntelligence = {
  suggestion: string;
  reason: string;
  message: string;
};

function buildReduceIntelligence(
  stock: string,
  allocation: number,
  topHoldingPnl: number,
  sellPercent: number,
): ReduceIntelligence {
  if (allocation > HIGH_CONCENTRATION_THRESHOLD) {
    if (topHoldingPnl > 0) {
      return {
        suggestion: "Book partial profit",
        reason: `${stock} is ${allocation}% of your portfolio with unrealised gains — trimming now locks in profit while lowering concentration risk.`,
        message: `Book partial profit — sell ${sellPercent}% of ${stock} while gains are intact`,
      };
    }

    return {
      suggestion: "Reduce risk exposure",
      reason: `${stock} is ${allocation}% of your portfolio and underwater — reducing size lowers single-stock risk without forcing a full exit.`,
      message: `Reduce risk exposure — trim ${sellPercent}% of ${stock} to rebalance`,
    };
  }

  if (topHoldingPnl > 0) {
    return {
      suggestion: "Rebalance gradually",
      reason: `${stock} is ${allocation}% of your portfolio — taking some profit off the table keeps you diversified without abandoning the position.`,
      message: `Sell ${sellPercent}% of ${stock} to rebalance while keeping exposure`,
    };
  }

  return {
    suggestion: "Reduce concentration",
    reason: `${stock} is ${allocation}% of your portfolio — spreading weight reduces the impact of one stock on your overall outcome.`,
    message: `Sell ${sellPercent}% of ${stock} to reduce concentration risk`,
  };
}

function buildMessage(
  action: DecisionActionType,
  stock?: string,
  sellPercent?: number,
  reduceIntelligence?: ReduceIntelligence,
): string | undefined {
  if (action === "reduce" && reduceIntelligence) {
    return reduceIntelligence.message;
  }

  if (action === "reduce" && stock && sellPercent !== undefined) {
    return `Sell ${sellPercent}% of ${stock} to reduce risk`;
  }

  if (action === "buy") {
    return "Invest your monthly surplus in steady, small steps";
  }

  if (action === "wait") {
    return "Pause new investments until your cash flow stabilises";
  }

  return undefined;
}

function actionsForDecision(
  decision: DailyDecisionType,
  focusSymbol?: string,
  suggestion?: string,
): string[] {
  switch (decision) {
    case "WAIT":
      return [
        "Pause new investments until expenses are under control",
        "Focus on building a small emergency buffer first",
      ];
    case "BUY_MORE":
      return [
        "Invest your monthly surplus in steady, small steps",
        focusSymbol
          ? `Review ${focusSymbol} and other large holdings before adding more`
          : "Review your largest holdings before adding more",
      ];
    case "REDUCE":
      if (suggestion === "Book partial profit" && focusSymbol) {
        return [
          `Consider selling 10–25% of ${focusSymbol} to lock in gains`,
          "Redeploy proceeds into other sectors or cash for flexibility",
        ];
      }
      if (suggestion === "Reduce risk exposure" && focusSymbol) {
        return [
          `Trim ${focusSymbol} gradually — small steps beat reactive selling`,
          "Avoid adding more to this position until allocation improves",
        ];
      }
      return [
        focusSymbol
          ? `Review trimming ${focusSymbol} gradually — no need to rush`
          : "Review your most overweight holding",
        "Consider rebalancing toward a more even allocation",
      ];
    default:
      return [
        "Stay steady — no change needed today",
        "Keep watching; your plan still looks balanced",
      ];
  }
}

function mentorAligns(
  decision: DailyDecisionType,
  mentor: MentorDecision | null | undefined,
): boolean {
  if (!mentor) return false;

  if (decision === "WAIT") {
    return mentor.action === "observe" || mentor.action === "hold";
  }

  if (decision === "BUY_MORE") {
    return mentor.action === "add";
  }

  if (decision === "REDUCE") {
    return mentor.action === "reduce";
  }

  return mentor.action === "hold" || mentor.action === "observe";
}

type ConfidenceContext = {
  allocation?: number;
  topHoldingPnl?: number;
  suggestion?: string;
  portfolioPnl?: number;
};

function confidenceForDecision(
  decision: DailyDecisionType,
  mentor: MentorDecision | null | undefined,
  hasProfile: boolean,
  context: ConfidenceContext = {},
): number {
  const base: Record<DailyDecisionType, number> = {
    WAIT: 88,
    BUY_MORE: 78,
    REDUCE: 76,
    HOLD: 68,
    EXPLORE: 74,
  };

  let confidence = base[decision];

  if (!hasProfile) {
    confidence -= 10;
  }

  if (mentorAligns(decision, mentor)) {
    confidence += 8;
  }

  if (mentor?.confidence === "high") {
    confidence += 4;
  } else if (mentor?.confidence === "low") {
    confidence -= 4;
  }

  if (decision === "REDUCE" && context.allocation !== undefined) {
    if (context.allocation > 90) {
      confidence += 8;
    } else if (context.allocation > HIGH_CONCENTRATION_THRESHOLD) {
      confidence += 6;
    } else if (context.allocation > 60) {
      confidence += 3;
    }

    if (
      context.allocation > HIGH_CONCENTRATION_THRESHOLD &&
      context.topHoldingPnl !== undefined
    ) {
      if (context.topHoldingPnl > 0) {
        confidence += context.suggestion === "Book partial profit" ? 6 : 3;
      } else {
        confidence += context.suggestion === "Reduce risk exposure" ? 5 : 2;
      }
    }
  }

  if (
    decision === "WAIT" &&
    context.portfolioPnl !== undefined &&
    context.portfolioPnl < 0
  ) {
    confidence += 3;
  }

  return clampConfidence(confidence);
}

function buildConfidenceFactors(
  decision: DailyDecisionType,
  context: {
    stock?: string;
    allocation?: number;
    holdingsCount: number;
    topHoldingPnl?: number;
    hasProfile: boolean;
    mentorAligned: boolean;
    underInvested: boolean;
    expensesHigh: boolean;
  },
): string[] {
  const factors: string[] = [];

  if (decision === "REDUCE" && context.allocation !== undefined) {
    if (context.stock) {
      factors.push(
        `Portfolio is ${context.allocation}% in ${context.stock}`,
      );
    } else {
      factors.push(
        `Portfolio is ${context.allocation}% in one stock`,
      );
    }

    if (context.holdingsCount <= 1 || context.allocation >= 80) {
      factors.push("No diversification");
    }

    if (context.allocation > 80) {
      factors.push("High downside risk");
      factors.push("Buying more is not allowed above 80% concentration");
    } else if (context.allocation > 60) {
      factors.push("Elevated concentration risk");
    }

    if (context.topHoldingPnl !== undefined && context.topHoldingPnl < 0) {
      factors.push("Top holding is currently underwater");
    } else if (
      context.topHoldingPnl !== undefined &&
      context.topHoldingPnl > 0 &&
      context.allocation > 80
    ) {
      factors.push("Profits are tied to a single position");
    }
  } else if (decision === "WAIT") {
    if (context.expensesHigh) {
      factors.push("Expenses match or exceed your income");
      factors.push("Cash flow needs protection before new investments");
    }
    if (!context.hasProfile) {
      factors.push("Complete your financial profile for sharper guidance");
    }
  } else if (decision === "BUY_MORE") {
    if (context.underInvested) {
      factors.push("Investable surplus is available each month");
      factors.push("Portfolio size is below a steady long-term target");
    }
    if (context.holdingsCount >= MIN_HOLDINGS_FOR_BUY) {
      factors.push("Holdings are spread across multiple positions");
    }
    if (context.allocation !== undefined && context.allocation < BUY_MAX_ALLOCATION_THRESHOLD) {
      factors.push("Top holding is below 50% — room to invest steadily");
    }
  } else if (decision === "HOLD" && context.allocation !== undefined && context.allocation > HIGH_CONCENTRATION_THRESHOLD) {
    factors.push(`Portfolio is ${context.allocation}% in one stock`);
    factors.push("No diversification");
    factors.push("Buying more is not allowed at this concentration");
  } else {
    factors.push("Portfolio allocation looks reasonably balanced");
    if (context.holdingsCount >= 3) {
      factors.push("Holdings are spread across multiple positions");
    }
  }

  if (context.mentorAligned) {
    factors.push("Mentor view supports this call");
  }

  if (!context.hasProfile && decision !== "WAIT") {
    factors.push("Add your financial profile to refine confidence");
  }

  return factors.slice(0, 5);
}


function recommendationPortfolioFromSnapshot(
  input: DecisionEngineInput,
): RecommendationPortfolio {
  return portfolioContextFromHoldings(input.portfolioSnapshot.holdings);
}

export function validateDecision({
  signals,
  marketTrend,
  portfolioRisk,
}: {
  signals: Signals;
  marketTrend: MarketTrend;
  portfolioRisk: number;
}): ValidationResult {
  const signalStrength =
    (signals.trend + signals.momentum + signals.volume) / 3;

  const signalAgreement =
    signals.trend > 60 && signals.momentum > 60;

  const marketAlignment =
    marketTrend === "bullish" && signals.trend > 60;

  const riskOk = portfolioRisk < 8;

  const score =
    signalStrength * 0.4 +
    (signalAgreement ? 20 : 0) +
    (marketAlignment ? 20 : 0) +
    (riskOk ? 20 : 0);

  const confidence = Math.min(100, Math.round(score));

  return {
    confidence,
    isValid: confidence > 65 && signalAgreement,
    breakdown: {
      signal_strength: Math.round(signalStrength),
      signal_agreement: signalAgreement,
      market_alignment: marketAlignment,
      risk_ok: riskOk,
    },
  };
}

function resolveSignals(signals?: Partial<Signals>): Signals {
  return {
    trend: signals?.trend ?? 50,
    momentum: signals?.momentum ?? 50,
    volume: signals?.volume ?? 50,
  };
}

function resolveMarketTrend(marketTrend?: MarketTrend): MarketTrend {
  return marketTrend ?? "sideways";
}

function resolvePortfolioRisk(portfolioRisk?: number): number {
  return portfolioRisk && portfolioRisk > 0 ? portfolioRisk : 7;
}

/** Market context for validation — uses detected NIFTY regime with safe defaults. */
async function getValidationMarketContext(portfolioRiskScore: number): Promise<{
  marketTrend: MarketTrend;
  portfolioRisk: number;
}> {
  const marketTrend = await getMarketRegime();

  return {
    marketTrend: resolveMarketTrend(marketTrend),
    portfolioRisk: resolvePortfolioRisk(portfolioRiskScore),
  };
}

async function enrichWithConfidenceMetrics(
  decision: DailyDecisionOutput,
  signals: Signals,
  marketTrend: MarketTrend,
  input: DecisionEngineInput,
): Promise<DailyDecisionOutput> {
  const structureScore = await computeStructureScoreSafe(decision.stock);
  const confidenceMetrics = await computeConfidenceSafe({
    signals,
    regime: marketTrend,
    supabase: input.supabase ?? null,
    userId: input.userId ?? null,
    structureScore,
  });

  return {
    ...decision,
    structureScore,
    confidenceMetrics,
  };
}

function buildWaitDecisionFromValidation(
  intent: Intent,
  validation: ValidationResult,
  hasProfile: boolean,
  picks: StockPick[],
): DailyDecisionOutput {
  return {
    decision: "WAIT",
    action: "wait",
    intent,
    confidence: validation.confidence,
    message: "No strong opportunity today",
    validation: validation.breakdown,
    picks,
    reason: "Signals are not strong enough to act today",
    confidence_factors: [
      `Signal strength: ${validation.breakdown.signal_strength}/100`,
      validation.breakdown.signal_agreement
        ? "Trend and momentum agree"
        : "Trend and momentum do not align",
      validation.breakdown.market_alignment
        ? "Market trend supports new positions"
        : "Market trend does not support new positions",
      validation.breakdown.risk_ok
        ? "Portfolio risk is within limits"
        : "Portfolio risk is elevated",
      hasProfile
        ? "Financial profile is available for sizing guidance"
        : "Add your financial profile to refine guidance",
    ],
    actions: [
      "Pause new investments until signals strengthen",
      "Review your portfolio allocation before acting",
    ],
    opportunities: [],
  };
}

async function buildGrowDecision(
  input: DecisionEngineInput,
  hasProfile: boolean,
  mentor: MentorDecision | null | undefined,
): Promise<DailyDecisionOutput> {
  const mentorAligned = mentor?.action === "add";
  const portfolio = recommendationPortfolioFromSnapshot(input);
  const scoringPortfolio = portfolioScoringContextFromRecommendation(portfolio);
  const { risk_level: risk, risk_score: portfolioRiskScore } =
    portfolioRiskFromAllocation(portfolio.top_allocation_pct ?? 0);
  const topPicks = await getTopPicks(
    5,
    scoringPortfolio,
    input.adaptiveSignalWeights,
  );
  const best = topPicks[0];
  const { marketTrend, portfolioRisk } =
    await getValidationMarketContext(portfolioRiskScore);
  const validation = validateDecision({
    signals: best?.signals ?? resolveSignals(),
    marketTrend,
    portfolioRisk,
  });

  console.log("Decision Validation:", validation);

  if (!validation.isValid) {
    return enrichWithConfidenceMetrics(
      buildWaitDecisionFromValidation(
        "grow",
        validation,
        hasProfile,
        topPicks,
      ),
      best?.signals ?? resolveSignals(),
      marketTrend,
      input,
    );
  }

  return enrichWithConfidenceMetrics(
    {
      decision: "BUY_MORE",
      action: "buy",
      intent: "grow",
      stock: best?.stock,
      confidence: validation.confidence,
      message: best ? `Top opportunity: ${best.stock}` : "Strong opportunity based on aligned signals",
      validation: validation.breakdown,
      picks: topPicks,
      suggestion: "Use available funds to accumulate quality stocks",
      opportunities: getOpportunities("grow", risk, portfolio),
      reason: "Portfolio size can be increased steadily",
      confidence_factors: [
        "You selected Grow Portfolio as today's intent",
        "Signals are aligned — trend, momentum, and market trend agree",
        hasProfile
          ? "Financial profile is available for sizing guidance"
          : "Add your financial profile to refine investable surplus",
        mentorAligned
          ? "Mentor view supports adding steadily"
          : "Small, regular steps beat timing the market",
      ],
      actions: [
        "Invest your available funds in steady, small steps",
        "Spread new money across quality names instead of one concentrated bet",
      ],
    },
    best?.signals ?? resolveSignals(),
    marketTrend,
    input,
  );
}

async function buildExploreDecision(
  input: DecisionEngineInput,
  hasProfile: boolean,
  mentor: MentorDecision | null | undefined,
): Promise<DailyDecisionOutput> {
  const mentorAligned =
    mentor?.action === "add" || mentor?.action === "observe";
  const portfolio = recommendationPortfolioFromSnapshot(input);
  const scoringPortfolio = portfolioScoringContextFromRecommendation(portfolio);
  const { risk_level: risk, risk_score: portfolioRiskScore } =
    portfolioRiskFromAllocation(portfolio.top_allocation_pct ?? 0);
  const topPicks = await getTopPicks(
    5,
    scoringPortfolio,
    input.adaptiveSignalWeights,
  );
  const best = topPicks[0];
  const { marketTrend, portfolioRisk } =
    await getValidationMarketContext(portfolioRiskScore);
  const validation = validateDecision({
    signals: best?.signals ?? resolveSignals(),
    marketTrend,
    portfolioRisk,
  });

  console.log("Decision Validation:", validation);

  if (!validation.isValid) {
    return enrichWithConfidenceMetrics(
      buildWaitDecisionFromValidation(
        "explore",
        validation,
        hasProfile,
        topPicks,
      ),
      best?.signals ?? resolveSignals(),
      marketTrend,
      input,
    );
  }

  return enrichWithConfidenceMetrics(
    {
      decision: "EXPLORE",
      action: "explore",
      intent: "explore",
      stock: best?.stock,
      confidence: validation.confidence,
      message: best ? `Top opportunity: ${best.stock}` : "Strong opportunity based on aligned signals",
      validation: validation.breakdown,
      picks: topPicks,
      opportunities: getOpportunities("explore", risk, portfolio),
      reason:
        "You asked to find opportunities — these ideas span stability, growth, and diversification.",
      confidence_factors: [
        "You selected Find Opportunities as today's intent",
        "Signals are aligned — trend, momentum, and market trend agree",
        hasProfile
          ? "Ideas are framed around your stated risk and income profile"
          : "Complete your profile for sharper opportunity matching",
        mentorAligned ? "Mentor view supports exploring new ideas" : "Research before acting — guidance only",
      ],
      actions: [
        "Review each idea against your existing holdings",
        "Start with a small position if something fits your plan",
      ],
    },
    best?.signals ?? resolveSignals(),
    marketTrend,
    input,
  );
}

function mapDecisionAction(
  action: DecisionActionType,
  intent: Intent,
): DecisionActionType {
  if (intent === "risk" && action === "reduce") {
    return "sell";
  }
  return action;
}

function buildRiskDecision(
  input: DecisionEngineInput,
): DailyDecisionOutput {
  const { portfolioSnapshot, financialProfile, lastMentorOutput } = input;
  const hasProfile = Boolean(financialProfile);
  const holdingsCount = portfolioSnapshot.holdings.length;
  const topHolding = getTopHolding(portfolioSnapshot.holdings);
  const topWeight = topHolding?.weight ?? 0;
  const allocation = topWeight > 0 ? Math.round(topWeight) : undefined;
  const topHoldingPnl = topHolding?.pnl;
  const concentrated = isPortfolioConcentrated(topWeight);
  const highlyConcentrated = isHighlyConcentrated(topWeight);
  const stock =
    concentrated && topHolding ? topHolding.symbol : undefined;

  let decision: DailyDecisionType = "HOLD";
  let reason =
    highlyConcentrated
      ? "Your portfolio is heavily concentrated — adding more is not advisable until you rebalance."
      : concentrated
        ? "Concentration is elevated — reducing exposure comes before buying more."
        : "Your portfolio looks balanced for now — staying steady is reasonable.";
  let suggestion: string | undefined;
  let reduceIntelligence: ReduceIntelligence | undefined;
  let suggestedSellOverride: number | undefined;
  let underInvested = false;
  const expensesHigh = Boolean(
    financialProfile && expensesMeetOrExceedIncome(financialProfile),
  );

  if (financialProfile && expensesMeetOrExceedIncome(financialProfile)) {
    decision = "WAIT";
    reason =
      "Your expenses look equal to or higher than income — pausing new investments protects cash flow before you deploy more capital.";
  } else if (
    allocation !== undefined &&
    allocation > HIGH_CONCENTRATION_THRESHOLD &&
    stock &&
    topHoldingPnl !== undefined
  ) {
    decision = "REDUCE";
    suggestedSellOverride = 25;
    suggestion = "Reduce risk exposure";
    reason = "High concentration risk";
    reduceIntelligence = {
      suggestion: "Reduce risk exposure",
      reason: "High concentration risk",
      message: "Sell 25% to reduce concentration",
    };
  } else if (
    concentrated &&
    stock &&
    allocation !== undefined &&
    topHoldingPnl !== undefined
  ) {
    decision = "REDUCE";
    const reduceDecision = applyReduceDecision(stock, allocation, topHoldingPnl);
    suggestion = reduceDecision.suggestion;
    reason = reduceDecision.reason;
    reduceIntelligence = reduceDecision.reduceIntelligence;
  } else if (highlyConcentrated) {
    decision = "HOLD";
    reason =
      "Your portfolio is heavily concentrated — hold off on new buys until allocation improves.";
  }

  const rawAction = decisionToAction(decision);
  const suggested_sell_percent =
    rawAction === "reduce" && allocation !== undefined && topHoldingPnl !== undefined
      ? suggestedSellOverride ??
        suggestedSellPercent(allocation, topHoldingPnl > 0)
      : undefined;
  const action = mapDecisionAction(rawAction, "risk");
  const confidence = confidenceForDecision(
    decision,
    lastMentorOutput,
    hasProfile,
    {
      allocation,
      topHoldingPnl,
      suggestion,
      portfolioPnl: portfolioSnapshot.pnl,
    },
  );
  const message = buildMessage(
    rawAction,
    stock,
    suggested_sell_percent,
    reduceIntelligence,
  );
  const mentorAligned = mentorAligns(decision, lastMentorOutput);
  const confidence_factors = buildConfidenceFactors(decision, {
    stock,
    allocation,
    holdingsCount,
    topHoldingPnl,
    hasProfile,
    mentorAligned,
    underInvested,
    expensesHigh,
  });

  return {
    decision,
    action,
    intent: "risk",
    stock,
    confidence,
    allocation,
    suggested_sell_percent,
    suggestion,
    message,
    reason,
    confidence_factors,
    actions: actionsForDecision(decision, stock, suggestion),
    focusSymbol: stock,
    focusAllocationPct: allocation,
  };
}

export async function getDecision(
  input: DecisionEngineInput,
): Promise<DailyDecisionOutput> {
  return evaluateDailyDecision(input);
}

export async function evaluateDailyDecision(
  input: DecisionEngineInput,
): Promise<DailyDecisionOutput> {
  const intent = input.intent ?? "risk";
  const hasProfile = Boolean(input.financialProfile);

  if (intent === "grow") {
    return buildGrowDecision(input, hasProfile, input.lastMentorOutput);
  }

  if (intent === "explore") {
    return buildExploreDecision(input, hasProfile, input.lastMentorOutput);
  }

  return buildRiskDecision({ ...input, intent: "risk" });
}
