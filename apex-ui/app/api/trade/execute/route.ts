import { apiError, apiOk } from "@/lib/api/response";
import { createClient } from "@/lib/supabase/server";
import { executeTrade } from "@/services/trade/execute";
import { getMarketRegime } from "@/services/decision/stockScoring";
import { getLatestPortfolioSnapshotWithMetrics } from "@/services/portfolio/repository";
import { computePortfolioMetrics } from "@/services/brokers/zerodha";
import { normalizeSymbol } from "@/lib/stockPool";

type ExecuteTradeRequest = {
  stock?: string;
  amount?: number;
};

export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  let body: ExecuteTradeRequest;

  try {
    body = (await request.json()) as ExecuteTradeRequest;
  } catch {
    return apiError("Invalid JSON body", 400);
  }

  const stock = body.stock ? normalizeSymbol(body.stock) : "";
  const amount = Math.round(Number(body.amount ?? 0));

  if (!stock) {
    return apiError("stock is required", 400);
  }

  if (!Number.isFinite(amount) || amount <= 0) {
    return apiError("amount must be a positive number", 400);
  }

  const snapshot = await getLatestPortfolioSnapshotWithMetrics(
    supabase,
    user.id,
  );
  const portfolioValue = snapshot
    ? snapshot.total_value ||
      computePortfolioMetrics(snapshot.portfolio).totalValue
    : 0;
  const marketTrend = await getMarketRegime();

  const result = await executeTrade(supabase, user.id, {
    stock,
    amount,
    portfolioValue,
    marketTrend,
  });

  if (result.status === "NOT_CONNECTED") {
    return apiError("Zerodha is not connected", 409);
  }

  if (result.status === "TOKEN_EXPIRED") {
    return apiError("Zerodha session expired — reconnect to trade", 401);
  }

  if (result.status === "INSUFFICIENT_FUNDS") {
    return apiError(
      `Insufficient funds. Available: ${result.availableCash}, requested: ${result.requested}`,
      400,
    );
  }

  if (result.status === "RISK_BLOCKED") {
    return apiError(result.reason, 403);
  }

  if (result.status === "ENTRY_BLOCKED") {
    return apiError(result.reason, 409);
  }

  if (result.status === "ERROR") {
    return apiError(result.message, 400);
  }

  return apiOk({
    stock: result.stock,
    amount: result.amount,
    price: result.price,
    quantity: result.quantity,
    orderId: result.orderId,
  });
}
