import { apiError, apiOk } from "@/lib/api/response";
import { normalizeSymbol } from "@/lib/stockPool";
import { getApexBrokerFillToday } from "@/services/trade/logTradeFill";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const { searchParams } = new URL(request.url);
  const stock = normalizeSymbol(searchParams.get("stock") ?? "");

  if (!stock) {
    return apiError("stock is required", 400);
  }

  const fill = await getApexBrokerFillToday(supabase, user.id, stock);

  return apiOk({
    stock,
    filledToday: fill.filled,
    orderId: fill.orderId,
    quantity: fill.quantity,
    side: fill.side,
    price: fill.price,
  });
}
