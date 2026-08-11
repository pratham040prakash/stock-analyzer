import { createAdminClient } from "@/lib/supabase/admin";

export type MigrationProbeStatus = "ready" | "pending" | "unknown";

export type MigrationHealthReport = {
  operating_profile: MigrationProbeStatus;
  premium_subscriptions: MigrationProbeStatus;
  premium_trial_offers: MigrationProbeStatus;
};

async function probeTable(table: string): Promise<MigrationProbeStatus> {
  try {
    const admin = createAdminClient();
    const { error } = await admin.from(table).select("*", { head: true, count: "exact" }).limit(0);

    if (error) {
      const message = error.message.toLowerCase();
      if (
        message.includes(table) ||
        message.includes("does not exist") ||
        message.includes("schema cache")
      ) {
        return "pending";
      }

      return "unknown";
    }

    return "ready";
  } catch {
    return "unknown";
  }
}

export async function probeOperatingProfileMigration(): Promise<MigrationProbeStatus> {
  return probeTable("operating_profiles");
}

export async function probePremiumSubscriptionsMigration(): Promise<MigrationProbeStatus> {
  return probeTable("premium_subscriptions");
}

export async function probePremiumTrialOffersMigration(): Promise<MigrationProbeStatus> {
  return probeTable("premium_trial_offers");
}

export async function probeMigrationHealth(
  serviceRoleConfigured: boolean,
): Promise<MigrationHealthReport> {
  if (!serviceRoleConfigured) {
    return {
      operating_profile: "unknown",
      premium_subscriptions: "unknown",
      premium_trial_offers: "unknown",
    };
  }

  const [operating_profile, premium_subscriptions, premium_trial_offers] =
    await Promise.all([
      probeOperatingProfileMigration(),
      probePremiumSubscriptionsMigration(),
      probePremiumTrialOffersMigration(),
    ]);

  return {
    operating_profile,
    premium_subscriptions,
    premium_trial_offers,
  };
}

export function runMigrationHealthSelfCheck(): void {
  const statuses: MigrationProbeStatus[] = ["ready", "pending", "unknown"];

  for (const status of statuses) {
    if (!statuses.includes(status)) {
      throw new Error("Migration health self-check failed: status enum");
    }
  }
}
