import { NextResponse } from "next/server";
import { getKiteOrderProxyStatus } from "@/lib/broker/kiteOrderProxy";
import { getSystemConfigReport } from "@/lib/env/config";

export async function GET() {
  const report = getSystemConfigReport();
  const kiteProxy = getKiteOrderProxyStatus();

  return NextResponse.json(
    {
      supabase: report.supabase ? "connected" : "missing",
      env: report.ok ? "ok" : "incomplete",
      kite_proxy: kiteProxy.configured ? "configured" : "missing",
    },
    {
      status: report.ok ? 200 : 503,
      headers: {
        "Cache-Control": "no-store, must-revalidate",
      },
    },
  );
}
