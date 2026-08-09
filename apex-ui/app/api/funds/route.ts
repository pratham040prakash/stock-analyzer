import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { KITE_ACCESS_TOKEN_COOKIE } from "@/lib/broker/zerodhaSession";
import { computeTotalCapital } from "@/lib/broker/zerodhaFunds";
import {
  getActiveBrokerConnection,
  markBrokerConnectionExpired,
} from "@/services/broker/connections";
import {
  computePortfolioMetrics,
  fetchZerodhaHoldings,
  fetchZerodhaMargins,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";
import { createClient } from "@/lib/supabase/server";

function emptyFunds(status: string, extra?: Record<string, unknown>) {
  return NextResponse.json({
    ledger_cash: 0,
    collateral: 0,
    margin_available: 0,
    live_balance: 0,
    portfolio_value: 0,
    total_capital: 0,
    available_cash: 0,
    status,
    ...extra,
  });
}

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return emptyFunds("NOT_CONNECTED", { statusCode: 401 });
  }

  const connection = await getActiveBrokerConnection(supabase, user.id);

  if (!connection || connection.status !== "active") {
    return emptyFunds("NOT_CONNECTED");
  }

  const [marginsResult, holdingsResult] = await Promise.all([
    fetchZerodhaMargins(connection.accessToken),
    fetchZerodhaHoldings(connection.accessToken),
  ]);

  if (marginsResult.status === "TOKEN_EXPIRED") {
    await markBrokerConnectionExpired(supabase, user.id);
    const cookieStore = await cookies();
    cookieStore.delete(KITE_ACCESS_TOKEN_COOKIE);
    return emptyFunds("TOKEN_EXPIRED");
  }

  if (marginsResult.status === "ERROR") {
    return NextResponse.json(
      {
        ledger_cash: 0,
        collateral: 0,
        margin_available: 0,
        live_balance: 0,
        portfolio_value: 0,
        total_capital: 0,
        available_cash: 0,
        status: "ERROR",
        message: marginsResult.message,
      },
      { status: 502 },
    );
  }

  let portfolioValue = 0;

  if (holdingsResult.status === "OK") {
    const portfolio = mapKiteHoldingsToPortfolio(holdingsResult.data);
    portfolioValue = computePortfolioMetrics(portfolio).totalValue;
  }

  const totalCapital = computeTotalCapital(
    portfolioValue,
    marginsResult.ledgerCash,
  );

  return NextResponse.json({
    ledger_cash: marginsResult.ledgerCash,
    collateral: marginsResult.collateral,
    margin_available: marginsResult.marginAvailable,
    live_balance: marginsResult.liveBalance,
    portfolio_value: portfolioValue,
    total_capital: totalCapital,
    /** Deployable CNC balance — matches Zerodha margin available. */
    available_cash: marginsResult.marginAvailable,
    status: "OK",
  });
}
