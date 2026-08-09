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

  if (count < 3) {
    return "Building discipline — stay consistent.";
  }

  if (count <= 7) {
    return "Consistency forming — capital protection improving.";
  }

  return "Strong discipline — unnecessary risk avoided.";
}

export const DISCIPLINE_PRESSURE_LINE =
  "Skipping today breaks your discipline streak.";

export const WAIT_DISCIPLINE_REWARD =
  "Staying in cash is an active decision.";

export const TRUST_MICRO_REWARD =
  "Discipline today compounds into capital protection.";

export function getDecisionTensionLine(committedToday: boolean): string {
  return committedToday
    ? "Today's decision completed."
    : "Today's decision is pending.";
}

function getIstMinutes(now: Date): number {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kolkata",
    hour: "numeric",
    minute: "numeric",
    hour12: false,
  }).formatToParts(now);
  const hour = Number(parts.find((part) => part.type === "hour")?.value ?? 0);
  const minute = Number(
    parts.find((part) => part.type === "minute")?.value ?? 0,
  );

  return hour * 60 + minute;
}

/** NSE cash session window (IST): 9:15–15:30. */
export function getSessionTimeContext(now: Date = new Date()): string {
  const minutes = getIstMinutes(now);
  const open = 9 * 60 + 15;
  const close = 15 * 60 + 30;

  if (minutes >= open && minutes < close) {
    return "Decision valid for today's session.";
  }

  return "Decision closed — review tomorrow.";
}

export function getTrustMicroReward(seed: string): string | null {
  let hash = 0;

  for (let index = 0; index < seed.length; index += 1) {
    hash = (hash + seed.charCodeAt(index)) % 997;
  }

  if (hash % 5 !== 0) {
    return null;
  }

  return TRUST_MICRO_REWARD;
}

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

    return `Daily capital decision · ${time}`;
  } catch {
    return "Today's capital decision";
  }
}
