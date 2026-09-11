import { apiError, apiOk } from "@/lib/api/response";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import { getActiveBrokerConnection } from "@/services/broker/connections";
import { fetchZerodhaGtts, placeZerodhaGtt } from "@/services/brokers/zerodha";
import { readServerContract, writeServerContract } from "@/services/desk/contractStore";
import { tradingDateKey } from "@/lib/dailyLoop/disciplineDates";
import { normalizeGttStatus } from "@/lib/dailyLoop/deskNight";
import { getTodayDailyDecision } from "@/services/decision/repository";
import { validateExecutionAgainstArtifact } from "@/services/execution/authorization";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const connection = await getActiveBrokerConnection(supabase, user.id);
  if (!connection?.accessToken || connection.status !== "active") {
    return apiError("Zerodha is not connected", 409);
  }

  const result = await fetchZerodhaGtts(connection.accessToken);
  if (result.status !== "OK") {
    return apiError(result.status === "TOKEN_EXPIRED" ? "Token expired" : result.message, 502);
  }

  const desk = createAdminClient();
  const contract = await readServerContract(desk, user.id, tradingDateKey());
  const watch = contract?.watchSymbol?.trim().toUpperCase();
  const match = watch
    ? result.data.find((row) => row.tradingsymbol?.trim().toUpperCase() === watch)
    : contract?.gttId
      ? result.data.find((row) => String(row.id) === String(contract.gttId))
      : null;
  const watchStatus =
    normalizeGttStatus(match?.status) ??
    (contract?.gttId && !match ? "expired" : normalizeGttStatus(contract?.gttStatus));

  if (contract && watchStatus && watchStatus !== contract.gttStatus) {
    await writeServerContract(desk, user.id, {
      ...contract,
      gttStatus: watchStatus,
      gttId: match ? String(match.id) : contract.gttId,
    });
  }

  return apiOk({
    triggers: result.data,
    watchStatus,
    watchTriggerId: match ? String(match.id) : contract?.gttId ?? null,
  });
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: {
    tradingsymbol?: string;
    triggerPrice?: number;
    lastPrice?: number;
    quantity?: number;
    ticketInr?: number;
    killPrice?: number;
    bookCuts?: Array<{
      tradingsymbol?: string;
      triggerPrice?: number;
      lastPrice?: number;
      quantity?: number;
    }>;
  };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  const symbol = body.tradingsymbol?.trim().toUpperCase();
  const trigger = body.triggerPrice;
  const last = body.lastPrice;
  if (!symbol || !trigger || !last || trigger <= 0 || last <= 0) {
    return apiError("tradingsymbol, triggerPrice, and lastPrice are required", 400);
  }

  const quantity =
    body.quantity && body.quantity >= 1
      ? Math.floor(body.quantity)
      : body.ticketInr && body.ticketInr > 0
        ? Math.max(1, Math.floor(body.ticketInr / trigger))
        : 0;

  if (quantity < 1) {
    return apiError("quantity or ticketInr is required", 400);
  }

  // Wave 1: GTT tickets must reference today's authorised symbol.
  const artifact = await getTodayDailyDecision(supabase, user.id);
  const artifactAmount =
    artifact?.approved_size.kind === "buy_amount"
      ? artifact.approved_size.amount_inr
      : null;
  const authorization = validateExecutionAgainstArtifact(artifact, {
    side: "buy",
    symbol,
    amount: artifactAmount,
  });

  if (!authorization.ok) {
    return apiError(authorization.reason, 409);
  }

  const connection = await getActiveBrokerConnection(supabase, user.id);
  if (!connection?.accessToken || connection.status !== "active") {
    return apiError("Zerodha is not connected", 409);
  }

  const placed = await placeZerodhaGtt(connection.accessToken, {
    tradingsymbol: symbol,
    transaction_type: "BUY",
    quantity,
    triggerPrice: trigger,
    lastPrice: last,
  });

  if (placed.status !== "OK") {
    return apiError(
      placed.status === "TOKEN_EXPIRED" ? "Token expired" : placed.message,
      502,
    );
  }

  let killGttId: string | undefined;
  if (body.killPrice && body.killPrice > 0 && body.killPrice < last) {
    const kill = await placeZerodhaGtt(connection.accessToken, {
      tradingsymbol: symbol,
      transaction_type: "SELL",
      quantity,
      triggerPrice: body.killPrice,
      lastPrice: last,
    });
    if (kill.status === "OK") {
      killGttId = kill.triggerId;
    }
  }

  const bookGttIds: string[] = [];
  for (const cut of body.bookCuts ?? []) {
    const cutSymbol = cut.tradingsymbol?.trim().toUpperCase();
    const cutPrice = cut.triggerPrice;
    const cutLast = cut.lastPrice;
    const cutQty = cut.quantity;
    if (!cutSymbol || !cutPrice || !cutLast || !cutQty || cutPrice <= 0 || cutQty < 1) {
      continue;
    }

    const sell = await placeZerodhaGtt(connection.accessToken, {
      tradingsymbol: cutSymbol,
      transaction_type: "SELL",
      quantity: Math.floor(cutQty),
      triggerPrice: cutPrice,
      lastPrice: cutLast,
    });
    if (sell.status === "OK") {
      bookGttIds.push(sell.triggerId);
    }
  }

  const dateKey = tradingDateKey();
  const contract = await readServerContract(createAdminClient(), user.id, dateKey);
  if (contract) {
    await writeServerContract(createAdminClient(), user.id, {
      ...contract,
      gttId: placed.triggerId,
      gttStatus: normalizeGttStatus("active") ?? "active",
      killGttId: killGttId ?? contract.killGttId,
      bookGttIds: bookGttIds.length > 0 ? bookGttIds : contract.bookGttIds,
    });
  }

  return apiOk({
    triggerId: placed.triggerId,
    killGttId: killGttId ?? null,
    bookGttIds,
    status: "active",
  });
}
