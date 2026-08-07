export type { KiteHolding } from "@/services/brokers/zerodha";
export {
  fetchZerodhaHoldings,
  mapKiteHoldingsToPortfolio,
} from "@/services/brokers/zerodha";

export type ConnectionStatus = "NOT_CONNECTED" | "TOKEN_EXPIRED" | "CONNECTED";

export type HoldingsResult =
  | { status: "NOT_CONNECTED" }
  | { status: "TOKEN_EXPIRED" }
  | { status: "OK"; data: import("@/services/brokers/zerodha").KiteHolding[] };

/** @deprecated Use services/brokers/zerodha.fetchZerodhaHoldings with DB token */
export async function getHoldings(): Promise<HoldingsResult> {
  const { cookies } = await import("next/headers");
  const { fetchZerodhaHoldings } = await import("@/services/brokers/zerodha");
  const { getZerodhaConfig } = await import("@/lib/broker/zerodhaConfig");

  const cookieStore = await cookies();
  const token = cookieStore.get("kite_access_token")?.value;

  if (!token || !getZerodhaConfig().configured) {
    return { status: "NOT_CONNECTED" };
  }

  const result = await fetchZerodhaHoldings(token);

  if (result.status === "OK") {
    return { status: "OK", data: result.data };
  }

  if (result.status === "TOKEN_EXPIRED") {
    return { status: "TOKEN_EXPIRED" };
  }

  return { status: "TOKEN_EXPIRED" };
}
