import type { UserIntent } from "@/types/intent";

const STREAK_STORAGE_KEY = "apex_discipline_streak";

export type DisciplineStreakState = {
  streakCount: number;
  lastActionFollowed: boolean;
  lastCommitDate: string | null;
  lastDecisionKey: string | null;
};

export type DisciplineStreakSnapshot = DisciplineStreakState & {
  committedToday: boolean;
};

const EMPTY_STATE: DisciplineStreakState = {
  streakCount: 0,
  lastActionFollowed: false,
  lastCommitDate: null,
  lastDecisionKey: null,
};

function toDateKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function shiftDateKey(dateKey: string, dayOffset: number): string {
  const [year, month, day] = dateKey.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  date.setDate(date.getDate() + dayOffset);
  return toDateKey(date);
}

function readRawState(): DisciplineStreakState {
  if (typeof window === "undefined") {
    return EMPTY_STATE;
  }

  const raw = window.localStorage.getItem(STREAK_STORAGE_KEY);

  if (!raw) {
    return EMPTY_STATE;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<DisciplineStreakState>;
    return {
      streakCount: Number.isFinite(parsed.streakCount)
        ? Math.max(0, Math.round(parsed.streakCount ?? 0))
        : 0,
      lastActionFollowed: Boolean(parsed.lastActionFollowed),
      lastCommitDate:
        typeof parsed.lastCommitDate === "string" ? parsed.lastCommitDate : null,
      lastDecisionKey:
        typeof parsed.lastDecisionKey === "string" ? parsed.lastDecisionKey : null,
    };
  } catch {
    return EMPTY_STATE;
  }
}

function writeState(state: DisciplineStreakState): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STREAK_STORAGE_KEY, JSON.stringify(state));
}

/** Rolls streak forward when a new day starts without a prior commit. */
export function normalizeStreakForToday(
  state: DisciplineStreakState,
  today: Date = new Date(),
): DisciplineStreakState {
  const todayKey = toDateKey(today);

  if (!state.lastCommitDate) {
    return state;
  }

  if (state.lastCommitDate === todayKey) {
    return state;
  }

  const yesterdayKey = shiftDateKey(todayKey, -1);

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

export function buildDecisionKey(input: {
  intent: UserIntent;
  action: string;
  stock?: string;
}): string {
  return `${input.intent}:${input.action}:${input.stock ?? "none"}`;
}

export function isNoTradeDecision(action: string, intent?: UserIntent): boolean {
  if (action === "wait" || action === "hold") {
    return true;
  }

  return action === "explore" || intent === "explore";
}

export function getStreakMessage(streakCount: number): string {
  const count = Math.max(0, Math.round(streakCount));

  if (count <= 0) {
    return "Mark when you follow today to start protecting capital.";
  }

  if (count === 1) {
    return "Discipline streak: 1 day — capital protected.";
  }

  if (count <= 3) {
    return `Discipline streak: ${count} days — capital protected.`;
  }

  return `Discipline streak: ${count} days — no unnecessary risk taken.`;
}

export const DISCIPLINE_PRESSURE_LINE =
  "Breaking discipline today resets your streak and exposes capital to unnecessary risk.";

export const WAIT_DISCIPLINE_REWARD =
  "Staying in cash today is an active decision to protect capital.";

export const DAILY_CLOSURE_HEADLINE = "You've followed the system today.";
export const DAILY_CLOSURE_BODY =
  "Capital remains protected. No further action required.";
export const DAILY_CLOSURE_NEXT_STEP =
  "Next review: after market close or on new signal.";

const WAIT_REWARD_HOOKS = [
  "Cash preserved today keeps optionality for the next confirmed entry.",
  "Patience today avoids capital deployed without edge.",
] as const;

export function getWaitRewardHook(seed: string): string | null {
  let hash = 0;

  for (let index = 0; index < seed.length; index += 1) {
    hash = (hash + seed.charCodeAt(index)) % 997;
  }

  if (hash % 3 !== 0) {
    return null;
  }

  return WAIT_REWARD_HOOKS[hash % WAIT_REWARD_HOOKS.length];
}

export function readDisciplineStreak(
  today: Date = new Date(),
): DisciplineStreakSnapshot {
  const todayKey = toDateKey(today);
  const raw = readRawState();
  const normalized = normalizeStreakForToday(raw, today);

  if (
    normalized.streakCount !== raw.streakCount ||
    normalized.lastActionFollowed !== raw.lastActionFollowed ||
    normalized.lastCommitDate !== raw.lastCommitDate
  ) {
    writeState(normalized);
  }

  return {
    ...normalized,
    committedToday:
      normalized.lastCommitDate === todayKey && normalized.lastActionFollowed,
  };
}

export function commitDisciplineFollowed(input: {
  intent: UserIntent;
  action: string;
  stock?: string;
  today?: Date;
}): DisciplineStreakSnapshot {
  const today = input.today ?? new Date();
  const todayKey = toDateKey(today);
  const yesterdayKey = shiftDateKey(todayKey, -1);
  const decisionKey = buildDecisionKey(input);
  const current = normalizeStreakForToday(readRawState(), today);

  if (current.lastCommitDate === todayKey && current.lastActionFollowed) {
    return {
      ...current,
      committedToday: true,
    };
  }

  let streakCount = 1;

  if (
    current.lastCommitDate === yesterdayKey &&
    current.lastActionFollowed
  ) {
    streakCount = current.streakCount + 1;
  } else if (current.lastCommitDate === todayKey) {
    streakCount = Math.max(1, current.streakCount);
  }

  const next: DisciplineStreakState = {
    streakCount,
    lastActionFollowed: true,
    lastCommitDate: todayKey,
    lastDecisionKey: decisionKey,
  };

  writeState(next);

  return {
    ...next,
    committedToday: true,
  };
}

export function resetDisciplineStreak(): DisciplineStreakSnapshot {
  writeState(EMPTY_STATE);
  return {
    ...EMPTY_STATE,
    committedToday: false,
  };
}

export function formatDailyContextLabel(now: Date = new Date()): string {
  try {
    const time = new Intl.DateTimeFormat(undefined, {
      hour: "numeric",
      minute: "2-digit",
    }).format(now);

    return `Daily Check · ${time}`;
  } catch {
    return "Today's Readiness";
  }
}
