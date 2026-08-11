import { NextResponse } from "next/server";
import { getKiteOrderProxyStatus } from "@/lib/broker/kiteOrderProxy";
import { getSystemConfigReport } from "@/lib/env/config";
import { probeOperatingProfileMigration } from "@/lib/supabase/migrationHealth";

export async function GET() {
  const report = getSystemConfigReport();
  const kiteProxy = getKiteOrderProxyStatus();
  const operatingProfileMigration = report.serviceRole
    ? await probeOperatingProfileMigration()
    : "unknown";

  return NextResponse.json(
    {
      supabase: report.supabase ? "connected" : "missing",
      env: report.ok ? "ok" : "incomplete",
      kite_proxy: kiteProxy.configured ? "configured" : "missing",
      migrations: {
        operating_profile: operatingProfileMigration,
      },
    },
    {
      status: report.ok ? 200 : 503,
      headers: {
        "Cache-Control": "no-store, must-revalidate",
      },
    },
  );
}
