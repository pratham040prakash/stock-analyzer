"use client";

import { formatInr } from "@/lib/funds";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
  ApexBadge,
  ApexBody,
  ApexButton,
  ApexCard,
  ApexEyebrow,
  ApexTitle,
} from "@/components/ui/apex";
import DailyDisciplineLoop from "@/components/decision/DailyDisciplineLoop";

export type HomeDecision = {
  action: DecisionActionType | string;
  stock?: string;
  amount?: number;
  confidence?: number;
  structureScore?: number;
  confidenceMetrics?: {
    expectedReturn?: number;
    probability?: number;
    edgeScore?: number;
    expectedDrawdown?: number;
  };
  validation?: {
    risk_ok?: boolean;
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
  updatedAt?: string | null;
  onViewExecutionPlan?: () => void;
  className?: string;
};

type StatusChip = {
  label: "WAITING" | "READY" | "NO TRADE";
  tone: "waiting" | "success" | "neutral";
};

type StrengthMetric = {
  label: string;
  value: number;
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

  if (action === "wait" || action === "hold") {
    return "Stay in cash today.";
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return `Reduce ${stock} today.`;
  }

  if (action === "explore") {
    return "Watch the market today.";
  }

  return "Stay in cash today.";
}

function mentorSubtext(
  decision: HomeDecision,
  entryTiming: EntryTimingState,
): string {
  const action = decision.action;

  if (action === "buy") {
    return entryTiming.enter
      ? "This setup is worth acting on — move with discipline."
      : "The idea is sound. Wait for the market to confirm.";
  }

  if (action === "wait" || action === "hold") {
    return "Nothing in the market is worth your capital today.";
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return "Reduce exposure now before risk compounds.";
  }

  if (action === "explore") {
    return "Worth watching — nothing to force today.";
  }

  return "Nothing in the market is worth your capital today.";
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
  const action = decision.action;
  const confidence = decision.confidence ?? 0;
  const structure = decision.structureScore ?? 0;
  const expectedReturn = decision.confidenceMetrics?.expectedReturn ?? 0;

  if (action === "wait" || action === "hold") {
    return [
      "Setups are weak across the market",
      "Breakouts are failing to follow through",
      "Risk is higher than reward right now",
    ];
  }

  if (action === "buy") {
    const bullets: string[] = [];

    if (structure >= 55) {
      bullets.push("Price is holding above key levels");
    } else {
      bullets.push("Structure is still forming — patience required");
    }

    if (confidence >= 65) {
      bullets.push("Trend is pushing in your favor");
    } else {
      bullets.push("Conviction is building, not confirmed yet");
    }

    if (expectedReturn > 0) {
      bullets.push("Reward outweighs the downside from here");
    } else {
      bullets.push("Edge is present but still early");
    }

    return bullets.slice(0, 3);
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return [
      "Exposure has crept too high for comfort",
      "Downside pressure is building on this position",
      "Trimming now protects the rest of your portfolio",
    ];
  }

  if (action === "explore") {
    return [
      "A few names are worth tracking closely",
      "Nothing is ready for immediate action",
      "Patience keeps you ahead of the crowd",
    ];
  }

  return [
    "Setups are weak across the market",
    "Breakouts are failing to follow through",
    "Risk is higher than reward right now",
  ];
}

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function buildDecisionStrength(decision: HomeDecision): StrengthMetric[] {
  const metrics = decision.confidenceMetrics;
  const probability =
    metrics?.probability !== undefined
      ? clampPercent(metrics.probability * 100)
      : clampPercent(decision.confidence ?? 50);
  const structure = clampPercent(decision.structureScore ?? 50);

  let riskControl = 70;
  if (decision.validation?.risk_ok) {
    riskControl = 80;
  }
  if (metrics?.edgeScore !== undefined) {
    riskControl = clampPercent(metrics.edgeScore * 100);
  } else if (metrics?.expectedDrawdown !== undefined) {
    riskControl = clampPercent(100 - metrics.expectedDrawdown * 100);
  }

  return [
    { label: "Probability", value: probability },
    { label: "Structure", value: structure },
    { label: "Risk Control", value: riskControl },
  ];
}

function strengthBar(filledSlots: number): string {
  const filled = Math.max(0, Math.min(10, filledSlots));
  return `${"█".repeat(filled)}${"░".repeat(10 - filled)}`;
}

function DecisionStrength({ metrics }: { metrics: StrengthMetric[] }) {
  return (
    <section className="mt-8">
      <ApexEyebrow className="mb-4">Decision Strength</ApexEyebrow>
      <ul className="space-y-3">
        {metrics.map((metric) => (
          <li
            key={metric.label}
            className="grid grid-cols-[5.5rem_1fr_2.5rem] items-center gap-3 text-[13px]"
          >
            <span className="text-apex-muted">{metric.label}</span>
            <span className="font-mono text-[12px] tracking-tight text-apex-text/70">
              {strengthBar(Math.round(metric.value / 10))}
            </span>
            <span className="text-right text-apex-muted">{metric.value}%</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function HomeDecisionScreen({
  decision,
  entryTiming,
  portfolio,
  updatedAt,
  onViewExecutionPlan,
  className = "",
}: HomeDecisionScreenProps) {
  const headline = heroText(decision, entryTiming);
  const subtext = mentorSubtext(decision, entryTiming);
  const chip = statusChip(decision, entryTiming);
  const whyBullets = buildWhyBullets(decision);
  const strengthMetrics = buildDecisionStrength(decision);
  const canViewPlan = decision.action === "buy";

  return (
    <div className={`space-y-5 ${className}`.trim()}>
      <ApexCard hover={false} className="border-apex-border/50 shadow-none">
        <div className="mb-6">
          <ApexBadge tone={chip.tone}>{chip.label}</ApexBadge>
        </div>

        <ApexTitle className="text-[28px] sm:text-[30px]">{headline}</ApexTitle>
        <ApexBody className="mt-4 text-[15px] text-apex-text/80">
          {subtext}
        </ApexBody>

        <section className="mt-8 rounded-xl border border-apex-border/40 bg-apex-bg/30 px-4 py-4">
          <p className="text-[13px] font-semibold text-apex-text/90">
            Why this stands out
          </p>
          <ul className="mt-3 space-y-2.5">
            {whyBullets.map((bullet) => (
              <li
                key={bullet}
                className="flex gap-2 text-[13px] leading-relaxed text-apex-muted"
              >
                <span className="text-apex-muted/70">•</span>
                {bullet}
              </li>
            ))}
          </ul>
        </section>

        <DecisionStrength metrics={strengthMetrics} />

        <div className="mt-8 space-y-2 border-t border-apex-border/40 pt-6">
          <div className="flex items-baseline justify-between gap-4 text-[14px]">
            <span className="text-apex-muted">Portfolio</span>
            <span className="font-medium text-apex-text">
              {formatInr(portfolio.value)}
            </span>
          </div>
          <div className="flex items-baseline justify-between gap-4 text-[14px]">
            <span className="text-apex-muted">Cash</span>
            <span className="font-medium text-apex-text">
              {formatInr(portfolio.cash)}
            </span>
          </div>
        </div>

        {decision.action === "buy" ? (
          <ApexButton
            className="mt-8"
            variant={canViewPlan ? "primary" : "secondary"}
            onClick={onViewExecutionPlan}
          >
            View Execution Plan
          </ApexButton>
        ) : null}

        <p className="mt-8 text-center text-[12px] italic text-apex-muted/80">
          Most days, doing nothing is the edge.
        </p>
      </ApexCard>

      <DailyDisciplineLoop updatedAt={updatedAt} />
    </div>
  );
}
