import { istDateKey, shiftIstDateKey } from "@/lib/dailyLoop/disciplineDates";
import type { UserIntent } from "@/types/intent";

export type DisciplineStreakState = {
  streakCount: number;
  lastActionFollowed: boolean;
  lastCommitDate: string | null;
  lastDecisionKey: string | null;
};

export type DisciplineStreakSnapshot = DisciplineStreakState & {
  committedToday: boolean;
};

export const EMPTY_DISCIPLINE_STREAK_STATE: DisciplineStreakState = {
  streakCount: 0,
  lastActionFollowed: false,
  lastCommitDate: null,
  lastDecisionKey: null,
};

export function buildDecisionKey(input: {
  intent: UserIntent;
  action: string;
  stock?: string;
}): string {
  return `${input.intent}:${input.action}:${input.stock ?? "none"}`;
}

export function normalizeStreakForToday(
  state: DisciplineStreakState,
  today: Date = new Date(),
): DisciplineStreakState {
  const todayKey = istDateKey(today);

  if (!state.lastCommitDate) {
    return state;
  }

  if (state.lastCommitDate === todayKey) {
    return state;
  }

  const yesterdayKey = shiftIstDateKey(todayKey, -1);

  if (state.lastCommitDate === yesterdayKey && state.lastActionFollowed) {
    return {
      ...state,
      lastActionFollowed: false,
    };
  }

  return {
    ...state,
    streakCount: 0,
    lastActionFollowed: false,
  };
}

export function buildDisciplineStreakSnapshot(
  state: DisciplineStreakState,
  today: Date = new Date(),
): DisciplineStreakSnapshot {
  const todayKey = istDateKey(today);
  const normalized = normalizeStreakForToday(state, today);

  return {
    ...normalized,
    committedToday:
      normalized.lastCommitDate === todayKey && normalized.lastActionFollowed,
  };
}

export function commitDisciplineState(
  current: DisciplineStreakState,
  input: {
    intent: UserIntent;
    action: string;
    stock?: string;
    today?: Date;
  },
): DisciplineStreakState {
  const today = input.today ?? new Date();
  const todayKey = istDateKey(today);
  const yesterdayKey = shiftIstDateKey(todayKey, -1);
  const decisionKey = buildDecisionKey(input);
  const normalized = normalizeStreakForToday(current, today);

  if (normalized.lastCommitDate === todayKey && normalized.lastActionFollowed) {
    return normalized;
  }

  let streakCount = 1;

  if (
    normalized.lastCommitDate === yesterdayKey &&
    normalized.lastActionFollowed
  ) {
    streakCount = normalized.streakCount + 1;
  } else if (normalized.lastCommitDate === todayKey) {
    streakCount = Math.max(1, normalized.streakCount);
  }

  return {
    streakCount,
    lastActionFollowed: true,
    lastCommitDate: todayKey,
    lastDecisionKey: decisionKey,
  };
}
