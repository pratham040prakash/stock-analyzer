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
import type { ExploreLiveTrigger } from "@/services/explore/liveTriggers";
import {
  EXPLORE_PIPELINE_EMPTY_BODY,
  EXPLORE_PIPELINE_EMPTY_HEADLINE,
  buildTrustReinforcement,
  formatGrowActionStage,
} from "@/lib/dailyLoop/capitalDecision";
import { formatFinalStateSummary } from "@/lib/dailyLoop/capitalFinalState";
import { formatInr } from "@/lib/funds";
import {
  DAILY_CLOSURE_HEADLINE,
  DAILY_CLOSURE_NEXT_STEP,
  getDailyClosureBody,
} from "@/lib/dailyLoop/disciplineStreak";
import type { TodayExecutionKind } from "@/lib/dailyLoop/todaySurface";
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
  depthOnly = false,
  liveTriggers,
  liveTriggersLoading = false,
}: {
  decision: CapitalDecision;
  delayMs: number;
  depthOnly?: boolean;
  liveTriggers?: Map<string, ExploreLiveTrigger>;
  liveTriggersLoading?: boolean;
}) {
  if (decision.mode === "explore") {
    return (
      <ExploreMonitoringBlock
        decision={decision}
        delayMs={delayMs}
        liveTriggers={liveTriggers}
        liveTriggersLoading={liveTriggersLoading}
      />
    );
  }

  return (
    <GrowCapitalActionsBlock
      decision={decision}
      delayMs={delayMs}
      depthOnly={depthOnly}
    />
  );
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
  depthOnly = false,
}: {
  decision: CapitalDecision;
  delayMs: number;
  depthOnly?: boolean;
}) {
  return (
    <section
      className="space-y-8 animate-apex-fade-in"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      {!depthOnly ? (
        <div className="space-y-1">
          <p className="text-sm font-medium leading-snug text-apex-text">
            {decision.portfolioStance}
          </p>
          <p className="text-sm leading-snug text-apex-text/70">
            {decision.portfolioStanceDetail}
          </p>
          <p className="text-sm leading-snug text-apex-text/75">
            Available to deploy: {formatInr(decision.deployableCapital ?? decision.availableCash)}
          </p>
          {decision.capitalMode === "MARGIN" ? (
            <>
              <p className="text-sm font-medium leading-snug text-apex-text/85">
                Capital Mode: MARGIN
              </p>
              {decision.marginWarning ? (
                <p className="text-sm leading-snug text-amber-200/85">
                  {decision.marginWarning}
                </p>
              ) : null}
            </>
          ) : null}
          {decision.deployAmount > 0 ? (
            <p className="text-sm leading-snug text-apex-text/75">
              Deploy amount: {formatInr(decision.deployAmount)}
            </p>
          ) : null}
        </div>
      ) : null}

      {!depthOnly ? (
        <div className="space-y-1">
          <p className="text-lg font-medium leading-snug text-apex-text">
            {decision.primaryAction}
          </p>
          <p className="text-sm leading-snug text-apex-text/75">
            {decision.primaryActionDetail}
          </p>
        </div>
      ) : null}

      {decision.growEmptyMessage ? (
        <p className="text-sm font-medium leading-snug text-apex-text/90">
          {decision.growEmptyMessage}
        </p>
      ) : null}

      {decision.actions.length > 0 ? (
        <ul className="space-y-8">
          {decision.actions.map((item) => (
            <CapitalActionRow key={item.symbol} action={item} />
          ))}
        </ul>
      ) : null}

      {decision.finalState ? (
        <div className="space-y-1 border-t border-apex-border/15 pt-4">
          {formatFinalStateSummary(decision.finalState).map((line) => (
            <p
              key={line}
              className={[
                "text-sm leading-snug",
                line === decision.finalState?.risk &&
                decision.finalState.risk === "Concentration risk remains"
                  ? "text-amber-200/85"
                  : line === "After execution:"
                    ? "font-medium text-apex-text/90"
                    : "text-apex-text/75",
              ].join(" ")}
            >
              {line}
            </p>
          ))}
        </div>
      ) : null}

      {decision.decisionLock ? (
        <div className="space-y-1 border-t border-apex-border/15 pt-4">
          <p className="text-sm font-semibold leading-snug text-apex-text">
            {decision.decisionLock.messagePrimary}
          </p>
          <p className="text-sm font-medium leading-snug text-apex-text/85">
            {decision.decisionLock.messageSecondary}
          </p>
        </div>
      ) : null}
    </section>
  );
}

function ExploreMonitoringBlock({
  decision,
  delayMs,
  liveTriggers,
  liveTriggersLoading = false,
}: {
  decision: CapitalDecision;
  delayMs: number;
  liveTriggers?: Map<string, ExploreLiveTrigger>;
  liveTriggersLoading?: boolean;
}) {
  return (
    <TierBlock tier="primary" delayMs={delayMs}>
      <div className="space-y-4">
        <StancePrimaryHeader decision={decision} />

        {liveTriggersLoading ? (
          <p className="text-xs text-apex-muted/70">Refreshing live triggers…</p>
        ) : liveTriggers && liveTriggers.size > 0 ? (
          <p className="text-xs text-apex-muted/65">
            Live trigger states from Zerodha / market data.
          </p>
        ) : null}

        {decision.explorePipelineSummary ? (
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            {decision.explorePipelineSummary}
          </p>
        ) : null}

        {decision.exploreSetups.length > 0 ? (
          <ul className="space-y-5 border-t border-apex-border/15 pt-4">
            {decision.exploreSetups.map((item) => (
              <ExploreSetupRow
                key={item.symbol}
                setup={item}
                liveTrigger={liveTriggers?.get(item.symbol)}
              />
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

function triggerStateClass(state: ExploreLiveTrigger["state"]): string {
  if (state === "confirmed") {
    return "border-emerald-400/30 bg-emerald-500/10 text-emerald-200/95";
  }

  if (state === "near_entry") {
    return "border-amber-400/30 bg-amber-500/10 text-amber-200/95";
  }

  if (state === "watch") {
    return "border-blue-300/25 bg-blue-500/10 text-blue-100/90";
  }

  return "border-apex-border/20 bg-white/[0.03] text-apex-muted/80";
}

function ExploreSetupRow({
  setup,
  liveTrigger,
}: {
  setup: ExploreSetup;
  liveTrigger?: ExploreLiveTrigger;
}) {
  const isHighlighted =
    setup.priorityMarker === "Closest to activation" || setup.isPrimary;
  const headline = liveTrigger?.liveScanLine ?? setup.scanLine;

  return (
    <li
      className={
        isHighlighted
          ? "rounded-lg border border-apex-border/20 bg-white/[0.02] p-3"
          : undefined
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-base font-medium tracking-wide text-apex-text/70">
          {setup.symbol}
        </p>
        {liveTrigger ? (
          <span
            className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wide ${triggerStateClass(liveTrigger.state)}`}
          >
            {liveTrigger.label}
          </span>
        ) : null}
      </div>
      <p className="mt-0.5 text-xl font-semibold leading-tight text-apex-text">
        {headline}
      </p>
      {liveTrigger ? (
        <p className="mt-1 text-xs text-apex-muted/70">
          Live {formatInr(liveTrigger.livePrice)}
          {liveTrigger.gapPct !== undefined && liveTrigger.activationLevel
            ? ` · ${liveTrigger.gapPct}% to ${formatInr(liveTrigger.activationLevel)}`
            : null}
        </p>
      ) : null}
      <p className="mt-1.5 text-xs font-medium uppercase tracking-wider text-apex-text/55">
        {setup.stageLine}
      </p>
      <div className="mt-2.5 space-y-1 border-t border-apex-border/10 pt-2.5 text-sm leading-snug text-apex-text/70">
        <p>{setup.progressDelta}</p>
        <p>{setup.progressLine}</p>
        {setup.whyThisMatters ? (
          <p className="border-l-2 border-blue-200/50 pl-2.5 font-medium text-apex-text/90">
            {setup.whyThisMatters}
          </p>
        ) : null}
        <p>{setup.activation}</p>
        <p>{setup.timeHorizon}</p>
      </div>
    </li>
  );
}

function CapitalActionRow({ action }: { action: CapitalAction }) {
  return (
    <li className="space-y-2">
      <p className="text-base font-semibold leading-snug text-apex-text">
        {action.symbol}
      </p>
      <p className="text-sm leading-snug text-apex-text/85">{action.action}</p>
      {action.action === "BUY" ? (
        <>
          <p className="text-sm leading-snug text-apex-text/85">
            {action.deployAmount !== undefined && action.deployAmount > 0
              ? `Deploy ${formatInr(action.deployAmount)} (${action.deployPercentage}% of available cash)`
              : `Deploy ${action.deployPercentage}% of available cash`}
          </p>
          <p className="text-sm leading-snug text-apex-text/85">
            Only if trigger confirms
          </p>
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            No entry before confirmation.
          </p>
        </>
      ) : null}
      {action.action === "WAIT" ? (
        <>
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            Do not deploy yet
          </p>
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            Premature entry is invalid.
          </p>
          {action.stage ? (
            <p className="text-sm leading-snug text-apex-text/70">
              {formatGrowActionStage(action.stage)}
            </p>
          ) : null}
        </>
      ) : null}
      {action.action === "SELL" ? (
        <>
          {action.portfolioWeight !== undefined ? (
            <p className="text-sm leading-snug text-apex-text/85">
              Portfolio weight: {Math.round(action.portfolioWeight)}%
            </p>
          ) : null}
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            Reduce exposure
          </p>
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            Do not add until trim completes.
          </p>
        </>
      ) : null}
      <div className="space-y-0.5 text-sm leading-snug text-apex-text/75">
        <p>Missing: {action.reason.missing}</p>
        <p>Confirm: {action.reason.confirm}</p>
        <p>Timing: {action.reason.timing}</p>
      </div>
      {action.ifIgnored &&
      (action.action === "WAIT" || action.action === "SELL") ? (
        <p className="text-sm leading-snug text-apex-text/75">
          {action.ifIgnored}
        </p>
      ) : null}
      {action.postActionImpact ? (
        <p className="text-sm leading-snug text-apex-text/75">
          {action.postActionImpact}
        </p>
      ) : null}
      {action.postAction ? (
        <div className="space-y-1 border-t border-apex-border/10 pt-2">
          <p className="text-sm leading-snug text-apex-text/80">
            {action.postAction.note}
          </p>
          {action.postAction.warning ? (
            <p className="text-sm leading-snug text-amber-200/85">
              {action.postAction.warning}
            </p>
          ) : null}
        </div>
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
  commitmentHeadline,
  commitmentMicroReward,
  delayMs,
  capitalDeployment = false,
  decision,
  executionKind,
}: {
  committedToday: boolean;
  onMarkFollowed: () => void;
  streakMessage: string;
  pressureLine: string | null;
  waitDisciplineReward: string | null;
  rewardHook: string | null;
  commitmentHeadline?: string;
  commitmentMicroReward?: string | null;
  delayMs: number;
  capitalDeployment?: boolean;
  decision?: CapitalDecision;
  executionKind?: TodayExecutionKind;
}) {
  const trustReinforcement =
    capitalDeployment && committedToday && decision
      ? buildTrustReinforcement(decision)
      : null;

  if (capitalDeployment) {
    return (
      <section
        className="mt-8 space-y-2 animate-apex-fade-in"
        style={{ animationDelay: `${delayMs}ms` }}
      >
        {commitmentHeadline ? (
          <p className="text-sm font-medium leading-snug text-apex-text/90">
            {commitmentHeadline}
          </p>
        ) : null}
        {commitmentMicroReward ? (
          <p className="text-xs leading-snug text-apex-muted/65">
            {commitmentMicroReward}
          </p>
        ) : null}
        {committedToday ? (
          <p className="text-sm leading-snug text-apex-text/90">
            [✓] Followed today
          </p>
        ) : (
          <button
            type="button"
            onClick={onMarkFollowed}
            disabled={committedToday}
            className="text-left text-sm leading-snug text-apex-text/85 transition-opacity hover:text-apex-text disabled:cursor-default disabled:opacity-60"
          >
            [ ] Followed today
          </button>
        )}
        {trustReinforcement ? (
          <div className="space-y-1 pt-1">
            <p className="text-sm leading-snug text-apex-text/90">
              {trustReinforcement.confirmation}
            </p>
            <p className="text-sm leading-snug text-apex-text/80">
              {trustReinforcement.framing}
            </p>
            {trustReinforcement.microReward ? (
              <p className="text-xs leading-snug text-apex-muted/65">
                {trustReinforcement.microReward}
              </p>
            ) : null}
            <p className="text-xs leading-snug text-apex-muted/60">
              {trustReinforcement.nextStep}
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            <p className="text-xs leading-snug text-apex-muted/70">
              {streakMessage}
            </p>
            {pressureLine ? (
              <p className="text-xs leading-snug text-apex-muted/65">
                {pressureLine}
              </p>
            ) : null}
            {waitDisciplineReward ? (
              <p className="text-xs leading-snug text-apex-muted/60">
                {waitDisciplineReward}
              </p>
            ) : null}
          </div>
        )}
      </section>
    );
  }

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
            {getDailyClosureBody(executionKind)}
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
