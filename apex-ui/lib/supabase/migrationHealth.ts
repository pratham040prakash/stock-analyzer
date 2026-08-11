import { createAdminClient } from "@/lib/supabase/admin";

export type MigrationProbeStatus = "ready" | "pending" | "unknown";

export async function probeOperatingProfileMigration(): Promise<MigrationProbeStatus> {
  try {
    const admin = createAdminClient();
    const { error } = await admin
      .from("operating_profiles")
      .select("user_id", { head: true, count: "exact" })
      .limit(0);

    if (error) {
      const message = error.message.toLowerCase();
      if (
        message.includes("operating_profiles") ||
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
