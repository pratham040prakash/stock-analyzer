import type { OperatingProfile } from "@/types/operatingProfile";
import { parseInvestmentStyle } from "@/types/operatingProfile";
import type { Database } from "@/types/database";
import type { SupabaseClient } from "@supabase/supabase-js";

type Client = SupabaseClient<Database>;

function mapRow(row: {
  investment_style: string;
  intraday_acknowledged_at: string;
}): OperatingProfile {
  const investmentStyle = parseInvestmentStyle(row.investment_style);

  if (!investmentStyle) {
    throw new Error("Invalid investment_style in database");
  }

  return {
    investmentStyle,
    intradayAcknowledgedAt: row.intraday_acknowledged_at,
  };
}

export async function getOperatingProfileFromDb(
  supabase: Client,
  userId: string,
): Promise<OperatingProfile | null> {
  const { data, error } = await supabase
    .from("operating_profiles")
    .select("investment_style, intraday_acknowledged_at")
    .eq("user_id", userId)
    .maybeSingle();

  if (error || !data) {
    return null;
  }

  return mapRow(data);
}

export async function upsertOperatingProfile(
  supabase: Client,
  userId: string,
  profile: OperatingProfile,
): Promise<void> {
  const { error } = await supabase.from("operating_profiles").upsert(
    {
      user_id: userId,
      investment_style: profile.investmentStyle,
      intraday_acknowledged_at: profile.intradayAcknowledgedAt,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "user_id" },
  );

  if (error) {
    throw error;
  }
}

export function runOperatingProfileRepositorySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Operating profile repository self-check failed: ${message}`);
    }
  };

  assert(
    parseInvestmentStyle("core_plus_tactical") === "core_plus_tactical",
    "Must parse valid style",
  );
  assert(parseInvestmentStyle("invalid") === null, "Must reject invalid style");
}
