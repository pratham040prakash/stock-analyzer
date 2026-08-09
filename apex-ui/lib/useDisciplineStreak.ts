"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  commitDisciplineFollowed,
  DISCIPLINE_PRESSURE_LINE,
  formatDailyContextLabel,
  getStreakMessage,
  getWaitRewardHook,
  isNoTradeDecision,
  readDisciplineStreak,
  WAIT_DISCIPLINE_REWARD,
  type DisciplineStreakSnapshot,
} from "@/lib/dailyLoop/disciplineStreak";
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
  isWaitMode: boolean;
  pressureLine: string | null;
  waitDisciplineReward: string | null;
  rewardHook: string | null;
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

  useEffect(() => {
    setSnapshot(readDisciplineStreak());
  }, [intent, action, stock]);

  useEffect(() => {
    const updateLabel = () => {
      setDailyContextLabel(formatDailyContextLabel());
    };

    updateLabel();
    const intervalId = window.setInterval(updateLabel, 60_000);
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

  const commitFollowed = useCallback(() => {
    const next = commitDisciplineFollowed({ intent, action, stock });
    setSnapshot(next);
  }, [action, intent, stock]);

  return {
    streakCount: snapshot.streakCount,
    lastActionFollowed: snapshot.lastActionFollowed,
    committedToday: snapshot.committedToday,
    streakMessage: getStreakMessage(snapshot.streakCount),
    dailyContextLabel,
    isWaitMode,
    pressureLine: isWaitMode ? DISCIPLINE_PRESSURE_LINE : null,
    waitDisciplineReward,
    rewardHook,
    commitFollowed,
  };
}
