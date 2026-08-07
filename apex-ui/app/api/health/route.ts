import { NextResponse } from "next/server";
import { getSystemConfigReport } from "@/lib/env/config";

export async function GET() {
  const report = getSystemConfigReport();

  return NextResponse.json(
    {
      supabase: report.supabase ? "connected" : "missing",
      env: report.ok ? "ok" : "incomplete",
    },
    { status: report.ok ? 200 : 503 },
  );
}
