"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  commitDisciplineFollowed,
  DISCIPLINE_PRESSURE_LINE,
  formatDailyContextLabel,
  getDecisionTensionLine,
  getSessionTimeContext,
  getStreakMessage,
  getWaitRewardHook,
  isNoTradeDecision,
  readDisciplineStreak,
  WAIT_DISCIPLINE_REWARD,
  type DisciplineStreakSnapshot,
} from "@/lib/dailyLoop/disciplineStreak";
import { buildCommitmentCopy } from "@/lib/dailyLoop/disciplineCommitment";
import type { UserIntent } from "@/types/intent";

type UseDisciplineStreakInput = {
  intent: UserIntent;
  action: string;
  stock?: string;
  deploymentPercentage?: number;
};

export type DisciplineStreakView = {
  streakCount: number;
  lastActionFollowed: boolean;
  committedToday: boolean;
  streakMessage: string;
  dailyContextLabel: string;
  decisionTensionLine: string;
  sessionTimeContext: string;
  isWaitMode: boolean;
  pressureLine: string | null;
  waitDisciplineReward: string | null;
  rewardHook: string | null;
  commitmentHeadline: string;
  commitmentMicroReward: string | null;
  commitFollowed: () => void;
};

export function useDisciplineStreak({
  intent,
  action,
  stock,
  deploymentPercentage,
}: UseDisciplineStreakInput): DisciplineStreakView {
  const [snapshot, setSnapshot] = useState<DisciplineStreakSnapshot>(() =>
    readDisciplineStreak(),
  );
  const [dailyContextLabel, setDailyContextLabel] = useState(() =>
    formatDailyContextLabel(),
  );
  const [sessionTimeContext, setSessionTimeContext] = useState(() =>
    getSessionTimeContext(),
  );

  useEffect(() => {
    setSnapshot(readDisciplineStreak());
  }, [intent, action, stock]);

  useEffect(() => {
    const updateContext = () => {
      setDailyContextLabel(formatDailyContextLabel());
      setSessionTimeContext(getSessionTimeContext());
    };

    updateContext();
    const intervalId = window.setInterval(updateContext, 60_000);
    return () => window.clearInterval(intervalId);
  }, []);

  const isWaitMode =
    isNoTradeDecision(action, intent) ||
    (deploymentPercentage !== undefined && deploymentPercentage <= 0);

  const rewardHook = useMemo(() => {
    if (!isWaitMode) {
      return null;
    }

    const seed = `${intent}:${action}:${stock ?? "none"}`;
    return getWaitRewardHook(seed);
  }, [action, intent, isWaitMode, stock]);

  const waitDisciplineReward = isWaitMode ? WAIT_DISCIPLINE_REWARD : null;

  const commitmentSeed = useMemo(
    () =>
      `${new Date().toISOString().slice(0, 10)}:${intent}:${action}:${stock ?? "none"}`,
    [action, intent, stock],
  );

  const commitmentCopy = useMemo(
    () => buildCommitmentCopy(snapshot.committedToday, commitmentSeed),
    [commitmentSeed, snapshot.committedToday],
  );

  const commitFollowed = useCallback(() => {
    if (snapshot.committedToday) {
      return;
    }

    const next = commitDisciplineFollowed({ intent, action, stock });
    setSnapshot(next);
  }, [action, intent, snapshot.committedToday, stock]);

  return {
    streakCount: snapshot.streakCount,
    lastActionFollowed: snapshot.lastActionFollowed,
    committedToday: snapshot.committedToday,
    streakMessage: getStreakMessage(snapshot.streakCount),
    dailyContextLabel,
    decisionTensionLine: getDecisionTensionLine(snapshot.committedToday),
    sessionTimeContext,
    isWaitMode,
    pressureLine: snapshot.committedToday ? null : DISCIPLINE_PRESSURE_LINE,
    waitDisciplineReward,
    rewardHook,
    commitmentHeadline: commitmentCopy.headline,
    commitmentMicroReward: commitmentCopy.microReward,
    commitFollowed,
  };
}
