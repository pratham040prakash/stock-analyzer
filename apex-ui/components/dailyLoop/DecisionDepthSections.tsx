"use client";

import type { ReactNode } from "react";
import type {
  DecisionDepth,
  ProtectAllocationInsight,
} from "@/lib/dailyLoop/decisionDepth";
import { convictionLabel } from "@/lib/dailyLoop/decisionDepth";

function BulletList({ items }: { items: string[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item} className="flex gap-2 text-[14px] leading-snug text-apex-text/90">
          <span className="text-apex-muted" aria-hidden>
            •
          </span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function DepthSection({
  title,
  delayMs,
  children,
}: {
  title: string;
  delayMs: number;
  children: ReactNode;
}) {
  return (
    <section
      className="animate-apex-fade-in space-y-3 border-t border-apex-border/20 pt-5"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <h2 className="text-[13px] font-medium tracking-wide text-apex-muted">
        {title}
      </h2>
      {children}
    </section>
  );
}

export function WhyThisDecisionSection({
  bullets,
  delayMs,
}: {
  bullets: string[];
  delayMs: number;
}) {
  return (
    <DepthSection title="Why this decision" delayMs={delayMs}>
      <BulletList items={bullets} />
    </DepthSection>
  );
}

export function WhatToWatchSection({
  items,
  delayMs,
}: {
  items: string[];
  delayMs: number;
}) {
  return (
    <DepthSection title="What to watch next" delayMs={delayMs}>
      <BulletList items={items} />
    </DepthSection>
  );
}

export function SystemContextSection({
  depth,
  delayMs,
}: {
  depth: DecisionDepth;
  delayMs: number;
}) {
  const conviction = convictionLabel(depth.systemContext.conviction);

  return (
    <DepthSection title="System context" delayMs={delayMs}>
      <div className="flex flex-wrap gap-x-5 gap-y-2 text-[13px] text-apex-text/90">
        <span>
          Confidence{" "}
          <span className="font-medium text-apex-text">
            {depth.systemContext.confidenceLevel}
          </span>
        </span>
        <span>
          Regime{" "}
          <span className="font-medium text-apex-text">
            {depth.systemContext.marketRegime}
          </span>
        </span>
        {conviction ? (
          <span>
            Conviction{" "}
            <span className="font-medium text-apex-text">{conviction}</span>
          </span>
        ) : null}
      </div>
    </DepthSection>
  );
}

export function ProtectAllocationSection({
  insight,
  delayMs,
}: {
  insight: ProtectAllocationInsight;
  delayMs: number;
}) {
  const label = insight.topSymbol ?? "Top holding";

  return (
    <DepthSection title="Allocation balance" delayMs={delayMs}>
      <div className="grid grid-cols-2 gap-3 text-[13px]">
        <div>
          <p className="text-apex-muted">Current</p>
          <p className="mt-1 font-medium tabular-nums text-apex-text">
            {label} · {insight.currentPct}%
          </p>
        </div>
        <div>
          <p className="text-apex-muted">Ideal</p>
          <p className="mt-1 font-medium tabular-nums text-apex-text">
            ≤ {insight.idealPct}% per name
          </p>
        </div>
      </div>
      <p className="text-[14px] leading-relaxed text-apex-text/85">
        {insight.sellExplanation}
      </p>
    </DepthSection>
  );
}

export function ExploreInterestingSection({
  setups,
  delayMs,
  showTitle = true,
}: {
  setups: string[];
  delayMs: number;
  showTitle?: boolean;
}) {
  const content = (
    <>
      {setups.length > 0 ? (
        <BulletList items={setups} />
      ) : (
        <p className="text-[14px] leading-relaxed text-apex-text/85">
          Nothing stands out sharply — mixed markets often reward patience.
        </p>
      )}
      <p className="text-[13px] font-medium text-blue-200/80">No action yet</p>
    </>
  );

  if (!showTitle) {
    return (
      <section
        className="animate-apex-fade-in space-y-3 border-t border-apex-border/20 pt-5"
        style={{ animationDelay: `${delayMs}ms` }}
      >
        {content}
      </section>
    );
  }

  return (
    <DepthSection title="What is interesting today" delayMs={delayMs}>
      {content}
    </DepthSection>
  );
}
