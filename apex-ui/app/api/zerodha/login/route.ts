import { NextResponse } from "next/server";
import { getZerodhaConfig } from "@/lib/broker/zerodhaConfig";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const config = getZerodhaConfig();

  if (!config.configured) {
    return NextResponse.json(
      { configured: false, reason: config.reason },
      { status: 503 },
    );
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", "/api/zerodha/login");
    return NextResponse.redirect(loginUrl);
  }

  const loginUrl = `https://kite.zerodha.com/connect/login?api_key=${config.apiKey}&v=3`;

  return NextResponse.redirect(loginUrl);
}
