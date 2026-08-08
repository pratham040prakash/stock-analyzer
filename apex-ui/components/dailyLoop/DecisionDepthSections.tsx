"use client";

import type { ReactNode } from "react";
import type {
  DecisionDepth,
  ProtectAllocationInsight,
} from "@/lib/dailyLoop/decisionDepth";
import type { SetupInsight } from "@/lib/dailyLoop/setupInsight";
import { convictionLabel } from "@/lib/dailyLoop/decisionDepth";

type SectionTier = "primary" | "support" | "context" | "background";

const TIER_CLASS: Record<SectionTier, string> = {
  primary: "mb-5 animate-apex-fade-in",
  support: "mb-3 space-y-2 animate-apex-fade-in",
  context: "mt-4 opacity-60 animate-apex-fade-in",
  background: "mt-6 space-y-2 animate-apex-fade-in",
};

export function PrimaryEmphasis({ children }: { children: ReactNode }) {
  return (
    <div className="space-y-3 rounded-xl bg-white/[0.03] p-4 transition-all duration-200 hover:scale-[1.01]">
      {children}
    </div>
  );
}

function TierBlock({
  tier,
  delayMs,
  children,
  className = "",
}: {
  tier: SectionTier;
  delayMs: number;
  children: ReactNode;
  className?: string;
}) {
  const body =
    tier === "primary" ? <PrimaryEmphasis>{children}</PrimaryEmphasis> : children;

  return (
    <section
      className={[TIER_CLASS[tier], className].filter(Boolean).join(" ")}
      style={{ animationDelay: `${delayMs}ms` }}
    >
      {body}
    </section>
  );
}

function SupportLabel({ children }: { children: ReactNode }) {
  return (
    <p className="text-sm font-medium text-apex-muted">{children}</p>
  );
}

function BulletList({ items }: { items: string[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <ul className="space-y-1.5">
      {items.map((item) => (
        <li key={item} className="flex gap-2 text-sm leading-snug text-apex-text/85">
          <span className="text-apex-muted/70" aria-hidden>
            •
          </span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function WhySection({
  bullets,
  delayMs,
}: {
  bullets: string[];
  delayMs: number;
}) {
  if (bullets.length === 0) {
    return null;
  }

  return (
    <TierBlock tier="support" delayMs={delayMs}>
      <SupportLabel>Why</SupportLabel>
      <BulletList items={bullets} />
    </TierBlock>
  );
}

export function WatchSection({
  items,
  delayMs,
}: {
  items: string[];
  delayMs: number;
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <TierBlock tier="support" delayMs={delayMs}>
      <SupportLabel>Watch</SupportLabel>
      <BulletList items={items} />
    </TierBlock>
  );
}

export function SystemContextLine({
  depth,
  delayMs,
}: {
  depth: DecisionDepth;
  delayMs: number;
}) {
  const conviction = convictionLabel(depth.systemContext.conviction);
  const parts = [
    `${depth.systemContext.confidenceLevel} confidence`,
    `${depth.systemContext.marketRegime} regime`,
  ];

  if (conviction) {
    parts.push(`${conviction} conviction`);
  }

  return (
    <TierBlock tier="context" delayMs={delayMs}>
      <p className="text-xs text-apex-muted">{parts.join(" · ")}</p>
    </TierBlock>
  );
}

export function ProtectPrimaryBlock({
  reason,
  riskElevated,
  insight,
  delayMs,
}: {
  reason?: string;
  riskElevated: boolean;
  insight?: ProtectAllocationInsight;
  delayMs: number;
}) {
  return (
    <TierBlock tier="primary" delayMs={delayMs}>
      <p className="text-lg font-medium leading-snug text-apex-text">
        {reason ?? "Conditions are not strong enough to risk capital today."}
      </p>
      {insight ? (
        <div className="space-y-2 text-sm text-apex-text/85">
          <p>
            <span className="font-medium text-apex-text">
              {insight.topSymbol ?? "Top holding"}
            </span>
            {" · "}
            {insight.currentPct}% now → ideal ≤ {insight.idealPct}%
          </p>
          <p>{insight.sellExplanation}</p>
        </div>
      ) : null}
      {riskElevated ? (
        <p className="text-sm text-amber-200/80">
          Portfolio risk is elevated — protecting capital comes first.
        </p>
      ) : null}
    </TierBlock>
  );
}

export function ExplorePrimaryBlock({
  setupItems,
  delayMs,
}: {
  setupItems: SetupInsight[];
  delayMs: number;
}) {
  return (
    <TierBlock tier="primary" delayMs={delayMs}>
      {setupItems.length > 0 ? (
        <ul className="space-y-5">
          {setupItems.map((item) => (
            <li key={item.title}>
              <p className="text-lg font-semibold leading-snug text-apex-text">
                {item.title}
              </p>
              <p className="mt-1 text-sm font-medium leading-snug text-apex-text/90">
                {item.line1}
              </p>
              <p className="mt-0.5 text-sm leading-snug text-apex-text/75">
                {item.line2}
              </p>
              <p className="mt-1 text-xs text-apex-muted">{item.tag}</p>
            </li>
          ))}
        </ul>
      ) : (
        <div>
          <p className="text-lg font-medium leading-snug text-apex-text/90">
            Nothing stands out sharply
          </p>
          <p className="mt-1 text-sm text-apex-text/75">
            Mixed markets often reward patience over action.
          </p>
          <p className="mt-1 text-xs text-apex-muted">Wait</p>
        </div>
      )}
      <p className="text-sm text-blue-200/75">No action yet</p>
    </TierBlock>
  );
}

export function BackgroundNote({
  text,
  delayMs,
}: {
  text: string;
  delayMs: number;
}) {
  return (
    <TierBlock tier="background" delayMs={delayMs}>
      <p className="text-sm leading-relaxed text-apex-text/75">{text}</p>
    </TierBlock>
  );
}

/** @deprecated Use WhySection */
export const WhyThisDecisionSection = WhySection;

/** @deprecated Use WatchSection */
export const WhatToWatchSection = WatchSection;

/** @deprecated Use SystemContextLine */
export const SystemContextSection = SystemContextLine;

/** @deprecated Use ProtectPrimaryBlock */
export function ProtectAllocationSection({
  insight,
  delayMs,
}: {
  insight: ProtectAllocationInsight;
  delayMs: number;
}) {
  return (
    <ProtectPrimaryBlock
      insight={insight}
      riskElevated={false}
      delayMs={delayMs}
    />
  );
}

/** @deprecated Use ExplorePrimaryBlock */
export function ExploreInterestingSection({
  setups,
  delayMs,
}: {
  setups: string[];
  delayMs: number;
  showTitle?: boolean;
}) {
  return (
    <ExplorePrimaryBlock
      setupItems={setups.map((title) => ({
        title,
        line1: "Developing trend with building momentum",
        line2: "Reasonable setup",
        tag: "Early" as const,
      }))}
      delayMs={delayMs}
    />
  );
}
