import {
  getExpenseMidpoint,
  getIncomeMidpoint,
  getInvestableSurplus,
  type FinancialProfile,
} from "@/lib/financialProfile";
import type {
  DailyDecisionOutput,
  DailyDecisionType,
  DecisionActionType,
  DecisionEngineInput,
} from "@/types/decision";
import { dailyDecisionTypeToAction } from "@/types/decision";
import type { MentorDecision } from "@/types/mentorDecision";
import type { Holding } from "@/types/portfolio";

const CONCENTRATION_REDUCE_THRESHOLD = 50;
const HIGH_CONCENTRATION_THRESHOLD = 80;

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
    if (context.allocation !== undefined && context.allocation < 40) {
      factors.push("Allocation looks spread — room to invest steadily");
    }
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

export function evaluateDailyDecision(
  input: DecisionEngineInput,
): DailyDecisionOutput {
  const { portfolioSnapshot, financialProfile, lastMentorOutput } = input;
  const hasProfile = Boolean(financialProfile);
  const topHolding = getTopHolding(portfolioSnapshot.holdings);
  const topWeight = topHolding?.weight ?? 0;
  const stock =
    topWeight > CONCENTRATION_REDUCE_THRESHOLD && topHolding
      ? topHolding.symbol
      : undefined;
  const allocation =
    topWeight > CONCENTRATION_REDUCE_THRESHOLD
      ? Math.round(topWeight)
      : undefined;
  const topHoldingPnl = topHolding?.pnl;

  let decision: DailyDecisionType = "HOLD";
  let reason =
    "Your portfolio looks balanced for now — staying steady is reasonable.";
  let suggestion: string | undefined;
  let reduceIntelligence: ReduceIntelligence | undefined;
  let underInvested = false;
  const expensesHigh = Boolean(
    financialProfile && expensesMeetOrExceedIncome(financialProfile),
  );
  const holdingsCount = portfolioSnapshot.holdings.length;

  if (financialProfile && expensesMeetOrExceedIncome(financialProfile)) {
    decision = "WAIT";
    reason =
      "Your expenses look equal to or higher than income — pausing new investments protects cash flow before you deploy more capital.";
  } else if (financialProfile) {
    const surplus = getInvestableSurplus(financialProfile);
    const targetInvested = surplus * 9;

    if (surplus > 0 && portfolioSnapshot.total_value < targetInvested) {
      decision = "BUY_MORE";
      underInvested = true;
      reason =
        "You have investable surplus and your portfolio is below a comfortable long-term level — steady investing could help.";
    } else if (
      stock &&
      allocation !== undefined &&
      topHoldingPnl !== undefined
    ) {
      decision = "REDUCE";
      const sellPercent = suggestedSellPercent(
        allocation,
        topHoldingPnl > 0,
      );
      reduceIntelligence = buildReduceIntelligence(
        stock,
        allocation,
        topHoldingPnl,
        sellPercent,
      );
      suggestion = reduceIntelligence.suggestion;
      reason = reduceIntelligence.reason;
    }
  } else if (
    stock &&
    allocation !== undefined &&
    topHoldingPnl !== undefined
  ) {
    decision = "REDUCE";
    const sellPercent = suggestedSellPercent(allocation, topHoldingPnl > 0);
    reduceIntelligence = buildReduceIntelligence(
      stock,
      allocation,
      topHoldingPnl,
      sellPercent,
    );
    suggestion = reduceIntelligence.suggestion;
    reason = reduceIntelligence.reason;
  }

  const action = decisionToAction(decision);
  const suggested_sell_percent =
    action === "reduce" && allocation !== undefined && topHoldingPnl !== undefined
      ? suggestedSellPercent(allocation, topHoldingPnl > 0)
      : undefined;
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
    action,
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
