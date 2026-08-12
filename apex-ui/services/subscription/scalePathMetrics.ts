import { createAdminClient } from "@/lib/supabase/admin";
import type { MigrationHealthReport } from "@/lib/supabase/migrationHealth";

/** ESTIMATE — T4-6 business milestone targets from transformation roadmap. */
export const SCALE_PATH_TARGETS = {
  payingUsersMin: 15_000,
  payingUsersMax: 25_000,
  arrCrMin: 8,
  arrCrMax: 15,
  milestoneId: "T4-6",
} as const;

export type ScalePathSnapshot = {
  milestone_id: typeof SCALE_PATH_TARGETS.milestoneId;
  paying_subscriptions: number | null;
  active_trials: number | null;
  invite_activations: number | null;
  target_paying_users_min: number;
  target_paying_users_max: number;
  arr_target_cr_min: number;
  arr_target_cr_max: number;
  note: string;
};

async function countTableRows(
  table: string,
  migrationStatus: "ready" | "pending" | "unknown",
): Promise<number | null> {
  if (migrationStatus !== "ready") {
    return null;
  }

  try {
    const admin = createAdminClient();
    const { count, error } = await admin
      .from(table)
      .select("*", { count: "exact", head: true });

    if (error) {
      return null;
    }

    return count ?? 0;
  } catch {
    return null;
  }
}

async function countActivePremiumSubscriptions(
  migrationStatus: "ready" | "pending" | "unknown",
): Promise<number | null> {
  if (migrationStatus !== "ready") {
    return null;
  }

  try {
    const admin = createAdminClient();
    const { count, error } = await admin
      .from("premium_subscriptions")
      .select("*", { count: "exact", head: true })
      .in("status", ["active", "authenticated"]);

    if (error) {
      return null;
    }

    return count ?? 0;
  } catch {
    return null;
  }
}

async function countActiveTrials(
  migrationStatus: "ready" | "pending" | "unknown",
): Promise<number | null> {
  if (migrationStatus !== "ready") {
    return null;
  }

  try {
    const admin = createAdminClient();
    const now = new Date().toISOString();
    const { count, error } = await admin
      .from("premium_trial_offers")
      .select("*", { count: "exact", head: true })
      .not("claimed_at", "is", null)
      .gt("expires_at", now);

    if (error) {
      return null;
    }

    return count ?? 0;
  } catch {
    return null;
  }
}

export async function assembleScalePathSnapshot(
  migrations: MigrationHealthReport,
  serviceRoleConfigured: boolean,
): Promise<ScalePathSnapshot | null> {
  if (!serviceRoleConfigured) {
    return null;
  }

  const [paying_subscriptions, active_trials, invite_activations] =
    await Promise.all([
      countActivePremiumSubscriptions(migrations.premium_subscriptions),
      countActiveTrials(migrations.premium_trial_offers),
      countTableRows("premium_activations", "ready"),
    ]);

  return {
    milestone_id: SCALE_PATH_TARGETS.milestoneId,
    paying_subscriptions,
    active_trials,
    invite_activations,
    target_paying_users_min: SCALE_PATH_TARGETS.payingUsersMin,
    target_paying_users_max: SCALE_PATH_TARGETS.payingUsersMax,
    arr_target_cr_min: SCALE_PATH_TARGETS.arrCrMin,
    arr_target_cr_max: SCALE_PATH_TARGETS.arrCrMax,
    note:
      "ESTIMATE — counts are ops signals only; T4-6 is a business milestone, not a deploy gate.",
  };
}

export function runScalePathMetricsSelfCheck(): void {
  if (SCALE_PATH_TARGETS.payingUsersMin >= SCALE_PATH_TARGETS.payingUsersMax) {
    throw new Error("Scale path metrics self-check failed: user targets");
  }

  if (SCALE_PATH_TARGETS.arrCrMin >= SCALE_PATH_TARGETS.arrCrMax) {
    throw new Error("Scale path metrics self-check failed: ARR targets");
  }
}
