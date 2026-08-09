import {
  buildDecisionKey,
  buildDisciplineStreakSnapshot,
  commitDisciplineState,
  EMPTY_DISCIPLINE_STREAK_STATE,
  normalizeStreakForToday,
  type DisciplineStreakSnapshot,
  type DisciplineStreakState,
} from "@/lib/dailyLoop/disciplineStreakLogic";
import type { TodayExecutionKind } from "@/lib/dailyLoop/todaySurface";
import type { UserIntent } from "@/types/intent";

export type { DisciplineStreakSnapshot, DisciplineStreakState };
export { buildDecisionKey, normalizeStreakForToday };

const STREAK_STORAGE_KEY = "apex_discipline_streak";

const EMPTY_STATE = EMPTY_DISCIPLINE_STREAK_STATE;

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
    ? "Discipline logged for today."
    : "Today's decision is pending.";
}

export function getBrokerStepLine(
  committedToday: boolean,
  executionKind?: TodayExecutionKind,
): string | null {
  if (!committedToday) {
    return null;
  }

  if (executionKind === "SELL" || executionKind === "BUY") {
    return "Broker step still open · See plan below.";
  }

  return null;
}

export function getDailyClosureBody(
  executionKind?: TodayExecutionKind,
): string {
  if (executionKind === "SELL" || executionKind === "BUY") {
    return "Discipline is locked in. Execute on Zerodha when ready, or review the plan below.";
  }

  return DAILY_CLOSURE_BODY;
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

  return "Market closed · Review your plan below.";
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
  const raw = readRawState();
  const normalized = normalizeStreakForToday(raw, today);

  if (
    normalized.streakCount !== raw.streakCount ||
    normalized.lastActionFollowed !== raw.lastActionFollowed ||
    normalized.lastCommitDate !== raw.lastCommitDate
  ) {
    writeState(normalized);
  }

  return buildDisciplineStreakSnapshot(normalized, today);
}

export function commitDisciplineFollowed(input: {
  intent: UserIntent;
  action: string;
  stock?: string;
  today?: Date;
}): DisciplineStreakSnapshot {
  const today = input.today ?? new Date();
  const current = normalizeStreakForToday(readRawState(), today);
  const next = commitDisciplineState(current, { ...input, today });

  writeState(next);

  return buildDisciplineStreakSnapshot(next, today);
}

export function applyDisciplineStreakSnapshot(
  snapshot: DisciplineStreakSnapshot,
): void {
  writeState({
    streakCount: snapshot.streakCount,
    lastActionFollowed: snapshot.lastActionFollowed,
    lastCommitDate: snapshot.lastCommitDate,
    lastDecisionKey: snapshot.lastDecisionKey,
  });
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

export function runDisciplineStatusSelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Discipline status self-check failed: ${message}`);
    }
  };

  assert(
    getDecisionTensionLine(true) === "Discipline logged for today.",
    "Committed tension line must describe discipline, not completion",
  );
  assert(
    getDecisionTensionLine(false) === "Today's decision is pending.",
    "Pending tension line must stay unchanged",
  );
  assert(
    getBrokerStepLine(true, "SELL") ===
      "Broker step still open · See plan below.",
    "Sell plans must surface broker step after discipline commit",
  );
  assert(getBrokerStepLine(true, "WAIT") === null, "Wait plans have no broker step");
  assert(
    getDailyClosureBody("SELL").includes("Zerodha"),
    "Sell closure must mention broker execution",
  );
  assert(
    getDailyClosureBody("WAIT") === DAILY_CLOSURE_BODY,
    "Wait closure must keep capital protection copy",
  );
}
