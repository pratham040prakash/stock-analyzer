import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { KITE_ACCESS_TOKEN_COOKIE } from "@/lib/broker/zerodhaSession";
import { computeTotalCapital } from "@/lib/broker/zerodhaFunds";
import { fetchZerodhaFundsForUser } from "@/services/broker/funds";
import { markBrokerConnectionExpired } from "@/services/broker/connections";
import {
  computePortfolioMetrics,
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

function portfolioValueFromHoldings(
  holdings: { data: { tradingsymbol: string; quantity: number; average_price: number; last_price: number; close_price?: number }[] } | null,
): number {
  if (!holdings) {
    return 0;
  }

  const portfolio = mapKiteHoldingsToPortfolio(holdings.data);
  return computePortfolioMetrics(portfolio).totalValue;
}

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return emptyFunds("NOT_CONNECTED", { statusCode: 401 });
  }

  const result = await fetchZerodhaFundsForUser(supabase, user.id);

  if (result.status === "NOT_CONNECTED") {
    return emptyFunds("NOT_CONNECTED", { message: result.message });
  }

  if (result.status === "TOKEN_EXPIRED") {
    await markBrokerConnectionExpired(supabase, user.id);
    const cookieStore = await cookies();
    cookieStore.delete(KITE_ACCESS_TOKEN_COOKIE);

    const portfolioValue = result.holdings
      ? portfolioValueFromHoldings(result.holdings)
      : 0;

    return NextResponse.json({
      ledger_cash: 0,
      collateral: 0,
      margin_available: 0,
      live_balance: 0,
      portfolio_value: portfolioValue,
      total_capital: computeTotalCapital(portfolioValue, 0),
      available_cash: 0,
      status: "TOKEN_EXPIRED",
      message: result.message,
    });
  }

  if (result.status === "ERROR") {
    const portfolioValue = result.holdings
      ? portfolioValueFromHoldings(result.holdings)
      : 0;

    return NextResponse.json({
      ledger_cash: 0,
      collateral: 0,
      margin_available: 0,
      live_balance: 0,
      portfolio_value: portfolioValue,
      total_capital: computeTotalCapital(portfolioValue, 0),
      available_cash: 0,
      status: portfolioValue > 0 ? "PARTIAL" : "ERROR",
      message: result.message,
    });
  }

  const { margins, holdings } = result;
  const portfolioValue = portfolioValueFromHoldings(holdings);
  const totalCapital = computeTotalCapital(portfolioValue, margins.ledgerCash);

  return NextResponse.json({
    ledger_cash: margins.ledgerCash,
    collateral: margins.collateral,
    margin_available: margins.marginAvailable,
    live_balance: margins.liveBalance,
    portfolio_value: portfolioValue,
    total_capital: totalCapital,
    available_cash: margins.marginAvailable,
    status: "OK",
  });
}
