import { redirect } from "next/navigation";
import HomeClient from "@/components/HomeClient";
import { samplePortfolio } from "@/data/samplePortfolio";
import { hasActiveBrokerConnection } from "@/services/broker/connections";
import { getLatestPortfolioSnapshot } from "@/services/portfolio/repository";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";
import type { ConnectionStatus } from "@/lib/broker/zerodha";
import { getFinancialProfileFromDb } from "@/services/portfolio/repository";

export default async function Home() {
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
    redirect("/login");
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

  return (
    <HomeClient
      initialPortfolio={initialPortfolio}
      connectionStatus={connectionStatus}
      userName={userName}
      initialFinancialProfile={initialFinancialProfile}
    />
  );
}
