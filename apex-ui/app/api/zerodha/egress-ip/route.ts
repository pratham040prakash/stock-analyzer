import { apiError, apiOk } from "@/lib/api/response";
import {
  fetchEgressIpv4,
  getKiteOrderProxyStatus,
} from "@/lib/broker/kiteOrderProxy";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

/** Compare Vercel direct egress vs proxied egress for Kite IP whitelisting. */
export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return apiError("Unauthorized", 401);
  }

  const proxyStatus = getKiteOrderProxyStatus();
  const direct = await fetchEgressIpv4();
  const proxied =
    proxyStatus.configured
      ? await fetchEgressIpv4(proxyStatus.url)
      : { ip: null, via: "proxy" as const, error: "KITE_ORDER_PROXY_URL not set" };

  return apiOk({
    direct_egress_ipv4: direct.ip,
    direct_error: direct.error,
    proxy_configured: proxyStatus.configured,
    proxy_reason: proxyStatus.configured ? undefined : proxyStatus.reason,
    proxied_egress_ipv4: proxied.ip,
    proxied_error: proxied.error,
    whitelist_hint:
      "Add proxied_egress_ipv4 to developers.kite.trade → Profile → IP Whitelist",
  });
}
