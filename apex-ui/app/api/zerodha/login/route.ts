import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";
import { NextResponse } from "next/server";

export async function GET() {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return NextResponse.json(
      { configured: false, reason: config.reason },
      { status: 503 },
    );
  }

  const loginUrl = `https://kite.zerodha.com/connect/login?api_key=${config.apiKey}&v=3`;

  return NextResponse.redirect(loginUrl);
}
