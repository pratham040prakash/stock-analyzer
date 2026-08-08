"use client";

import { formatInr } from "@/lib/funds";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  ApexBadge,
  ApexBody,
  ApexButton,
  ApexCard,
  ApexInsight,
  ApexRow,
  ApexSection,
  ApexTitle,
} from "@/components/ui/apex";

export type HomeDecision = {
  action: DecisionActionType | string;
  stock?: string;
  amount?: number;
  confidence?: number;
  structureScore?: number;
  confidenceMetrics?: {
    expectedReturn?: number;
  };
};

export type HomePortfolioSnapshot = {
  value: number;
  cash: number;
};

export type HomeDecisionScreenProps = {
  decision: HomeDecision;
  entryTiming: EntryTimingState;
  portfolio: HomePortfolioSnapshot;
  onViewExecutionPlan?: () => void;
  className?: string;
};

type StatusChip = {
  label: "WAITING" | "READY" | "NO TRADE";
  tone: "waiting" | "success" | "neutral";
};

function heroText(decision: HomeDecision, entryTiming: EntryTimingState): string {
  const action = decision.action;
  const stock = decision.stock ?? "your holding";
  const amount = decision.amount ?? 0;
  const amountLabel = amount > 0 ? formatInr(amount) : "your planned amount";

  if (action === "buy") {
    const prefix = entryTiming.enter ? "Invest" : "Prepare to invest";
    return `${prefix} ${amountLabel} in ${stock}`;
  }

  if (action === "wait") {
    return "Do nothing today";
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return `Exit position in ${stock}`;
  }

  if (action === "explore") {
    return "Explore opportunities today";
  }

  return "Hold steady today";
}

function mentorSubtext(
  decision: HomeDecision,
  entryTiming: EntryTimingState,
): string {
  const action = decision.action;

  if (action === "buy") {
    return entryTiming.enter
      ? "Opportunity identified — execute with discipline"
      : "Conditions are not ready yet — wait for confirmation";
  }

  if (action === "wait") {
    return "No strong opportunities today — capital is safe";
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return "Protect capital by reducing exposure when risk is elevated";
  }

  return "Stay patient — your plan is still on track";
}

function statusChip(
  decision: HomeDecision,
  entryTiming: EntryTimingState,
): StatusChip {
  const action = decision.action;

  if (action === "wait" || action === "hold") {
    return { label: "NO TRADE", tone: "neutral" };
  }

  if (action === "buy") {
    return entryTiming.enter
      ? { label: "READY", tone: "success" }
      : { label: "WAITING", tone: "waiting" };
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return { label: "READY", tone: "success" };
  }

  return { label: "NO TRADE", tone: "neutral" };
}

function buildWhyBullets(decision: HomeDecision): string[] {
  const bullets: string[] = [];

  if ((decision.confidence ?? 0) >= 65) {
    bullets.push("Strong trend");
  }

  if ((decision.structureScore ?? 0) >= 55) {
    bullets.push("Good market structure");
  }

  if ((decision.confidenceMetrics?.expectedReturn ?? 0) > 0) {
    bullets.push("Positive expected return");
  }

  if (bullets.length === 0) {
    return [
      "Balanced risk profile",
      "Capital preservation first",
      "Wait for clearer alignment",
    ];
  }

  while (bullets.length < 3) {
    if (!bullets.includes("Positive expected return")) {
      bullets.push("Positive expected return");
    } else if (!bullets.includes("Good market structure")) {
      bullets.push("Good market structure");
    } else {
      bullets.push("Disciplined execution");
    }
  }

  return bullets.slice(0, 3);
}

export default function HomeDecisionScreen({
  decision,
  entryTiming,
  portfolio,
  onViewExecutionPlan,
  className = "",
}: HomeDecisionScreenProps) {
  const headline = heroText(decision, entryTiming);
  const subtext = mentorSubtext(decision, entryTiming);
  const chip = statusChip(decision, entryTiming);
  const whyBullets = buildWhyBullets(decision);
  const canViewPlan = decision.action === "buy";

  return (
    <div className={className}>
      <ApexCard>
        <div className="mb-5">
          <ApexBadge tone={chip.tone}>{chip.label}</ApexBadge>
        </div>

        <ApexTitle>{headline}</ApexTitle>
        <ApexBody className="mt-3">{subtext}</ApexBody>

        <ApexInsight title="Why this decision?" className="mt-6">
          <ul className="space-y-2">
            {whyBullets.map((bullet) => (
              <li
                key={bullet}
                className="flex gap-2 text-[13px] text-blue-100/75"
              >
                <span className="text-blue-400/90">•</span>
                {bullet}
              </li>
            ))}
          </ul>
        </ApexInsight>

        <ApexSection className="mt-5 rounded-xl border border-apex-border px-4">
          <ApexRow label="Portfolio" value={formatInr(portfolio.value)} />
          <ApexRow label="Cash" value={formatInr(portfolio.cash)} />
        </ApexSection>

        {decision.action === "buy" ? (
          <ApexButton
            className="mt-6"
            variant={canViewPlan ? "primary" : "secondary"}
            onClick={onViewExecutionPlan}
          >
            View Execution Plan
          </ApexButton>
        ) : null}
      </ApexCard>
    </div>
  );
}
