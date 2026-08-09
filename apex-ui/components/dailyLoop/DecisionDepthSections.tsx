"use client";

import type { ReactNode } from "react";
import type {
  DecisionDepth,
  ProtectAllocationInsight,
} from "@/lib/dailyLoop/decisionDepth";
import type {
  CapitalAction,
  CapitalDecision,
  ExploreSetup,
} from "@/lib/dailyLoop/capitalDecision";
import {
  EXPLORE_PIPELINE_EMPTY_BODY,
  EXPLORE_PIPELINE_EMPTY_HEADLINE,
} from "@/lib/dailyLoop/capitalDecision";
import {
  DAILY_CLOSURE_BODY,
  DAILY_CLOSURE_HEADLINE,
  DAILY_CLOSURE_NEXT_STEP,
} from "@/lib/dailyLoop/disciplineStreak";
import type { SetupInsight } from "@/lib/dailyLoop/setupInsight";
import { convictionLabel } from "@/lib/dailyLoop/decisionDepth";
import {
  EXPLORE_EMPTY_BODY,
  EXPLORE_EMPTY_HEADLINE,
  formatJudgment,
  voiceConfidenceContext,
} from "@/lib/dailyLoop/apexVoice";

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
  const line = voiceConfidenceContext(
    depth.systemContext.confidenceLevel,
    depth.systemContext.marketRegime,
    Boolean(conviction),
  );

  return (
    <TierBlock tier="context" delayMs={delayMs}>
      <p className="text-xs text-apex-muted">{line}</p>
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
        {reason ??
          formatJudgment("Nothing is clean enough to risk capital", "patience matters")}
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
          {formatJudgment("Portfolio risk is elevated", "avoid for now")}
        </p>
      ) : null}
    </TierBlock>
  );
}

export function CapitalActionsBlock({
  decision,
  delayMs,
}: {
  decision: CapitalDecision;
  delayMs: number;
}) {
  if (decision.mode === "explore") {
    return <ExploreMonitoringBlock decision={decision} delayMs={delayMs} />;
  }

  return <GrowCapitalActionsBlock decision={decision} delayMs={delayMs} />;
}

function StancePrimaryHeader({ decision }: { decision: CapitalDecision }) {
  return (
    <>
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-apex-muted">
          Portfolio stance
        </p>
        <p className="text-sm font-medium leading-snug text-apex-text/90">
          {decision.portfolioStance}
        </p>
        <p className="text-sm leading-snug text-apex-text/75">
          {decision.portfolioStanceDetail}
        </p>
      </div>

      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-apex-muted">
          Primary action
        </p>
        <p className="text-base font-semibold leading-snug text-apex-text">
          {decision.primaryAction}
        </p>
        <p className="text-sm leading-snug text-apex-text/75">
          {decision.primaryActionDetail}
        </p>
      </div>
    </>
  );
}

function GrowCapitalActionsBlock({
  decision,
  delayMs,
}: {
  decision: CapitalDecision;
  delayMs: number;
}) {
  return (
    <TierBlock tier="primary" delayMs={delayMs}>
      <div className="space-y-4">
        <StancePrimaryHeader decision={decision} />

        {decision.growEmptyMessage ? (
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            {decision.growEmptyMessage}
          </p>
        ) : null}

        {decision.actions.length > 0 ? (
          <ul className="space-y-5 border-t border-apex-border/15 pt-4">
            {decision.actions.map((item) => (
              <CapitalActionRow key={item.symbol} action={item} />
            ))}
          </ul>
        ) : null}
      </div>
    </TierBlock>
  );
}

function ExploreMonitoringBlock({
  decision,
  delayMs,
}: {
  decision: CapitalDecision;
  delayMs: number;
}) {
  return (
    <TierBlock tier="primary" delayMs={delayMs}>
      <div className="space-y-4">
        <StancePrimaryHeader decision={decision} />

        {decision.explorePipelineSummary ? (
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            {decision.explorePipelineSummary}
          </p>
        ) : null}

        {decision.exploreSetups.length > 0 ? (
          <ul className="space-y-5 border-t border-apex-border/15 pt-4">
            {decision.exploreSetups.map((item) => (
              <ExploreSetupRow key={item.symbol} setup={item} />
            ))}
          </ul>
        ) : (
          <div className="border-t border-apex-border/15 pt-4">
            <p className="text-lg font-medium leading-snug text-apex-text">
              {EXPLORE_PIPELINE_EMPTY_HEADLINE}
            </p>
            <p className="mt-2 text-sm leading-snug text-apex-text/75">
              {EXPLORE_PIPELINE_EMPTY_BODY}
            </p>
          </div>
        )}
      </div>
    </TierBlock>
  );
}

function ExploreSetupRow({ setup }: { setup: ExploreSetup }) {
  const isHighlighted =
    setup.priorityMarker === "Closest to activation" || setup.isPrimary;

  return (
    <li
      className={
        isHighlighted
          ? "rounded-lg border border-apex-border/20 bg-white/[0.02] p-3"
          : undefined
      }
    >
      <p className="text-lg font-semibold leading-snug text-apex-text">
        {setup.symbol}
        {setup.priorityMarker ? (
          <span className="ml-2 text-xs font-medium uppercase tracking-wide text-blue-200/80">
            {setup.priorityMarker}
          </span>
        ) : null}
      </p>
      <p className="mt-1 text-sm leading-snug text-apex-text/85">
        Stage: {setup.stage}
      </p>
      <p className="text-sm leading-snug text-apex-text/85">
        Setup: {setup.setupDescription}
      </p>
      <div className="mt-1 space-y-0.5 text-sm leading-snug text-apex-text/75">
        <p>Progress needed: {setup.progressDelta}</p>
        <p>Progress: {setup.progressLine}</p>
        {setup.whyThisMatters ? (
          <p>Why this matters: {setup.whyThisMatters}</p>
        ) : null}
        <p>Activation: {setup.activation}</p>
        <p>Time horizon: {setup.timeHorizon}</p>
      </div>
    </li>
  );
}

function CapitalActionRow({ action }: { action: CapitalAction }) {
  return (
    <li
      className={
        action.isPrimary
          ? "rounded-lg border border-apex-border/20 bg-white/[0.02] p-3"
          : undefined
      }
    >
      <p className="text-lg font-semibold leading-snug text-apex-text">
        {action.symbol}
        {action.isPrimary ? (
          <span className="ml-2 text-xs font-medium uppercase tracking-wide text-apex-muted">
            Primary
          </span>
        ) : null}
      </p>
      <p className="mt-1 text-sm leading-snug text-apex-text/85">
        Action: {action.action}
      </p>
      <p className="text-sm leading-snug text-apex-text/85">{action.deployLabel}</p>
      {action.stage ? (
        <p className="text-sm leading-snug text-apex-text/85">
          Stage: {action.stage}
        </p>
      ) : null}
      <div className="mt-1 space-y-0.5 text-sm leading-snug text-apex-text/75">
        <p>Reason:</p>
        {action.missing ? <p>Missing: {action.missing}</p> : null}
        {action.confirm ? <p>Confirm: {action.confirm}</p> : null}
        {action.timing ? <p>Timing: {action.timing}</p> : null}
        {action.ifIgnored ? <p>{action.ifIgnored}</p> : null}
      </div>
      {action.postActionImpact ? (
        <p className="mt-2 text-sm leading-snug text-apex-text/80">
          {action.postActionImpact}
        </p>
      ) : null}
    </li>
  );
}

export function ExecutionStatusBlock({
  committedToday,
  onMarkFollowed,
  streakMessage,
  pressureLine,
  waitDisciplineReward,
  rewardHook,
  delayMs,
}: {
  committedToday: boolean;
  onMarkFollowed: () => void;
  streakMessage: string;
  pressureLine: string | null;
  waitDisciplineReward: string | null;
  rewardHook: string | null;
  delayMs: number;
}) {
  return (
    <section
      className="mt-5 space-y-3 animate-apex-fade-in"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-apex-muted">
          Execution status
        </p>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-6">
          <p
            className={[
              "text-sm leading-snug",
              committedToday ? "text-apex-muted/45" : "font-medium text-apex-text/90",
            ].join(" ")}
          >
            [ ] Not acted
          </p>
          {committedToday ? (
            <p className="text-sm font-medium leading-snug text-emerald-300/90">
              [✓] Followed today
            </p>
          ) : (
            <button
              type="button"
              onClick={onMarkFollowed}
              className="text-left text-sm leading-snug text-apex-text/85 transition-transform duration-150 hover:text-apex-text active:scale-[0.98]"
            >
              [ ] Followed today
            </button>
          )}
        </div>
      </div>

      <p className="text-sm text-apex-text/80">{streakMessage}</p>

      {committedToday ? (
        <div className="space-y-2 rounded-lg border border-apex-border/15 bg-white/[0.02] px-4 py-3">
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            {DAILY_CLOSURE_HEADLINE}
          </p>
          <p className="text-sm leading-snug text-apex-text/75">
            {DAILY_CLOSURE_BODY}
          </p>
          <p className="text-xs leading-snug text-apex-muted/70">
            {DAILY_CLOSURE_NEXT_STEP}
          </p>
        </div>
      ) : (
        <>
          {pressureLine ? (
            <p className="text-xs text-apex-muted/80">{pressureLine}</p>
          ) : null}

          {waitDisciplineReward ? (
            <p className="text-sm leading-snug text-apex-text/75">
              {waitDisciplineReward}
            </p>
          ) : null}

          {rewardHook ? (
            <p className="text-xs text-apex-muted/60">{rewardHook}</p>
          ) : null}
        </>
      )}
    </section>
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
              {item.line2 ? (
                <p className="mt-0.5 text-sm leading-snug text-apex-text/75">
                  {item.line2}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <div>
          <p className="text-lg font-medium leading-snug text-apex-text">
            {EXPLORE_EMPTY_HEADLINE}
          </p>
          <p className="mt-2 text-sm leading-snug text-apex-text/75">
            {EXPLORE_EMPTY_BODY}
          </p>
        </div>
      )}
      <p className="mt-3 text-sm text-blue-200/75">
        {formatJudgment("Observation only", "patience matters")}
      </p>
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
        line1: "Trend is developing. Momentum is picking up.",
        line2: formatJudgment("Setup is taking shape", "not ready yet"),
        ending: "not ready yet" as const,
        format: "split" as const,
      }))}
      delayMs={delayMs}
    />
  );
}
