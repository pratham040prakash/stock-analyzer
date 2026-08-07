import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { KITE_ACCESS_TOKEN_COOKIE } from "@/lib/broker/zerodhaSession";
import {
  getActiveBrokerConnection,
  markBrokerConnectionExpired,
} from "@/services/broker/connections";
import { fetchZerodhaMargins } from "@/services/brokers/zerodha";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ available_cash: 0, status: "NOT_CONNECTED" }, {
      status: 401,
    });
  }

  const connection = await getActiveBrokerConnection(supabase, user.id);

  if (!connection || connection.status !== "active") {
    return NextResponse.json({ available_cash: 0, status: "NOT_CONNECTED" });
  }

  const marginsResult = await fetchZerodhaMargins(connection.accessToken);

  if (marginsResult.status === "TOKEN_EXPIRED") {
    await markBrokerConnectionExpired(supabase, user.id);
    const cookieStore = await cookies();
    cookieStore.delete(KITE_ACCESS_TOKEN_COOKIE);
    return NextResponse.json({ available_cash: 0, status: "TOKEN_EXPIRED" });
  }

  if (marginsResult.status === "ERROR") {
    return NextResponse.json(
      { available_cash: 0, status: "ERROR", message: marginsResult.message },
      { status: 502 },
    );
  }

  return NextResponse.json({
    available_cash: marginsResult.availableCash,
    status: "OK",
  });
}
