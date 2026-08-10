import type { AxiosRequestConfig } from "axios";
import { HttpsProxyAgent } from "https-proxy-agent";

const PLACEHOLDER_VALUES = new Set(["", "changeme", "replace_me", "your_vm_ip"]);

export type KiteOrderProxyStatus =
  | { configured: true; url: string }
  | { configured: false; reason: string };

export function getKiteOrderProxyStatus(): KiteOrderProxyStatus {
  const raw = process.env.KITE_ORDER_PROXY_URL?.trim();

  if (!raw) {
    return {
      configured: false,
      reason:
        "KITE_ORDER_PROXY_URL is not set — order placement requires a static IP proxy",
    };
  }

  try {
    const parsed = new URL(raw);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return {
        configured: false,
        reason: "KITE_ORDER_PROXY_URL must use http:// or https://",
      };
    }

    if (
      PLACEHOLDER_VALUES.has(parsed.hostname) ||
      PLACEHOLDER_VALUES.has(parsed.password ?? "")
    ) {
      return {
        configured: false,
        reason: "Replace placeholder values in KITE_ORDER_PROXY_URL",
      };
    }

    return { configured: true, url: raw };
  } catch {
    return { configured: false, reason: "KITE_ORDER_PROXY_URL is not a valid URL" };
  }
}

/** Axios config for Kite API calls — routes through the whitelisted VM when set. */
export function buildKiteAxiosConfig(): Pick<
  AxiosRequestConfig,
  "httpsAgent" | "proxy"
> {
  const status = getKiteOrderProxyStatus();
  if (!status.configured) {
    return {};
  }

  return {
    httpsAgent: new HttpsProxyAgent(status.url),
    proxy: false,
  };
}

/** @deprecated Use buildKiteAxiosConfig */
export function buildKiteOrderProxyAxiosConfig(): Pick<
  AxiosRequestConfig,
  "httpsAgent" | "proxy"
> {
  return buildKiteAxiosConfig();
}

export function isStaticIpRequiredMessage(message: string): boolean {
  return /static ip|ip whitelist|no ips configured/i.test(message);
}

export function formatStaticIpOrderError(message: string): string {
  if (!isStaticIpRequiredMessage(message)) {
    return message;
  }

  return `${message} Configure KITE_ORDER_PROXY_URL to your Oracle VM proxy and whitelist that IP in the Kite developer console.`;
}

export async function fetchEgressIpv4(
  proxyUrl?: string,
): Promise<{ ip: string | null; via: "direct" | "proxy"; error?: string }> {
  const target = "https://api.ipify.org?format=json";

  try {
    const axios = (await import("axios")).default;

    if (proxyUrl) {
      const agent = new HttpsProxyAgent(proxyUrl);
      const proxied = await axios.get<{ ip?: string }>(target, {
        httpsAgent: agent,
        proxy: false,
        timeout: 10_000,
      });
      return { ip: proxied.data.ip ?? null, via: "proxy" };
    }

    const direct = await axios.get<{ ip?: string }>(target, { timeout: 10_000 });
    return { ip: direct.data.ip ?? null, via: "direct" };
  } catch (error) {
    return {
      ip: null,
      via: proxyUrl ? "proxy" : "direct",
      error: error instanceof Error ? error.message : "egress lookup failed",
    };
  }
}

export function runKiteOrderProxySelfCheck(): void {
  const assert = (condition: boolean, message: string) => {
    if (!condition) {
      throw new Error(`Kite order proxy self-check failed: ${message}`);
    }
  };

  const unset = getKiteOrderProxyStatus();
  assert(!unset.configured, "Unset proxy must report not configured");

  process.env.KITE_ORDER_PROXY_URL = "http://apex:secret@203.0.113.10:3128";
  const configured = getKiteOrderProxyStatus();
  assert(configured.configured, "Valid proxy URL must be accepted");

  const axiosConfig = buildKiteOrderProxyAxiosConfig();
  assert(Boolean(axiosConfig.httpsAgent), "Proxy agent must be created");
  assert(axiosConfig.proxy === false, "Axios native proxy must be disabled");

  assert(
    isStaticIpRequiredMessage("No IPs configured for this app"),
    "Must detect Zerodha static IP errors",
  );
  assert(
    formatStaticIpOrderError("No IPs configured").includes(
      "KITE_ORDER_PROXY_URL",
    ),
    "Must append proxy setup hint",
  );

  delete process.env.KITE_ORDER_PROXY_URL;
}
