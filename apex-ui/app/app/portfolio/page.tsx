import { redirect } from "next/navigation";
import PortfolioPageClient from "@/components/PortfolioPageClient";
import ConnectZerodhaCard from "@/components/ConnectZerodhaCard";
import { ApexShell } from "@/components/ui/apex";
import ApexSurfaceNav from "@/components/nav/ApexSurfaceNav";
import { hasActiveBrokerConnection } from "@/services/broker/connections";
import { isSystemConfigured } from "@/lib/env/config";
import { createClient } from "@/lib/supabase/server";
import type { ConnectionStatus } from "@/lib/broker/zerodha";

export default async function PortfolioPage() {
  if (!isSystemConfigured()) {
    redirect("/login?next=/app/portfolio");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/app/portfolio");
  }

  let connectionStatus: ConnectionStatus = "NOT_CONNECTED";
  const isConnected = await hasActiveBrokerConnection(supabase, user.id);

  if (isConnected) {
    connectionStatus = "CONNECTED";
  }

  const userName =
    (user.user_metadata?.full_name as string | undefined)?.split(" ")[0] ??
    user.email?.split("@")[0] ??
    "there";

  if (connectionStatus === "NOT_CONNECTED") {
    return (
      <ApexShell>
        <header className="mb-6">
          <ApexSurfaceNav />
        </header>
        <ConnectZerodhaCard />
      </ApexShell>
    );
  }

  return (
    <PortfolioPageClient
      connectionStatus={connectionStatus}
      userName={userName}
    />
  );
}
