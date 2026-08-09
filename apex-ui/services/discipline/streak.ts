import {
  buildDisciplineStreakSnapshot,
  commitDisciplineState,
  EMPTY_DISCIPLINE_STREAK_STATE,
  normalizeStreakForToday,
  type DisciplineStreakSnapshot,
  type DisciplineStreakState,
} from "@/lib/dailyLoop/disciplineStreakLogic";
import type { Database } from "@/types/database";
import type { UserIntent } from "@/types/intent";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

type StreakRow = Database["public"]["Tables"]["discipline_streak_state"]["Row"];

function rowToState(row: StreakRow | null): DisciplineStreakState {
  if (!row) {
    return EMPTY_DISCIPLINE_STREAK_STATE;
  }

  return {
    streakCount: Math.max(0, row.streak_count ?? 0),
    lastActionFollowed: Boolean(row.last_action_followed),
    lastCommitDate:
      typeof row.last_commit_date === "string" ? row.last_commit_date : null,
    lastDecisionKey:
      typeof row.last_decision_key === "string" ? row.last_decision_key : null,
  };
}

async function persistStreakState(
  supabase: Client,
  userId: string,
  state: DisciplineStreakState,
): Promise<void> {
  const { error } = await supabase.from("discipline_streak_state").upsert(
    {
      user_id: userId,
      streak_count: state.streakCount,
      last_commit_date: state.lastCommitDate,
      last_decision_key: state.lastDecisionKey,
      last_action_followed: state.lastActionFollowed,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" },
  );

  if (error) {
    throw new Error(error.message);
  }
}

export async function getDisciplineStreak(
  supabase: Client,
  userId: string,
): Promise<DisciplineStreakSnapshot> {
  const { data, error } = await supabase
    .from("discipline_streak_state")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  const raw = rowToState(data);
  const normalized = normalizeStreakForToday(raw);

  if (
    data &&
    (normalized.streakCount !== raw.streakCount ||
      normalized.lastActionFollowed !== raw.lastActionFollowed ||
      normalized.lastCommitDate !== raw.lastCommitDate)
  ) {
    await persistStreakState(supabase, userId, normalized);
  }

  return buildDisciplineStreakSnapshot(normalized);
}

export async function commitDisciplineStreak(
  supabase: Client,
  userId: string,
  input: {
    intent: UserIntent;
    action: string;
    stock?: string;
  },
): Promise<DisciplineStreakSnapshot> {
  const { data, error } = await supabase
    .from("discipline_streak_state")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  const current = rowToState(data);
  const next = commitDisciplineState(current, input);
  const snapshot = buildDisciplineStreakSnapshot(next);

  if (!next.lastCommitDate || !next.lastDecisionKey) {
    throw new Error("Invalid discipline commit state");
  }

  await persistStreakState(supabase, userId, next);

  const { error: commitError } = await supabase.from("discipline_commits").upsert(
    {
      user_id: userId,
      commit_date: next.lastCommitDate,
      intent: input.intent,
      action: input.action,
      stock: input.stock ?? null,
      decision_key: next.lastDecisionKey,
      followed: true,
      streak_count: next.streakCount,
    },
    { onConflict: "user_id,commit_date" },
  );

  if (commitError) {
    throw new Error(commitError.message);
  }

  return snapshot;
}
