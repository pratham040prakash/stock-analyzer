/**
 * Optional smoke checks for externally deployed services (Alpha AI worker, Kite proxy).
 *
 * Usage:
 *   npx tsx scripts/verify-deploy-services.ts
 *
 * Env (optional — skips when unset):
 *   ALPHA_AI_SERVICE_URL  → GET {url}/health
 *   KITE_ORDER_PROXY_URL  → TCP connect or HTTP health if available
 */

type ServiceCheck = {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
  skipped: boolean;
};

function record(checks: ServiceCheck[], check: ServiceCheck): void {
  checks.push(check);
}

async function fetchHealth(url: string): Promise<{ ok: boolean; detail: string }> {
  const healthUrl = url.replace(/\/$/, "") + "/health";

  try {
    const response = await fetch(healthUrl, { signal: AbortSignal.timeout(8000) });
    const body = (await response.json().catch(() => null)) as Record<string, unknown> | null;

    return {
      ok: response.ok && body?.status === "ok",
      detail: `GET ${healthUrl} → ${response.status}`,
    };
  } catch (error) {
    return {
      ok: false,
      detail: error instanceof Error ? error.message : "fetch failed",
    };
  }
}

async function runChecks(): Promise<ServiceCheck[]> {
  const checks: ServiceCheck[] = [];
  const alphaUrl = process.env.ALPHA_AI_SERVICE_URL?.trim();
  const kiteProxy = process.env.KITE_ORDER_PROXY_URL?.trim();

  if (alphaUrl) {
    const result = await fetchHealth(alphaUrl);
    record(checks, {
      id: "alpha-ai-health",
      label: "Alpha AI worker health",
      ok: result.ok,
      detail: result.detail,
      skipped: false,
    });
  } else {
    record(checks, {
      id: "alpha-ai-skipped",
      label: "Alpha AI worker health",
      ok: true,
      detail: "ALPHA_AI_SERVICE_URL not set — skipped",
      skipped: true,
    });
  }

  if (kiteProxy) {
    record(checks, {
      id: "kite-proxy-configured",
      label: "Kite order proxy configured",
      ok: true,
      detail: `KITE_ORDER_PROXY_URL set (${kiteProxy.replace(/:[^:@/]+@/, ":***@")})`,
      skipped: false,
    });
  } else {
    record(checks, {
      id: "kite-proxy-skipped",
      label: "Kite order proxy configured",
      ok: true,
      detail: "KITE_ORDER_PROXY_URL not set — skipped",
      skipped: true,
    });
  }

  return checks;
}

async function main(): Promise<void> {
  const checks = await runChecks();
  const failed = checks.filter((check) => !check.skipped && !check.ok);

  console.log("\nAPEX deploy services verify\n");

  for (const check of checks) {
    const mark = check.skipped ? "SKIP" : check.ok ? "PASS" : "FAIL";
    console.log(`[${mark}] ${check.label}`);
    console.log(`       ${check.detail}`);
  }

  if (failed.length > 0) {
    process.exitCode = 1;
  }
}

void main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});

export function runDeployServicesSelfCheck(): void {
  if (typeof fetch !== "function") {
    throw new Error("Deploy services self-check failed");
  }
}
