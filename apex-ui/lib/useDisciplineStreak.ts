"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { istDateKey } from "@/lib/dailyLoop/disciplineDates";
import {
  applyDisciplineStreakSnapshot,
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

type StreakApiResponse = {
  status: string;
  streak?: DisciplineStreakSnapshot;
  message?: string;
};

async function fetchDisciplineStreakFromServer(): Promise<DisciplineStreakSnapshot | null> {
  try {
    const response = await fetch("/api/discipline/streak", {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as StreakApiResponse;

    if (payload.status !== "ok" || !payload.streak) {
      return null;
    }

    return payload.streak;
  } catch {
    return null;
  }
}

async function postDisciplineCommit(input: {
  intent: UserIntent;
  action: string;
  stock?: string;
}): Promise<DisciplineStreakSnapshot | null> {
  try {
    const response = await fetch("/api/discipline/streak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as StreakApiResponse;

    if (payload.status !== "ok" || !payload.streak) {
      return null;
    }

    return payload.streak;
  } catch {
    return null;
  }
}

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
    let cancelled = false;

    const load = async () => {
      const serverSnapshot = await fetchDisciplineStreakFromServer();

      if (cancelled) {
        return;
      }

      if (serverSnapshot) {
        applyDisciplineStreakSnapshot(serverSnapshot);
        setSnapshot(serverSnapshot);
        return;
      }

      setSnapshot(readDisciplineStreak());
    };

    void load();

    return () => {
      cancelled = true;
    };
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
      `${istDateKey()}:${intent}:${action}:${stock ?? "none"}`,
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

    void (async () => {
      const serverSnapshot = await postDisciplineCommit({ intent, action, stock });

      if (serverSnapshot) {
        applyDisciplineStreakSnapshot(serverSnapshot);
        setSnapshot(serverSnapshot);
        return;
      }

      const localSnapshot = commitDisciplineFollowed({ intent, action, stock });
      setSnapshot(localSnapshot);
    })();
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
