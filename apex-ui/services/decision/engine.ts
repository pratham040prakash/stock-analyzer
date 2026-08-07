import {
  getExpenseMidpoint,
  getIncomeMidpoint,
  getInvestableSurplus,
  type FinancialProfile,
} from "@/lib/financialProfile";
import type {
  DailyDecisionOutput,
  DailyDecisionType,
  DecisionEngineInput,
} from "@/types/decision";
import type { MentorDecision } from "@/types/mentorDecision";
import type { Holding } from "@/types/portfolio";

function clampConfidence(value: number): number {
  return Math.min(100, Math.max(0, Math.round(value)));
}

function getTopHoldingWeight(holdings: Holding[]): number {
  const totalValue = holdings.reduce(
    (sum, h) => sum + h.quantity * h.currentPrice,
    0,
  );

  if (totalValue <= 0 || holdings.length === 0) {
    return 0;
  }

  const topValue = Math.max(
    ...holdings.map((h) => h.quantity * h.currentPrice),
  );

  return (topValue / totalValue) * 100;
}

function expensesMeetOrExceedIncome(profile: FinancialProfile): boolean {
  return (
    getExpenseMidpoint(profile.expenseRange) >=
    getIncomeMidpoint(profile.incomeRange)
  );
}

function actionsForDecision(decision: DailyDecisionType): string[] {
  switch (decision) {
    case "WAIT":
      return [
        "Pause new investments until expenses are under control",
        "Focus on building a small emergency buffer first",
      ];
    case "BUY_MORE":
      return [
        "Invest your monthly surplus in steady, small steps",
        "Review your largest holdings before adding more",
      ];
    case "REDUCE":
      return [
        "Review your most overweight holding",
        "Consider trimming gradually — no need to rush",
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

function confidenceForDecision(
  decision: DailyDecisionType,
  mentor: MentorDecision | null | undefined,
  hasProfile: boolean,
): number {
  const base: Record<DailyDecisionType, number> = {
    WAIT: 88,
    BUY_MORE: 78,
    REDUCE: 82,
    HOLD: 70,
  };

  let confidence = base[decision];

  if (!hasProfile) {
    confidence -= 12;
  }

  if (mentorAligns(decision, mentor)) {
    confidence += 10;
  }

  if (mentor?.confidence === "high") {
    confidence += 4;
  } else if (mentor?.confidence === "low") {
    confidence -= 4;
  }

  return clampConfidence(confidence);
}

export function evaluateDailyDecision(
  input: DecisionEngineInput,
): DailyDecisionOutput {
  const { portfolioSnapshot, financialProfile, lastMentorOutput } = input;
  const hasProfile = Boolean(financialProfile);
  const topWeight = getTopHoldingWeight(portfolioSnapshot.holdings);

  let decision: DailyDecisionType = "HOLD";
  let reason =
    "Your portfolio looks balanced for now — staying steady is reasonable.";

  if (financialProfile && expensesMeetOrExceedIncome(financialProfile)) {
    decision = "WAIT";
    reason =
      "Your expenses look equal to or higher than income — pausing new investments may be wise.";
  } else if (financialProfile) {
    const surplus = getInvestableSurplus(financialProfile);
    const targetInvested = surplus * 9;

    if (surplus > 0 && portfolioSnapshot.total_value < targetInvested) {
      decision = "BUY_MORE";
      reason =
        "You have investable surplus and your portfolio is below a comfortable long-term level — steady investing could help.";
    } else if (topWeight > 50) {
      decision = "REDUCE";
      reason = `One stock carries about ${Math.round(topWeight)}% of your portfolio — reducing concentration may lower risk.`;
    }
  } else if (topWeight > 50) {
    decision = "REDUCE";
    reason = `One stock carries about ${Math.round(topWeight)}% of your portfolio — worth reviewing before adding more.`;
  }

  return {
    decision,
    confidence: confidenceForDecision(
      decision,
      lastMentorOutput,
      hasProfile,
    ),
    reason,
    actions: actionsForDecision(decision),
  };
}
