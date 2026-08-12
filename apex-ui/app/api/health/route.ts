import { NextResponse } from "next/server";
import { getKiteOrderProxyStatus } from "@/lib/broker/kiteOrderProxy";
import { getSystemConfigReport } from "@/lib/env/config";
import { probeMigrationHealth } from "@/lib/supabase/migrationHealth";
import { assembleScalePathSnapshot } from "@/services/subscription/scalePathMetrics";

export async function GET() {
  const report = getSystemConfigReport();
  const kiteProxy = getKiteOrderProxyStatus();
  const migrations = await probeMigrationHealth(report.serviceRole);
  const scalePath = await assembleScalePathSnapshot(migrations, report.serviceRole);

  return NextResponse.json(
    {
      supabase: report.supabase ? "connected" : "missing",
      env: report.ok ? "ok" : "incomplete",
      kite_proxy: kiteProxy.configured ? "configured" : "missing",
      migrations,
      scale_path: scalePath,
    },
    {
      status: report.ok ? 200 : 503,
      headers: {
        "Cache-Control": "no-store, must-revalidate",
      },
    },
  );
}
