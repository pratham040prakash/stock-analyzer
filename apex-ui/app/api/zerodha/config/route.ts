import { NextResponse } from "next/server";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";
import { getZerodhaCallbackUrl } from "@/lib/env/config";

export async function GET(request: Request) {
  const config = getZerodhaConfig();
  const origin = new URL(request.url).origin;
  const redirectUrl = getZerodhaCallbackUrl(origin);

  return NextResponse.json(
    config.configured
      ? { configured: true, redirectUrl }
      : { configured: false, reason: config.reason, redirectUrl },
    { status: config.configured ? 200 : 503 },
  );
}
