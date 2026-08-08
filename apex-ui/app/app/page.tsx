import { redirect } from "next/navigation";
import HomeClient from "@/components/HomeClient";
import { samplePortfolio } from "@/data/samplePortfolio";
import { hasActiveBrokerConnection } from "@/services/broker/connections";
import { getLatestPortfolioSnapshot } from "@/services/portfolio/repository";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { getFinancialProfileFromDb } from "@/services/portfolio/repository";

export default async function AppHome({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const requestToken = params.request_token;

  if (typeof requestToken === "string" && requestToken.trim()) {
    const qs = new URLSearchParams();
    qs.set("request_token", requestToken.trim());
    const status = params.status;
    if (typeof status === "string") {
      qs.set("status", status);
    }
    redirect(`/api/zerodha/callback?${qs.toString()}`);
  }

  const supabaseConfigured = isSystemConfigured();

  if (!supabaseConfigured) {
    return (
      <HomeClient
        initialPortfolio={samplePortfolio}
        connectionStatus="NOT_CONNECTED"
        userName="there"
        initialFinancialProfile={null}
      />
    );
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app");
  }

  let connectionStatus: ConnectionStatus = "NOT_CONNECTED";
  let initialPortfolio = samplePortfolio;

  const isConnected = await hasActiveBrokerConnection(supabase, user.id);
  if (isConnected) {
    connectionStatus = "CONNECTED";
  }

  const snapshot = await getLatestPortfolioSnapshot(supabase, user.id);
  if (snapshot && snapshot.holdings.length > 0) {
    initialPortfolio = snapshot;
  }

  const initialFinancialProfile = await getFinancialProfileFromDb(
    supabase,
    user.id,
  );

  const userName =
    (user.user_metadata?.full_name as string | undefined)?.split(" ")[0] ??
    user.email?.split("@")[0] ??
    "there";

  const zerodhaNotice =
    typeof params.zerodha === "string" ? params.zerodha : undefined;
  const zerodhaError =
    typeof params.zerodha_error === "string" ? params.zerodha_error : undefined;

  if (zerodhaNotice === "connected") {
    connectionStatus = "CONNECTED";
  }

  return (
    <HomeClient
      initialPortfolio={initialPortfolio}
      connectionStatus={connectionStatus}
      userName={userName}
      initialFinancialProfile={initialFinancialProfile}
      zerodhaNotice={zerodhaNotice}
      zerodhaError={zerodhaError}
    />
  );
}
