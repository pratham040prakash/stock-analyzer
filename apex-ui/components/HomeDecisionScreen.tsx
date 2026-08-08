"use client";

import { useEffect, useMemo, useState } from "react";
import { formatInr } from "@/lib/funds";
import { isSellAction, type DecisionActionType } from "@/types/decision";
import type { EntryTimingState } from "@/components/decision/ExecutionPlanCard";
import {
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

type MarketRegime = "Favorable" | "Neutral" | "Unfavorable";

type StrengthMetric = {
  label: string;
  value: number;
  interpretation: string;
};

const SIGNATURE_LINES = [
  "Most days, doing nothing is the edge.",
  "Discipline beats activity.",
  "Patience compounds.",
  "The best trade is often no trade.",
] as const;

const CHIP_TONE_CLASS: Record<StatusChip["tone"], string> = {
  success:
    "border-emerald-500/20 bg-emerald-500/10 text-emerald-300 shadow-[0_0_20px_rgba(16,185,129,0.08)]",
  waiting:
    "border-amber-500/20 bg-amber-500/10 text-amber-200 shadow-[0_0_20px_rgba(245,158,11,0.08)]",
  neutral:
    "border-white/20 bg-apex-bg/80 text-apex-muted shadow-[0_0_20px_rgba(156,163,175,0.08)]",
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
    return "Nothing today deserves your capital.";
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return "Reduce exposure now before risk compounds.";
  }

  if (action === "explore") {
    return "Worth watching — nothing to force today.";
  }

  return "Nothing today deserves your capital.";
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

function marketRegime(decision: HomeDecision, entryTiming: EntryTimingState): MarketRegime {
  const action = decision.action;

  if (action === "wait" || action === "hold") {
    return "Unfavorable";
  }

  if (action === "buy") {
    return entryTiming.enter ? "Favorable" : "Neutral";
  }

  if (isSellAction(action as DecisionActionType) || action === "sell") {
    return "Unfavorable";
  }

  const structure = decision.structureScore ?? 50;
  const confidence = decision.confidence ?? 50;
  const composite = (structure + confidence) / 2;

  if (composite >= 65) return "Favorable";
  if (composite >= 45) return "Neutral";
  return "Unfavorable";
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
      "Risk is higher than reward",
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
    "Risk is higher than reward",
  ];
}

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function probabilityInterpretation(value: number): string {
  if (value >= 75) return "Strong edge";
  if (value >= 60) return "Moderate edge";
  if (value >= 45) return "Limited edge";
  return "Weak edge";
}

function structureInterpretation(value: number): string {
  if (value >= 70) return "Strong";
  if (value >= 55) return "Acceptable";
  if (value >= 45) return "Not ideal";
  return "Weak";
}

function riskControlInterpretation(value: number): string {
  if (value >= 80) return "Strong";
  if (value >= 65) return "Solid";
  if (value >= 50) return "Moderate";
  return "Limited";
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
    {
      label: "Probability",
      value: probability,
      interpretation: probabilityInterpretation(probability),
    },
    {
      label: "Structure",
      value: structure,
      interpretation: structureInterpretation(structure),
    },
    {
      label: "Risk Control",
      value: riskControl,
      interpretation: riskControlInterpretation(riskControl),
    },
  ];
}

function strengthBar(filledSlots: number): string {
  const filled = Math.max(0, Math.min(10, filledSlots));
  return `${"█".repeat(filled)}${"░".repeat(10 - filled)}`;
}

function dailySignatureLine(): string {
  return SIGNATURE_LINES[new Date().getDate() % SIGNATURE_LINES.length];
}

function isNoTradeAction(action: string): boolean {
  return action === "wait" || action === "hold";
}

function LiveStatusChip({ chip }: { chip: StatusChip }) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1",
        "text-[10px] font-semibold uppercase tracking-wider",
        "animate-apex-chip-pulse",
        CHIP_TONE_CLASS[chip.tone],
      ].join(" ")}
    >
      {chip.label}
    </span>
  );
}

function InsightBullets({ bullets }: { bullets: string[] }) {
  return (
    <ul className="mt-3 space-y-2.5">
      {bullets.map((bullet, index) => (
        <li
          key={bullet}
          className="flex gap-2 text-[13px] leading-relaxed text-apex-muted animate-apex-bullet-in"
          style={{ animationDelay: `${index * 120}ms` }}
        >
          <span className="text-apex-muted/70">•</span>
          {bullet}
        </li>
      ))}
    </ul>
  );
}

function AnimatedStrengthRow({
  metric,
  index,
}: {
  metric: StrengthMetric;
  index: number;
}) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let frame = 0;
    const delay = index * 80;
    const duration = 600;

    setDisplayValue(0);

    const timer = window.setTimeout(() => {
      const start = performance.now();
      const tick = (now: number) => {
        const progress = Math.min(1, (now - start) / duration);
        setDisplayValue(Math.round(metric.value * progress));
        if (progress < 1) {
          frame = window.requestAnimationFrame(tick);
        }
      };
      frame = window.requestAnimationFrame(tick);
    }, delay);

    return () => {
      window.clearTimeout(timer);
      window.cancelAnimationFrame(frame);
    };
  }, [metric.value, index]);

  return (
    <li className="space-y-1">
      <div className="grid grid-cols-[5.5rem_1fr_2.5rem] items-center gap-3 text-[13px]">
        <span className="text-apex-muted">{metric.label}</span>
        <span className="font-mono text-[12px] tracking-tight text-apex-text/70">
          {strengthBar(Math.round(displayValue / 10))}
        </span>
        <span className="text-right text-apex-muted">{displayValue}%</span>
      </div>
      <p className="pl-[5.5rem] text-[11px] text-apex-muted/70">
        ({metric.interpretation})
      </p>
    </li>
  );
}

function DecisionStrength({ metrics }: { metrics: StrengthMetric[] }) {
  return (
    <section className="mt-8">
      <ApexEyebrow className="mb-4">Decision Strength</ApexEyebrow>
      <ul className="space-y-3">
        {metrics.map((metric, index) => (
          <AnimatedStrengthRow key={metric.label} metric={metric} index={index} />
        ))}
      </ul>
    </section>
  );
}

function StandByModal({
  open,
  onClose,
  bullets,
}: {
  open: boolean;
  onClose: () => void;
  bullets: string[];
}) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
      />
      <div
        role="dialog"
        aria-modal="true"
        className="relative w-full max-w-md rounded-2xl border border-apex-border/50 bg-apex-card p-6 shadow-2xl animate-apex-rise-in"
      >
        <p className="text-[13px] font-semibold text-apex-text">Standing by</p>
        <ApexBody className="mt-2">
          No action today. Capital stays protected until conditions improve.
        </ApexBody>
        <ul className="mt-4 space-y-2">
          {bullets.map((bullet) => (
            <li key={bullet} className="text-[13px] text-apex-muted">
              • {bullet}
            </li>
          ))}
        </ul>
        <ApexButton className="mt-6" variant="secondary" onClick={onClose}>
          Got it
        </ApexButton>
      </div>
    </div>
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
  const [standByOpen, setStandByOpen] = useState(false);
  const headline = heroText(decision, entryTiming);
  const subtext = mentorSubtext(decision, entryTiming);
  const chip = statusChip(decision, entryTiming);
  const regime = marketRegime(decision, entryTiming);
  const whyBullets = buildWhyBullets(decision);
  const strengthMetrics = buildDecisionStrength(decision);
  const signatureLine = useMemo(() => dailySignatureLine(), []);
  const canViewPlan = decision.action === "buy";
  const showStandBy = isNoTradeAction(decision.action);
  const allCapitalDeployed = portfolio.cash <= 0;

  return (
    <div className={`space-y-5 ${className}`.trim()}>
      <ApexCard
        hover={false}
        className="animate-apex-rise-in border-apex-border/50 shadow-none"
      >
        <div className="mb-5 space-y-3">
          <LiveStatusChip chip={chip} />
          <p className="text-[12px] text-apex-muted/80">
            Market regime: {regime}
          </p>
        </div>

        <ApexTitle className="animate-apex-fade-in text-[28px] tracking-[0.01em] sm:text-[30px]">
          {headline}
        </ApexTitle>
        <ApexBody
          className="mt-4 animate-apex-fade-in text-[15px] text-apex-text/80"
          style={{ animationDelay: "80ms" }}
        >
          {subtext}
        </ApexBody>

        <section className="mt-8 rounded-xl border border-apex-border/30 bg-apex-bg/30 px-4 py-4">
          <p className="text-[13px] font-semibold text-apex-text/90">
            Why this stands out
          </p>
          <InsightBullets bullets={whyBullets} />
        </section>

        <DecisionStrength metrics={strengthMetrics} />

        <div className="mt-8 space-y-2 border-t border-apex-border/30 pt-6">
          <div className="flex items-baseline justify-between gap-4 text-[14px]">
            <span className="text-apex-muted">Portfolio</span>
            <span className="font-medium text-apex-text">
              {formatInr(portfolio.value)}
            </span>
          </div>
          {allCapitalDeployed ? (
            <div className="flex items-baseline justify-between gap-4 text-[14px]">
              <span className="text-apex-muted">Status</span>
              <span className="font-medium text-apex-text/80">
                All capital deployed
              </span>
            </div>
          ) : (
            <div className="flex items-baseline justify-between gap-4 text-[14px]">
              <span className="text-apex-muted">Cash</span>
              <span className="font-medium text-apex-text">
                {formatInr(portfolio.cash)}
              </span>
            </div>
          )}
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

        {showStandBy ? (
          <ApexButton
            className="mt-8"
            variant="secondary"
            onClick={() => setStandByOpen(true)}
          >
            Stand by
          </ApexButton>
        ) : null}

        <p className="mt-8 text-center text-[11px] italic text-apex-muted/60">
          {signatureLine}
        </p>
      </ApexCard>

      <DailyDisciplineLoop updatedAt={updatedAt} />

      <StandByModal
        open={standByOpen}
        onClose={() => setStandByOpen(false)}
        bullets={whyBullets}
      />
    </div>
  );
}
