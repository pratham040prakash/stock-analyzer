import { stockSignals } from "@/data/stockSignals";
import type { FinancialProfile } from "@/lib/financialProfile";
import {
  formatRupee,
  getExpenseMidpoint,
  getIncomeMidpoint,
} from "@/lib/financialProfile";
import type { MentorTone } from "@/lib/mentorCopy";
import { updateMemory } from "@/lib/userMemory";
import type {
  AffectedStock,
  FinancialContext,
  MentorAction,
  MentorConfidence,
  MentorDecision,
  MentorFocusArea,
  MentorUrgency,
  SessionHistory,
  StockSuggestion,
} from "@/types/mentorDecision";
import type { Holding, Portfolio } from "@/types/portfolio";

type StockSignal = (typeof stockSignals)[keyof typeof stockSignals];

type PortfolioMetrics = {
  sorted: Holding[];
  concentration: number;
  pnlPercent: number;
  totalInvested: number;
  totalValue: number;
  top: Holding | undefined;
  second: Holding | undefined;
  worst: Holding | undefined;
};

export type MentorBrainInput = {
  portfolio: Portfolio;
  stockSignals?: typeof stockSignals;
  financialProfile: FinancialProfile | null;
  sessionHistory: SessionHistory;
  mentorTone?: MentorTone;
};

function getPortfolioMetrics(portfolio: Portfolio): PortfolioMetrics {
  const sorted = [...portfolio.holdings].sort(
    (a, b) => b.quantity * b.currentPrice - a.quantity * a.currentPrice,
  );

  const totalValue = portfolio.holdings.reduce(
    (sum, h) => sum + h.quantity * h.currentPrice,
    0,
  );

  const top2Value =
    sorted.length >= 2
      ? sorted[0].quantity * sorted[0].currentPrice +
        sorted[1].quantity * sorted[1].currentPrice
      : sorted[0]
        ? sorted[0].quantity * sorted[0].currentPrice
        : 0;

  const concentration = totalValue > 0 ? (top2Value / totalValue) * 100 : 0;

  const totalPL = portfolio.holdings.reduce(
    (sum, h) => sum + (h.currentPrice - h.avgPrice) * h.quantity,
    0,
  );

  const totalCost = portfolio.holdings.reduce(
    (sum, h) => sum + h.avgPrice * h.quantity,
    0,
  );

  const pnlPercent = totalCost > 0 ? (totalPL / totalCost) * 100 : 0;
  const totalInvested = totalCost;

  const worst =
    portfolio.holdings.length > 0
      ? portfolio.holdings.reduce((a, b) =>
          a.currentPrice - a.avgPrice < b.currentPrice - b.avgPrice ? a : b,
        )
      : undefined;

  return {
    sorted,
    concentration,
    pnlPercent,
    totalInvested,
    totalValue,
    top: sorted[0],
    second: sorted[1],
    worst,
  };
}

function getSignal(
  symbol: string,
  signals: typeof stockSignals,
): StockSignal | null {
  return signals[symbol as keyof typeof signals] ?? null;
}

function rawStockBias(
  signal: StockSignal | null,
): "buy" | "sell" | "hold" {
  if (!signal) return "hold";
  if (signal.trend === "up" && signal.strength === "strong") return "buy";
  if (signal.trend === "down" && signal.strength === "weak") return "sell";
  return "hold";
}

function toStockSuggestion(
  bias: "buy" | "sell" | "hold",
  concentration: number,
): StockSuggestion {
  if (bias === "sell") return "reduce";
  if (bias === "buy" && concentration <= 60) return "add";
  return "hold";
}

function stockReason(
  symbol: string,
  signal: StockSignal | null,
  suggestion: StockSuggestion,
  concentration: number,
): string {
  if (suggestion === "reduce") {
    return `${symbol} is under pressure — reducing exposure may help balance risk.`;
  }
  if (suggestion === "add") {
    return `${symbol} is showing strength — worth adding carefully if it fits your plan.`;
  }
  if (concentration > 60 && signal && rawStockBias(signal) === "buy") {
    return `${symbol} looks fine on its own, but your portfolio is already concentrated elsewhere.`;
  }
  return `${symbol} is stable — no strong reason to change course right now.`;
}

function stockPriority(suggestion: StockSuggestion): number {
  if (suggestion === "reduce") return 3;
  if (suggestion === "add") return 2;
  return 1;
}

function buildAffectedStocks(
  portfolio: Portfolio,
  signals: typeof stockSignals,
  concentration: number,
): AffectedStock[] {
  return portfolio.holdings
    .map((holding) => {
      const signal = getSignal(holding.symbol, signals);
      const bias = rawStockBias(signal);
      const suggestion = toStockSuggestion(bias, concentration);
      const weight =
        portfolio.holdings.reduce(
          (sum, h) => sum + h.quantity * h.currentPrice,
          0,
        ) > 0
          ? (holding.quantity * holding.currentPrice) /
            portfolio.holdings.reduce(
              (sum, h) => sum + h.quantity * h.currentPrice,
              0,
            )
          : 0;

      return {
        symbol: holding.symbol,
        suggestion,
        reason: stockReason(holding.symbol, signal, suggestion, concentration),
        weight,
      };
    })
    .sort((a, b) => stockPriority(b.suggestion) - stockPriority(a.suggestion));
}

function getInvestableSurplus(profile: FinancialProfile): number {
  const surplus =
    getIncomeMidpoint(profile.incomeRange) -
    getExpenseMidpoint(profile.expenseRange);
  return Math.max(0, surplus);
}

function getUtilizationLevel(
  totalInvested: number,
  monthlySurplus: number,
): FinancialContext["utilizationLevel"] {
  if (monthlySurplus <= 0) return "over";
  if (totalInvested === 0) return "under";

  const yearsOfSurplus = totalInvested / (monthlySurplus * 12);
  if (yearsOfSurplus < 0.75) return "under";
  if (yearsOfSurplus > 1.5) return "over";
  return "optimal";
}

function buildFinancialContext(
  profile: FinancialProfile,
  metrics: PortfolioMetrics,
): FinancialContext {
  const investableSurplus = getInvestableSurplus(profile);
  const utilizationLevel = getUtilizationLevel(
    metrics.totalInvested,
    investableSurplus,
  );

  let message = "";

  if (investableSurplus <= 0) {
    message =
      "Your expenses look close to your income — investing lightly until there's breathing room may be wise.";
  } else if (utilizationLevel === "under") {
    message = `Based on your lifestyle, you could comfortably invest around ${formatRupee(investableSurplus)} per month — you're investing less than what you could.`;
  } else if (utilizationLevel === "optimal") {
    message = `You're already allocating well around ${formatRupee(investableSurplus)} per month — consistency will matter more now.`;
  } else {
    message =
      "Your invested capital looks heavy relative to your monthly surplus — balance matters as much as growth.";
  }

  return { investableSurplus, utilizationLevel, message };
}

function buildBehavioralInsight(history: SessionHistory): string | undefined {
  const isRevisit =
    history.visitCount > 1 ||
    history.pastDecisions.length > 0 ||
    Boolean(history.lastReviewedStock);

  if (history.pastDecisions.length > 3) {
    return "You tend to review frequently — staying consistent may help more than timing the market.";
  }

  if (isRevisit) {
    return "You're building a good habit — reviewing consistently matters more than timing the market.";
  }

  if (history.lastReviewedStock) {
    return `We were looking at ${history.lastReviewedStock} last time — picking up where you left off could help.`;
  }

  return undefined;
}

function sessionClosingForTone(tone: MentorTone): string {
  switch (tone) {
    case "concerned":
      return "That's enough for today — rest easy knowing we've flagged what matters. Come back tomorrow and we'll continue.";
    case "encouraging":
      return "You showed up today — that counts. Come back tomorrow and we'll keep building on this.";
    case "observational":
      return "That's all for today — sit with what you noticed. Come back tomorrow and we'll see what's changed.";
    default:
      return "That's all for today — no need to overthink. Come back tomorrow and we'll take the next step.";
  }
}

function buildSummary(
  action: MentorAction,
  metrics: PortfolioMetrics,
  tone: MentorTone,
): string {
  const { concentration, pnlPercent } = metrics;

  if (concentration > 60) {
    return "You're slightly concentrated — I'd reduce a bit before adding more.";
  }

  if (pnlPercent < -10) {
    return tone === "encouraging"
      ? "It's been a tough stretch — let's review calmly before changing anything."
      : "Your portfolio needs attention — let's slow down before making changes.";
  }

  if (action === "add") {
    return "You have room to invest more — small, steady steps beat big bets.";
  }

  if (action === "reduce") {
    return "A few positions need a closer look — trimming exposure may help.";
  }

  if (action === "hold") {
    return "I'd stay steady for now — nothing needs a rushed response.";
  }

  return "Things look steady — I'd observe and stay patient for now.";
}

export function generateMentorDecision(input: MentorBrainInput): MentorDecision {
  const signals = input.stockSignals ?? stockSignals;
  const metrics = getPortfolioMetrics(input.portfolio);
  const affectedStocks = buildAffectedStocks(
    input.portfolio,
    signals,
    metrics.concentration,
  );
  const tone = input.mentorTone ?? "calm";

  const highRisk =
    metrics.concentration > 60 || metrics.pnlPercent < -10;
  const moderateRisk =
    metrics.concentration > 40 || metrics.pnlPercent < -5;

  let action: MentorAction = "observe";
  let urgency: MentorUrgency = "low";
  let confidence: MentorConfidence = "medium";
  let focusArea: MentorFocusArea = "portfolio";
  let primaryInsight = "Your portfolio looks reasonably balanced for now.";
  const reasoning: string[] = [];

  const financialContext = input.financialProfile
    ? buildFinancialContext(input.financialProfile, metrics)
    : undefined;

  const topReduce = affectedStocks.find((s) => s.suggestion === "reduce");
  const topAdd = affectedStocks.find((s) => s.suggestion === "add");

  // Priority 1: Risk overrides everything
  if (metrics.concentration > 60) {
    action = "reduce";
    urgency = "high";
    confidence = "high";
    focusArea = "risk";

    const topNames =
      metrics.top && metrics.second
        ? `${metrics.top.symbol} and ${metrics.second.symbol}`
        : metrics.top?.symbol ?? "a few positions";

    primaryInsight = `Your portfolio is concentrated — ${topNames} carry most of your weight.`;

    reasoning.push(
      "Overexposure to a few stocks can quietly increase risk even when returns look fine.",
    );
    reasoning.push(
      "If left as is, your portfolio could become overly dependent on a single stock.",
    );
    reasoning.push(
      "If you were to act, you might consider gradually balancing this over time — no urgency.",
    );
  } else if (metrics.pnlPercent < -10) {
    action = "reduce";
    urgency = "high";
    confidence = "high";
    focusArea = "risk";

    primaryInsight =
      "Your portfolio has been under pressure — rushing decisions often makes things worse.";

    if (metrics.worst) {
      reasoning.push(
        `${metrics.worst.symbol} has been the toughest spot — that's a sensible place to start reviewing.`,
      );
    }

    reasoning.push(
      "When a portfolio is under pressure, pausing to review helps you stay in control.",
    );
    reasoning.push(
      "If you were to act, revisiting your weakest positions calmly might help — no rush.",
    );
  }
  // Priority 2: Financial mismatch
  else if (
    financialContext &&
    financialContext.utilizationLevel === "under" &&
    financialContext.investableSurplus > 0
  ) {
    action = "add";
    urgency = "medium";
    confidence = "medium";
    focusArea = "behavior";

    primaryInsight =
      "You're investing less than what your current lifestyle could support.";

    reasoning.push(financialContext.message);
    reasoning.push(
      "Consistency matters more than timing — small monthly steps compound over time.",
    );
  }
  // Priority 3: Strong opportunities (risk controlled)
  else if (topAdd && !highRisk) {
    action = "add";
    urgency = "low";
    confidence = "high";
    focusArea = "opportunity";

    primaryInsight = `${topAdd.symbol} stands out as a careful add candidate if it fits your plan.`;
    reasoning.push(topAdd.reason);

    if (metrics.concentration > 40) {
      reasoning.push(
        "Even though your overall returns look stable, concentration is worth watching as you add.",
      );
    }
  }
  // Priority 4: Reduce on weak stock without full portfolio crisis
  else if (topReduce && moderateRisk) {
    action = "reduce";
    urgency = "medium";
    confidence = "medium";
    focusArea = "stock";

    primaryInsight = `${topReduce.symbol} is under pressure — worth a calm review.`;
    reasoning.push(topReduce.reason);
  }
  // Default: hold or observe
  else {
    action = moderateRisk ? "hold" : "observe";
    urgency = moderateRisk ? "medium" : "low";
    confidence = moderateRisk ? "medium" : "low";
    focusArea = "portfolio";

    if (metrics.concentration > 40 && metrics.top) {
      primaryInsight = `Your exposure to ${metrics.top.symbol} is higher than usual compared to your other holdings.`;
      reasoning.push(
        "Even though your overall returns look stable, this concentration is quietly increasing risk.",
      );
    } else {
      primaryInsight =
        "Nothing urgent stands out — staying aware is enough for now.";
      reasoning.push(
        "Staying patient and observing the market may be the best approach for now.",
      );
    }
  }

  if (
    financialContext &&
    focusArea !== "behavior" &&
    financialContext.utilizationLevel === "optimal"
  ) {
    reasoning.push(financialContext.message);
  }

  reasoning.push(
    "This is something many investors overlook — you're already ahead by noticing it.",
  );

  const behavioralInsight = buildBehavioralInsight(input.sessionHistory);

  const continueWithSymbol =
    topReduce?.symbol ??
    topAdd?.symbol ??
    input.sessionHistory.lastReviewedStock ??
    metrics.top?.symbol;

  let nextStep = "Let's look at this together — one step at a time.";

  if (action === "reduce" && topReduce) {
    nextStep = `Let's look at ${topReduce.symbol} together and see if trimming exposure feels right.`;
  } else if (action === "add" && topAdd) {
    nextStep = `Let's look at ${topAdd.symbol} together — adding carefully only if it fits your plan.`;
  } else if (continueWithSymbol) {
    nextStep = `Let's look at ${continueWithSymbol} together when you're ready.`;
  }

  const summary = buildSummary(action, metrics, tone);

  // Session memory (deterministic side effect for continuity)
  if (action === "reduce" || action === "hold") {
    const symbol = metrics.top?.symbol;
    if (symbol) {
      const mappedAction = action === "reduce" ? "SELL" : "HOLD";
      const last = input.sessionHistory.pastDecisions.at(-1);
      if (
        !last ||
        last.symbol !== symbol ||
        last.action !== mappedAction
      ) {
        updateMemory({
          pastDecisions: [
            ...input.sessionHistory.pastDecisions,
            { symbol, action: mappedAction },
          ],
        });
      }
    }
  }

  const visibleStocks = affectedStocks.filter(
    (s) => s.suggestion !== "hold" || metrics.concentration > 40,
  );

  return {
    summary,
    action,
    urgency,
    confidence,
    focusArea,
    primaryInsight,
    reasoning,
    affectedStocks:
      visibleStocks.length > 0 ? visibleStocks.slice(0, 4) : undefined,
    financialContext,
    behavioralInsight,
    nextStep,
    sessionClosing: sessionClosingForTone(tone),
    continueWithSymbol,
  };
}
