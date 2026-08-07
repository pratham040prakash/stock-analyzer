import { NextResponse } from "next/server";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";

export async function GET() {
  const config = getZerodhaConfig();

  return NextResponse.json(
    config.configured
      ? { configured: true }
      : { configured: false, reason: config.reason },
    { status: config.configured ? 200 : 503 },
  );
}
